"""Local bindings, source fingerprints and read-only workbook inspection."""
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import posixpath
import re
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / 'profiles/sovyn-my/profile.json'
NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}


def now():
    return datetime.now(timezone(timedelta(hours=8))).isoformat(timespec='seconds')


def load_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def safe_output(root, value):
    root = Path(root).resolve()
    local = (root / '.local').resolve()
    if not local.is_relative_to(root):
        raise ValueError('.local cannot point outside this repository')
    path = Path(value)
    path = (root / path).resolve() if not path.is_absolute() else path.resolve()
    if path == local or not path.is_relative_to(local):
        raise ValueError('Output must be inside this repository .local directory')
    if path.exists():
        raise ValueError(f'Output already exists; use a new filename: {path.name}')
    return path


def save_new(root, value, content):
    path = safe_output(root, value)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(content if isinstance(content, str) else json.dumps(content, ensure_ascii=False, indent=2))
    return path


def source_records(binding, profile):
    result = {}
    project = Path(binding['project_root'])
    for key, relative in profile['sources'].items():
        path = (project / relative).resolve()
        if not path.is_relative_to(project.resolve()):
            raise ValueError('Source route escapes the bound project')
        result[key] = {'path': str(path), 'exists': path.is_file()}
        if path.is_file():
            result[key]['sha256'] = sha256(path)
    return result


def bind(project_root, assets_root, pricing_root, root=ROOT):
    profile = load_json(Path(root) / 'profiles/sovyn-my/profile.json')
    binding = {'created_at': now(), 'project_root': str(Path(project_root).resolve()),
               'assets_root': str(Path(assets_root).resolve()), 'pricing_root': str(Path(pricing_root).resolve())}
    for key in ('project_root', 'assets_root', 'pricing_root'):
        if not Path(binding[key]).is_dir():
            raise ValueError(f'Binding directory is missing: {key}')
    binding['sources'] = source_records(binding, profile)
    missing = [key for key, value in binding['sources'].items() if not value['exists']]
    if missing:
        raise ValueError('Required business documents missing: ' + ', '.join(missing))
    workbook = Path(binding['project_root']) / profile['workbook_relative_path']
    if not workbook.is_file():
        raise ValueError('Live workbench file is missing')
    binding['workbook'] = {'path': str(workbook), 'sha256_at_bind': sha256(workbook)}
    path = save_new(root, '.local/bindings.json', binding)
    return {'status': 'BOUND', 'path': str(path), 'captured_at': binding['created_at']}


def load_binding(root=ROOT):
    path = Path(root) / '.local/bindings.json'
    if not path.is_file():
        raise ValueError('Local binding is missing; run bind first')
    return load_json(path)


def doctor(root=ROOT):
    profile = load_json(Path(root) / 'profiles/sovyn-my/profile.json')
    binding = load_binding(root)
    records = source_records(binding, profile)
    changed = [key for key, record in records.items()
               if record.get('sha256') != binding['sources'].get(key, {}).get('sha256')]
    missing = [key for key, record in records.items() if not record['exists']]
    pricing = Path(binding['pricing_root']) / 'domain/calibrated_pricing.py'
    workbook = Path(binding['workbook']['path'])
    return {'status': 'MISSING' if missing or not workbook.is_file() or not pricing.is_file()
            else 'SOURCE_CHANGED' if changed else 'LOCAL_SOURCES_AVAILABLE',
            'captured_at': now(), 'changed_documents': changed, 'missing_documents': missing,
            'sources': records, 'workbook_exists': workbook.is_file(), 'pricing_kernel_exists': pricing.is_file(),
            'limit': 'Availability and hashes do not verify account policy, visual quality or sales.'}


def read_sheet_rows(path, sheet_name):
    """Read cached cell values only; no macros, formulas or external links execute."""
    with zipfile.ZipFile(path) as archive:
        if sum(item.file_size for item in archive.infolist()) > 200 * 1024 * 1024:
            raise ValueError('Workbook is too large for this read-only adapter')
        shared = []
        if 'xl/sharedStrings.xml' in archive.namelist():
            tree = ET.fromstring(archive.read('xl/sharedStrings.xml'))
            shared = [''.join(t.text or '' for t in item.findall('.//s:t', NS)) for item in tree.findall('s:si', NS)]
        book = ET.fromstring(archive.read('xl/workbook.xml'))
        selected = next((sheet for sheet in book.findall('s:sheets/s:sheet', NS)
                         if sheet.get('name') == sheet_name), None)
        if selected is None:
            raise ValueError(f'Workbook sheet not found: {sheet_name}')
        rid = selected.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
        links = ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))
        relation = next((item for item in links if item.get('Id') == rid), None)
        if relation is None or relation.get('TargetMode') == 'External':
            raise ValueError('Worksheet relationship is missing or external')
        target = relation.get('Target', '')
        member = target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/' + target)
        if not member.startswith('xl/worksheets/'):
            raise ValueError('Unexpected worksheet path')
        tree = ET.fromstring(archive.read(member))
        rows = []
        for row in tree.findall('s:sheetData/s:row', NS):
            cells = {}
            for cell in row.findall('s:c', NS):
                column = re.sub(r'\d', '', cell.get('r', ''))
                value = cell.find('s:v', NS)
                text = value.text if value is not None else None
                if cell.get('t') == 's' and text is not None:
                    text = shared[int(text)]
                elif cell.get('t') == 'inlineStr':
                    text = ''.join(t.text or '' for t in cell.findall('.//s:t', NS))
                if text is not None:
                    cells[column] = text
            rows.append({'row_number': int(row.get('r', '0')), 'cells': cells})
    return rows


def inventory(binding, folder):
    assets = Path(binding['assets_root']).resolve()
    product = (assets / folder).resolve()
    if product == assets or not product.is_relative_to(assets) or not product.is_dir():
        raise ValueError('Product folder must be inside the bound assets root')
    originals = product / '01_原始参考素材'
    if not originals.is_dir() or not originals.resolve().is_relative_to(assets):
        raise ValueError('Original source folder is missing or outside the assets root')
    files = []
    for item in sorted(originals.rglob('*')):
        if not item.is_file():
            continue
        if not item.resolve().is_relative_to(assets):
            raise ValueError('A source file points outside the bound assets root')
        files.append({'path': str(item), 'bytes': item.stat().st_size, 'sha256': sha256(item)})
    rows = read_sheet_rows(binding['workbook']['path'], '商品总表')
    header = next((row for row in rows if any('原始资料目录' in value for value in row['cells'].values())), None)
    if not header:
        raise ValueError('Workbench headers missing; do not guess column positions')
    source_columns = [column for column, name in header['cells'].items() if name.strip() == '原始资料目录']
    if len(source_columns) != 1:
        raise ValueError('Workbench original-folder header is missing or ambiguous')
    matches = []
    for row in rows:
        raw = row['cells'].get(source_columns[0])
        if raw and Path(raw).resolve() == originals.resolve():
            matches.append({'row_number': row['row_number'],
                            'fields': {header['cells'].get(col, col): value for col, value in row['cells'].items()}})
    return {'captured_at': now(), 'product_folder': str(product), 'originals': files,
            'workbench_matches': matches, 'identity_status': 'MATCHED_PATH' if len(matches) == 1 else 'REVIEW_REQUIRED',
            'visual_review': 'NOT_VERIFIED', 'workbook_sha256': sha256(binding['workbook']['path'])}
