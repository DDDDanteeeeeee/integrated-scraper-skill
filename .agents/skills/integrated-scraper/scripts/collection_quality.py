"""Offline collection checks and source-document rendering; no browser or network."""
import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
from urllib.parse import urlsplit, urlunsplit


def public_url(value):
    if not isinstance(value, str) or re.search(r'[\s<>]', value):
        raise ValueError('Malformed source URL')
    u = urlsplit(value)
    if u.scheme not in ('http', 'https') or not u.hostname or u.username or u.password:
        raise ValueError('Expected public HTTP(S) URL without credentials')
    if re.search(r'(?i)(token|signature|password|cookie|session)=', u.query):
        raise ValueError('Do not persist signed or credential-bearing URLs')
    return urlunsplit((u.scheme.lower(), u.netloc.lower(), u.path or '/', u.query, ''))


def select_tab(tabs, expected_url, previous_target_id=None):
    """Match exact resource including query; a selected tab still needs live recheck."""
    matches = []
    expected = public_url(expected_url)
    for tab in tabs:
        try:
            if public_url(tab.get('url', '')) == expected:
                matches.append(tab)
        except ValueError:
            continue
    ids = [t.get('targetId', t.get('target_id')) for t in matches]
    if any(not isinstance(i, str) or not i for i in ids):
        raise ValueError('Tab target ID missing')
    if previous_target_id in ids or len(ids) == 1:
        return {'action': 'reuse', 'target_id': previous_target_id if previous_target_id in ids else ids[0],
                'requires_page_recheck': True}
    return {'action': 'inspect_candidates' if ids else 'target_missing',
            'candidate_ids': ids, 'requires_page_recheck': True}


def decode_capture(capture, allow_scalar_list=False):
    """JSON or explicitly selected flat scalar-list output, NOT general YAML."""
    value = capture.get('result')
    if value is None:
        try:
            value = json.loads(capture.get('stdout', ''))
        except (ValueError, TypeError) as exc:
            raise ValueError('Unrecognized output; retain raw capture') from exc
    if isinstance(value, dict) and 'unparsed' in value:
        if not allow_scalar_list:
            raise ValueError('Non-JSON output requires explicit scalar-list mode')
        rows = []
        for line in value['unparsed'].splitlines():
            if not line.strip():
                continue
            start = re.fullmatch(r'- ([A-Za-z_]+): (.*)', line)
            field = re.fullmatch(r'  ([A-Za-z_]+): (.*)', line)
            if start:
                rows.append({})
            match = start or field
            if not match or not rows:
                raise ValueError('Unsupported nesting or multiline scalar')
            key, scalar = match.groups()
            if key in rows[-1]:
                raise ValueError('Duplicate scalar key')
            if scalar.startswith(('!', '&', '*', '{', '[', '|', '>')):
                raise ValueError('Unsupported scalar syntax')
            if scalar.startswith(('"', "'")):
                if scalar[-1:] != scalar[0] or len(scalar) < 2:
                    raise ValueError('Unclosed scalar')
                scalar = json.loads(scalar) if scalar[0] == '"' else scalar[1:-1].replace("''", "'")
            rows[-1][key] = scalar
        value = rows
    return {'payload': value, 'exit_code': capture.get('exit_code'),
            'command_ok': type(capture.get('exit_code')) is int and capture['exit_code'] == 0,
            'acceptance_passed': False}


def comment_expression(container_selector, body_selector):
    """Call only with selectors already observed on the current page."""
    container, body = json.dumps(container_selector), json.dumps(body_selector)
    return (f"Array.from(document.querySelectorAll({container})).map(e=>({{"
            "id:e.getAttribute('thingid')||e.id,"
            f"text:Array.from(e.querySelectorAll({body})).filter(n=>"
            f"n.closest({container})===e).map(n=>n.innerText).join('\\n')"
            "}))")


