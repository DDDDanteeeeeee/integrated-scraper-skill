"""Synthetic regression fixtures; no personal comments or live platform credentials."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / '.agents/skills/integrated-scraper/scripts'
spec = importlib.util.spec_from_file_location('quality', SCRIPTS / 'collection_quality.py')
q = importlib.util.module_from_spec(spec)
spec.loader.exec_module(q)


class QualityTests(unittest.TestCase):
    def test_resume_exact_tab_not_title_domain_or_other_query(self):
        tabs = [{'targetId': 'a', 'url': 'https://example.org/search?q=one', 'title': 'Same'},
                {'targetId': 'b', 'url': 'https://example.org/search?q=two', 'title': 'Same'}]
        self.assertEqual(q.select_tab(tabs, tabs[0]['url'], 'a')['target_id'], 'a')
        self.assertEqual(q.select_tab(tabs, 'https://other.example/search?q=one')['action'], 'target_missing')
        tabs.append({'targetId': 'c', 'url': tabs[0]['url']})
        self.assertEqual(q.select_tab(tabs, tabs[0]['url'])['action'], 'inspect_candidates')
        self.assertEqual(q.select_tab(tabs, tabs[0]['url'], 'c')['target_id'], 'c')

    def test_signed_and_credential_urls_rejected(self):
        for url in ['https://u:p@example.org/', 'https://example.org/?xsec_token=private', 'file:///c:/x']:
            with self.assertRaises(ValueError):
                q.public_url(url)

    def test_nonzero_payload_never_success(self):
        result = q.decode_capture({'exit_code': 1, 'result': {'unparsed': "- rank: 1\n  text: 中文原话\n  author: '46'\n"}}, True)
        self.assertEqual(result['payload'][0]['text'], '中文原话')
        self.assertFalse(result['command_ok'])
        self.assertFalse(result['acceptance_passed'])
        self.assertEqual(q.decode_capture({'exit_code': 0, 'stdout': '[]'})['payload'], [])

    def test_unrecognized_formats_fail_closed(self):
        for text in ['- text: |\n    nested', '- text: !object', '- text: hi\n  text: duplicate', 'warning\n- text: hi']:
            with self.subTest(text=text), self.assertRaises(ValueError):
                q.decode_capture({'result': {'unparsed': text}}, True)
        with self.assertRaises(ValueError):
            q.decode_capture({'result': {'unparsed': '- text: hi'}})

    def row(self, identifier='1', text='原话'):
        return {'source_url': 'https://example.org/post', 'id': identifier, 'text_original': text}

    def data(self, rows, total):
        return {'records': rows, 'page_state': 'content_ready', 'displayed_count': total,
                'count_unit': 'all_comment_nodes'}

    def test_count_and_zero_gates(self):
        with self.assertRaises(ValueError):
            q.audit_comments(self.data([None], 1))
        self.assertIn('missing_body', q.audit_comments(self.data([self.row(text=None)], 1))['issues'])
        self.assertTrue(q.audit_comments(self.data([], 0))['zero_verified'])
        data = self.data([], 0)
        data['page_state'] = 'login_required'
        self.assertFalse(q.audit_comments(data)['zero_verified'])
        self.assertIn('count_gap', q.audit_comments(self.data([self.row()], 2))['issues'])
        data = self.data([self.row()], 1)
        data['count_unit'] = 'root_comments'
        self.assertIn('count_not_comparable', q.audit_comments(data)['issues'])

    def test_removed_parent_duplicate_and_empty_body(self):
        row = dict(self.row(), removed=True)
        self.assertIn('removed_parent_has_body', q.audit_comments(self.data([row], 1))['issues'])
        self.assertIn('duplicate_identity', q.audit_comments(self.data([self.row(), self.row()], 2))['issues'])
        self.assertIn('missing_body', q.audit_comments(self.data([self.row(text='')], 1))['issues'])
        self.assertTrue(q.audit_comments(self.data([dict(self.row(text=''), removed=True)], 1))['ok'])

    def test_date_no_year_no_invention(self):
        bounds = ('2026-06-13T00:00:00+08:00', '2026-09-11T12:00:00+08:00')
        for value in ['06-26 01:18', '2个月前', '2026-06-26']:
            self.assertEqual(q.date_window(value, *bounds), 'date_unconfirmed')
        self.assertEqual(q.date_window('2026-08-01T00:00:00Z', *bounds), 'within_window')
        self.assertEqual(q.date_window('2026-10-01T00:00:00Z', *bounds), 'outside_window')

    def test_renderer_portable_and_literal(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / 'first'; root.mkdir()
            source = root / 'raw/source.json'
            source.parent.mkdir(); source.write_text('{"public": "原文"}', encoding='utf-8')
            row = dict(self.row(), include=True, kind='comment', platform='Example',
                       source_file='source.json', source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                       captured_at='2026-09-11T00:00:00Z', text_original='原话\n' + chr(96)*3 + '\n<script>text</script>')
            output = root / 'reports/original.md'
            q.render_originals({'records': [row]}, source.parent, output)
            result = output.read_text(encoding='utf-8')
            self.assertIn(row['text_original'], result)
            self.assertIn('../raw/source.json', result)
            self.assertNotIn(str(root), result)
            moved = Path(temp) / 'new computer 中文'
            shutil.copytree(root, moved)
            self.assertTrue((moved/'reports/../raw/source.json').is_file())
            with self.assertRaises(FileExistsError):
                q.render_originals({'records': [row]}, source.parent, output)
            for patch in [{'source_file': '../outside'}, {'source_sha256': 'wrong'}, {'kind': 'error'}]:
                with self.assertRaises(ValueError):
                    q.render_originals({'records': [dict(row, **patch)]}, source.parent, root/'bad.md')


if __name__ == '__main__':
    unittest.main()
