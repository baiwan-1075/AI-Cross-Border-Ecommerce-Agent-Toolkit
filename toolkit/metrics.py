"""Natural-traffic arithmetic without invented benchmarks or causal claims."""
from datetime import date, datetime
import math


def diagnose(data):
    required = ['market', 'timezone', 'channel', 'source', 'captured_at', 'period_start', 'period_end',
                'scope', 'metric_scope', 'view_definition']
    missing = [key for key in required if not data.get(key)]
    if missing:
        raise ValueError('Metric metadata missing: ' + ', '.join(missing))
    if data['market'] != 'MY' or data['metric_scope'] != 'same_window_same_product_attribution':
        raise ValueError('MY and one explicit consistent product/window/attribution scope are required')
    if data['channel'] not in ('self_made_short_video', 'product_card'):
        raise ValueError('This adapter covers natural video and product-card traffic only')
    if not isinstance(data['scope'], dict) or not data['scope'].get('product_key'):
        raise ValueError('Metric product identity is missing')
    start, end = date.fromisoformat(data['period_start']), date.fromisoformat(data['period_end'])
    captured = datetime.fromisoformat(data['captured_at'])
    if not captured.tzinfo or start > end or end > captured.date():
        raise ValueError('Metric period or capture timezone is invalid')
    fields = ('views', 'product_impressions', 'product_clicks', 'orders')
    counts = {}
    for field in fields:
        value = data.get(field)
        if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float))
                                  or not math.isfinite(value) or value < 0 or value != int(value)):
            raise ValueError(f'{field} must be a nonnegative whole count or null')
        counts[field] = value

    def ratio(numerator, denominator):
        a, b = counts[numerator], counts[denominator]
        return None if a is None or b in (None, 0) else a / b

    missing_metrics = [key for key, value in counts.items() if value is None]
    limits = ['Low views do not establish tagging suppression or product failure.',
              'No universal CTR/conversion benchmark or commercial verdict is applied.',
              'Period views are not lifetime views; compare equal publication age.',
              'Source attribution definitions must be checked against the actual export.']
    if counts['product_clicks'] == 0:
        limits.append('No observed clicks: click-to-order conversion cannot be evaluated.')
    age = None
    if data.get('published_at'):
        published = datetime.fromisoformat(data['published_at'])
        if not published.tzinfo or published > captured:
            raise ValueError('Publication time must have timezone and precede capture')
        age = (captured - published).total_seconds() / 3600
    return {'status': 'PARTIAL' if missing_metrics else 'CALCULATED_WITH_LIMITS',
            'market': data['market'], 'timezone': data['timezone'], 'channel': data['channel'],
            'metric_scope': data['metric_scope'], 'view_definition': data['view_definition'],
            'source': data['source'], 'scope': data['scope'], 'period_start': data['period_start'],
            'period_end': data['period_end'], 'captured_at': data['captured_at'],
            'counts': counts, 'missing_metrics': missing_metrics,
            'product_ctr': ratio('product_clicks', 'product_impressions'),
            'click_to_order_rate': ratio('orders', 'product_clicks'),
            'formulas': {'product_ctr': 'product_clicks / product_impressions',
                         'click_to_order_rate': 'orders / product_clicks'},
            'publication_age_hours': age, 'causal_conclusion': 'NOT_VERIFIED', 'limits': limits}
