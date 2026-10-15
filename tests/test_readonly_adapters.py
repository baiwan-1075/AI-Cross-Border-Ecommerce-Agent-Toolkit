import contextlib
import io
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from sovyn import main
from toolkit.context import inventory, read_sheet_rows, sha256
from toolkit.pricing import read_saved_settings


def workbook(path, source_folder, external=False):
    from xml.sax.saxutils import escape
    ns = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
    rel = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
    with zipfile.ZipFile(path, 'w') as archive:
        archive.writestr('xl/workbook.xml', f'<workbook xmlns="{ns}" xmlns:r="{rel}"><sheets><sheet name="商品总表" sheetId="1" r:id="s1"/></sheets></workbook>')
        mode = ' TargetMode="External"' if external else ''
        archive.writestr('xl/_rels/workbook.xml.rels', f'<Relationships><Relationship Id="s1" Target="worksheets/custom.xml"{mode}/></Relationships>')
        archive.writestr('xl/sharedStrings.xml', f'<sst xmlns="{ns}"><si><r><t>WP</t></r><r><t>0099</t></r></si></sst>')
        archive.writestr('xl/worksheets/custom.xml', f'''<worksheet xmlns="{ns}"><sheetData>
<row r="4"><c r="A4" t="inlineStr"><is><t>固定编号</t></is></c><c r="C4" t="inlineStr"><is><t>原始资料目录</t></is></c></row>
<row r="9"><c r="A9" t="s"><v>0</v></c><c r="C9" t="inlineStr"><is><t>{escape(str(source_folder))}</t></is></c><c r="D9"><f>1+1</f><v>2</v></c></row>
</sheetData></worksheet>''')


class WorkbookTests(unittest.TestCase):
    def test_matches_directory_not_display_number_and_preserves_workbook(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = root / '03_demo' / '01_原始参考素材'
            original.mkdir(parents=True)
            (original / 'reference.txt').write_text('source', encoding='utf-8')
            book = root / 'book.xlsx'
            workbook(book, original)
            before = sha256(book)
            result = inventory({'assets_root': str(root), 'workbook': {'path': str(book)}}, '03_demo')
            self.assertEqual(result['identity_status'], 'MATCHED_PATH')
            self.assertEqual(result['workbench_matches'][0]['fields']['固定编号'], 'WP0099')
            self.assertEqual(result['visual_review'], 'NOT_VERIFIED')
            self.assertEqual(sha256(book), before)
            self.assertEqual(read_sheet_rows(book, '商品总表')[1]['cells']['D'], '2')

    def test_external_sheet_relationship_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'book.xlsx'
            workbook(path, directory, external=True)
            with self.assertRaises(ValueError):
                read_sheet_rows(path, '商品总表')


class PricingReadTests(unittest.TestCase):
    def test_reads_only_whitelisted_settings_without_altering_database(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'calculator.db'
            draft = dict(settings={'commission_rate': '0.09'}, fee_selection={}, forwarder_cost_cny='2',
                         target_mode='MARGIN', target_margin_rate='0.1', target_profit_cny='10',
                         product_cost_cny='999', actual_weight_g='9999')
            with contextlib.closing(sqlite3.connect(path)) as connection:
                connection.execute('CREATE TABLE app_settings (key TEXT, value_json TEXT, updated_at TEXT)')
                connection.execute('INSERT INTO app_settings VALUES (?,?,?)', ('simple_pricing_draft', json.dumps(draft), 'test'))
                connection.commit()
            before = sha256(path)
            settings, updated = read_saved_settings(path)
            self.assertEqual(updated, 'test')
            self.assertNotIn('product_cost_cny', settings)
            self.assertNotIn('actual_weight_g', settings)
            self.assertEqual(sha256(path), before)

    def test_missing_database_is_not_created(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'missing.db'
            with self.assertRaises(ValueError):
                read_saved_settings(path)
            self.assertFalse(path.exists())

    def test_invalid_input_is_reported_without_traceback_or_output_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'broken.json'
            path.write_text('{invalid', encoding='utf-8')
            stream = io.StringIO()
            with patch.object(sys, 'argv', ['sovyn.py', 'funnel', '--input', str(path), '--out', '.local/should-not-exist.json']), contextlib.redirect_stderr(stream):
                self.assertEqual(main(), 2)
            self.assertEqual(json.loads(stream.getvalue())['status'], 'ERROR')


if __name__ == '__main__':
    unittest.main()
