import json
from pathlib import Path
import tempfile
import unittest

from toolkit.context import safe_output
from toolkit.metrics import diagnose
from toolkit.workflow import validate_brief


class MetricsTests(unittest.TestCase):
    def base(self):
        return json.loads((Path(__file__).parents[1] / 'examples/synthetic-metrics.json').read_text('utf-8'))

    def test_missing_is_not_zero(self):
        data = self.base()
        data['product_clicks'] = None
        report = diagnose(data)
        self.assertIsNone(report['product_ctr'])
        self.assertIn('product_clicks', report['missing_metrics'])

    def test_report_keeps_metric_definitions_and_channel(self):
        data = self.base()
        report = diagnose(data)
        for key in ['market', 'timezone', 'channel', 'metric_scope', 'view_definition']:
            self.assertEqual(report[key], data[key])

    def test_zero_denominator_is_not_bad_conversion(self):
        report = diagnose(self.base())
        self.assertEqual(report['product_ctr'], 0)
        self.assertIsNone(report['click_to_order_rate'])
        self.assertEqual(report['causal_conclusion'], 'NOT_VERIFIED')

    def test_ctr_uses_product_impressions(self):
        data = self.base()
        data['views'] = 1000
        data['product_clicks'] = 3
        data['orders'] = 1
        report = diagnose(data)
        self.assertAlmostEqual(report['product_ctr'], 0.1)
        self.assertAlmostEqual(report['click_to_order_rate'], 1 / 3)

    def test_product_impressions_may_exceed_views(self):
        data = self.base()
        data['product_impressions'] = 150
        self.assertEqual(diagnose(data)['status'], 'CALCULATED_WITH_LIMITS')

    def test_negative_non_finite_or_boolean_counts_rejected(self):
        for value in [-1, float('nan'), float('inf'), True, 1.2]:
            data = self.base()
            data['views'] = value
            with self.assertRaises(ValueError):
                diagnose(data)

    def test_mixed_scope_and_reversed_period_rejected(self):
        for changes in [dict(metric_scope='different_attribution'), dict(period_end='2026-10-14')]:
            data = self.base()
            data.update(changes)
            with self.assertRaises(ValueError):
                diagnose(data)


class BoundaryTests(unittest.TestCase):
    def test_output_cannot_escape_or_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            target = safe_output(root, '.local/new.json')
            target.parent.mkdir(parents=True)
            target.write_text('existing')
            for path in ['.local/new.json', '.local/../../outside.json', 'README.md']:
                with self.assertRaises(ValueError):
                    safe_output(root, path)

    def test_unknown_dimensions_only_block_dependencies(self):
        brief = json.loads((Path(__file__).parents[1] / 'examples/synthetic-product.json').read_text('utf-8'))
        report = validate_brief(brief)
        self.assertEqual(report['identity'], 'SUPPORTED_FOR_PREPARATION')
        self.assertIn('strategy', report['blocked_dependencies'])
        self.assertNotIn('video', report['blocked_dependencies'])

    def test_unreferenced_fact_and_missing_identity_rejected(self):
        brief = json.loads((Path(__file__).parents[1] / 'examples/synthetic-product.json').read_text('utf-8'))
        brief['facts'][0]['source_ids'] = ['missing']
        with self.assertRaises(ValueError):
            validate_brief(brief)
        brief['facts'][0]['source_ids'] = ['demo']
        brief['product']['identity_status'] = 'NOT_VERIFIED'
        self.assertEqual(validate_brief(brief)['identity'], 'NOT_VERIFIED')


if __name__ == '__main__':
    unittest.main()
