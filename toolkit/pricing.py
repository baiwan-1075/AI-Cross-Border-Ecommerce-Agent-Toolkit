"""Read saved settings and reuse the bound pricing engine, without DB writes."""
from contextlib import closing
from dataclasses import fields
from datetime import date
from decimal import Decimal
import json
from pathlib import Path
import sqlite3
import sys

from .context import now, sha256


def read_saved_settings(database):
    path = Path(database).resolve()
    if not path.is_file():
        raise ValueError('Formal pricing database missing; no database will be created')
    with closing(sqlite3.connect(path.as_uri() + '?mode=ro', uri=True, timeout=2)) as connection:
        row = connection.execute('SELECT value_json,updated_at FROM app_settings WHERE key=?',
                                 ('simple_pricing_draft',)).fetchone()
    if not row:
        raise ValueError('Saved pricing configuration missing; no fee defaults will be invented')
    draft = json.loads(row[0])
    required = ('settings', 'fee_selection', 'forwarder_cost_cny', 'target_mode', 'target_margin_rate', 'target_profit_cny')
    if any(key not in draft for key in required):
        raise ValueError('Saved pricing configuration is incomplete')
    return {key: draft[key] for key in required}, row[1]


def review_pricing(binding, database, product_cost=None, weight=None, pricing_date=None):
    if (product_cost is None) != (weight is None):
        raise ValueError('Provide both this product cost and packaged chargeable weight, or neither')
    root = Path(binding['pricing_root']).resolve()
    kernel_files = ['domain/simple_pricing.py', 'domain/calibrated_pricing.py',
                    'domain/fee_scenarios.py', 'domain/my_standard_shipping.py']
    if any(not (root / path).is_file() for path in kernel_files):
        raise ValueError('The bound current pricing engine is incomplete')
    saved, updated = read_saved_settings(database)
    report = {'status': 'SAVED_CONFIGURATION_ONLY', 'captured_at': now(), 'saved_at': updated,
              'source': 'Local saved settings, not live account fee verification',
              'engine_files': {path: sha256(root / path) for path in kernel_files},
              'saved_configuration': saved,
              'limits': ['Current account eligibility, fee bases, caps and subsidies still require evidence.',
                         'No product cost/weight is inherited from an old draft.',
                         'Listing price, promotion price and paid merchandise income are different amounts.',
                         'No database, fee parameter, shop price or promotion was changed.']}
    if product_cost is None:
        return report
    if not Decimal(str(product_cost)).is_finite() or not Decimal(str(weight)).is_finite():
        raise ValueError('Cost and weight must be finite')
    if Decimal(str(product_cost)) < 0 or Decimal(str(weight)) <= 0:
        raise ValueError('Cost must be nonnegative and weight positive')
    # This is the existing user's inspected local source, not code from the upstream toolkit.
    # Imports run with bytecode disabled; only the pure domain calculation is called.
    for name, module in tuple(sys.modules.items()):
        if name == 'domain' or name.startswith('domain.'):
            origin = getattr(module, '__file__', None)
            if not origin or not Path(origin).resolve().is_relative_to(root):
                raise ValueError('An unrelated domain module is already loaded; use a fresh CLI process')
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(root))
    try:
        from domain.simple_pricing import SimplePricingInput, SimplePricingSettings, TargetMode, calculate_simple_pricing
        from domain.fee_scenarios import FeeSelection
        raw = saved['settings']
        prototype = SimplePricingSettings.defaults()
        converted = {}
        for field in fields(SimplePricingSettings):
            if field.name not in raw:
                raise ValueError(f'Saved field is missing; refusing default substitution: {field.name}')
            value, example = raw[field.name], getattr(prototype, field.name)
            if isinstance(example, Decimal):
                value = Decimal(str(value))
            elif isinstance(example, bool):
                if not isinstance(value, bool):
                    raise ValueError('Saved boolean fee switches are invalid')
            elif isinstance(example, date):
                value = date.fromisoformat(value)
            elif field.name == 'bxp_commission_rate' and value is not None:
                value = Decimal(str(value))
            converted[field.name] = value
        settings = SimplePricingSettings(**converted)
        if not settings.calibration:
            raise ValueError('A current calibrated fee model is required')
        switches = saved['fee_selection']
        fee_keys = ('include_bxp', 'include_bxp_plus', 'include_affiliate', 'include_ads',
                    'include_withdrawal', 'include_lvg', 'include_tail_sst')
        if any(key not in switches or not isinstance(switches[key], bool) for key in fee_keys):
            raise ValueError('Saved fee switches are incomplete or invalid')
        fees = FeeSelection(**{key: switches[key] for key in fee_keys})
        inp = SimplePricingInput(product_cost_cny=Decimal(str(product_cost)),
                                 forwarder_cost_cny=Decimal(str(saved['forwarder_cost_cny'])),
                                 actual_weight_g=Decimal(str(weight)),
                                 target_mode=TargetMode(saved['target_mode']),
                                 target_margin_rate=Decimal(str(saved['target_margin_rate'])),
                                 target_profit_cny=Decimal(str(saved['target_profit_cny'])),
                                 pricing_date=date.fromisoformat(pricing_date or now()[:10]))
        result = calculate_simple_pricing(inp, settings, fees)
        names = ['break_even_paid_myr', 'target_paid_myr', 'break_even_list_myr', 'target_list_myr',
                 'target_activity_myr', 'target_profit_myr', 'target_margin_rate', 'seller_shipping_myr', 'tail_sst_myr']
        report.update(status='CONDITIONAL_CALCULATED', input={'cost_cny': str(product_cost), 'weight_g': str(weight),
                      'pricing_date': inp.pricing_date.isoformat()},
                      result={key: str(getattr(result, key)) for key in names},
                      fee_breakdown={key: str(value) for key, value in result.target_fee_breakdown.items()},
                      warnings=list(result.configuration_warnings))
        return report
    finally:
        sys.path.remove(str(root))