def audit_comments(data):
    if not isinstance(data, dict):
        raise ValueError('Comment audit must be an object')
    rows = data['records']
    if not isinstance(rows, list):
        raise ValueError('records must be a list')
    issues, seen, duplicates = [], set(), []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('Each comment record must be an object')
        identifier = (row.get('source_url'), row.get('id'))
        if not all(isinstance(x, str) and x for x in identifier):
            issues.append('missing_stable_identity')
            continue
        if identifier in seen:
            duplicates.append(row['id'])
        seen.add(identifier)
        if row.get('removed') is True and row.get('text_original'):
            issues.append('removed_parent_has_body')
        if row.get('removed') is not True and (not isinstance(row.get('text_original'), str) or not row['text_original'].strip()):
            issues.append('missing_body')
    if duplicates:
        issues.append('duplicate_identity')
    if len({url for url, identifier in seen}) > 1:
        issues.append('mixed_source_counts')
    ready = data.get('page_state') == 'content_ready'
    if not ready:
        issues.append('page_not_ready')
    total = data.get('displayed_count')
    same_unit = data.get('count_unit') == 'all_comment_nodes'
    if type(total) is not int or total < 0 or not same_unit:
        issues.append('count_not_comparable')
        gap = None
    else:
        gap = total - len(seen)
        if gap != 0:
            issues.append('count_gap')
    return {'ok': not issues, 'issues': sorted(set(issues)), 'duplicate_ids': duplicates,
            'unique_nodes': len(seen), 'displayed_count': total, 'gap': gap,
            'zero_verified': ready and same_unit and type(total) is int and total == 0 and not rows,
            'note': 'Count equality does not establish relevance, date or authenticity.'}


def date_window(published, start, end):
    low, high = datetime.fromisoformat(start), datetime.fromisoformat(end)
    if low.tzinfo is None or high.tzinfo is None or low > high:
        raise ValueError('Window requires ordered timezone-aware bounds')
    try:
        point = datetime.fromisoformat(published.replace('Z', '+00:00'))
        if point.tzinfo is None:
            return 'date_unconfirmed'
    except (ValueError, AttributeError):
        return 'date_unconfirmed'
    return 'within_window' if low <= point <= high else 'outside_window'


def originals_text(data, run_dir, output):
    """Explicit reviewed records; hashes and relative links, no overwriting sources."""
    run_dir, output = Path(run_dir).resolve(), Path(output).resolve()
    if not isinstance(data, dict) or not isinstance(data.get('records'), list):
        raise ValueError('Source inventory requires a records array')
    groups = {}
    for row in data['records']:
        if not isinstance(row, dict) or type(row.get('include', True)) is not bool:
            raise ValueError('Each record must be an object; include must be boolean')
        if row.get('include', True) is False:
            if row.get('exclusion_reason') not in ('duplicate', 'sensitive', 'non_content', 'removed'):
                raise ValueError('Exclusion requires duplicate/sensitive/non_content/removed reason')
            continue
        if row.get('kind') not in ('comment', 'post', 'danmaku', 'article'):
            raise ValueError('Only source content belongs in original-content MD')
        rel = Path(row['source_file'])
        path = (run_dir / rel).resolve()
        if rel.is_absolute() or not path.is_relative_to(run_dir) or not path.is_file():
            raise ValueError('Source path missing or outside run directory')
        if hashlib.sha256(path.read_bytes()).hexdigest() != row['source_sha256']:
            raise ValueError('Source hash mismatch')
        public_url(row['source_url'])
        if not isinstance(row['text_original'], str) or not row['text_original'].strip():
            raise ValueError('Original text required')
        if row.get('removed') is True:
            raise ValueError('Removed placeholders are not original statements')
        page = public_url(row.get('page_url', row['source_url']))
        for field in ('platform', 'captured_at'):
            if not isinstance(row.get(field), str) or not row[field].strip():
                raise ValueError(f'{field} must be a nonempty string')
        groups.setdefault((row['platform'], page), []).append(row)
    def inline(value):
        return re.sub(r'[\r\n<>\x60\[\]]', ' ', str(value))
    count = sum(map(len, groups.values()))
    lines = [f'# 源数据记录\n\n共 {len(groups)} 个来源页面，{count} 条内容。保留已采原文；不代表平台全量，缺失日期不补造。\n']
    if not count:
        lines.append('\n本次没有可展示的源内容；是否为真实零结果以采集验收为准。\n')
    sources = {}
    last_platform = None
    kinds = {'comment': '评论', 'post': '正文', 'article': '正文', 'danmaku': '弹幕'}
    platform_order = list(dict.fromkeys(platform for platform, page in groups))
    ordered_groups = sorted(groups, key=lambda key: platform_order.index(key[0]))
    for platform, page in ordered_groups:
        rows = groups[(platform, page)]
        if platform != last_platform:
            lines.append(f'\n## {inline(platform)}\n')
            last_platform = platform
        lines.append(f"\n### {inline(rows[0].get('page_title', rows[0].get('title', '内容页面')))}\n\n[打开原页面](<{page}>)\n")
        for i, row in enumerate(rows, 1):
            link = Path(os.path.relpath(run_dir / row['source_file'], output.parent)).as_posix()
            key = (link, row['source_sha256'])
            if key not in sources:
                sources[key] = {'number': len(sources) + 1, 'times': set()}
            sources[key]['times'].add(row['captured_at'])
            text = row['text_original']
            fence = chr(96) * max(3, 1 + max([len(m.group()) for m in re.finditer(chr(96)+'+', text)] or [0]))
            label = '回复' if row.get('parent_id') else kinds[row['kind']]
            parent = f" · 回复对象：{inline(row['parent_id'])}" if row.get('parent_id') else ''
            identifier = f" · ID {inline(row['id'])}" if row.get('id') else ''
            source_ref = f" · [源{sources[key]['number']}](#source-{sources[key]['number']})"
            lines.append(f"\n**{label} {i} · {inline(row.get('author_public', '未提供作者'))} · {inline(row.get('published_raw', '日期未提供'))}**{identifier}{parent}{source_ref}\n\n"
                         f"{fence}text\n{text}\n{fence}\n")
            if row.get('context'):
                lines.append(f"\n备注：{inline(row['context'])}\n")
            if row['source_url'] != page:
                lines.append(f"\n[原文定位](<{row['source_url']}>)\n")
    lines.append('\n## 来源文件索引\n\n校验信息集中保留，正文不重复展示。\n')
    for (link, digest), source in sources.items():
        lines.append(f"\n<a id=\"source-{source['number']}\"></a>\n\n- [源文件 {source['number']}](<{link}>) · 采集：{inline(', '.join(sorted(source['times'])))}\n  SHA256：{digest}\n")
    return ''.join(lines), count


def render_originals(data, run_dir, output):
    text, count = originals_text(data, run_dir, output)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', encoding='utf-8') as stream:
        stream.write(text)
    return {'records': count, 'output': str(output)}


def validate_documents(records_path, run_dir, report, source_document):
    report, source_document = Path(report).resolve(), Path(source_document).resolve()
    if report == source_document:
        raise ValueError('Analysis and source documents must be separate files')
    for path in (report, source_document):
        if path.suffix.lower() != '.md' or not path.is_file() or not path.read_text(encoding='utf-8-sig').strip():
            raise ValueError('Both nonempty Markdown deliverables are required')
    data = json.loads(Path(records_path).read_text(encoding='utf-8-sig'))
    expected, count = originals_text(data, run_dir, source_document)
    if source_document.read_text(encoding='utf-8-sig') != expected:
        raise ValueError('Source document differs from complete supplied content inventory')
    return count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['decode', 'tabs', 'audit', 'render'])
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--run-dir', type=Path)
    parser.add_argument('--scalar-list', action='store_true')
    args = parser.parse_args()
    try:
        data = json.loads(args.input.read_text(encoding='utf-8-sig'))
        if args.action == 'decode':
            result = decode_capture(data, args.scalar_list)
        elif args.action == 'tabs':
            result = select_tab(data['tabs'], data['expected_url'], data.get('previous_target_id'))
        elif args.action == 'audit':
            result = audit_comments(data)
        else:
            if not args.run_dir or not args.output:
                raise ValueError('render requires --run-dir and --output')
            result = render_originals(data, args.run_dir, args.output)
        if args.output and args.action != 'render':
            with args.output.open('x', encoding='utf-8') as stream:
                json.dump(result, stream, ensure_ascii=False, indent=2)
        print(json.dumps(result, ensure_ascii=False))
        return 1 if args.action == 'audit' and not result['ok'] else 0
    except (OSError, ValueError, TypeError, KeyError) as error:
        print(json.dumps({'ok': False, 'error': str(error)}, ensure_ascii=False))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
