"""Regressions for read-only checks, status scope and script-safe embedding."""
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import build_catalogue
from catalogue_presentation import build_presentations


class CatalogueTests(unittest.TestCase):
    def test_scope_and_unresolved_readings_are_visible(self):
        versions = json.loads((ROOT / 'data/versions.json').read_text())
        labels = build_presentations(versions)
        self.assertIn('美国', labels['en-kerr-iww-1919']['rights'])
        self.assertNotIn('中国', labels['en-kerr-iww-1919']['rights'])
        self.assertIn('未决疑读', labels['en-kerr-iww-1919']['collation'])
        self.assertIn('结构及部分异文', labels['ru-kots-complete-publication-disputed']['collation'])
        self.assertIn('权利依据待补', labels['zh-collective-1962']['rights'])

    def test_hostile_source_heading_cannot_close_json_script(self):
        original = build_catalogue.load
        heading = '</script><script>alert("source heading")</script>'

        def load(name):
            data = original(name)
            if name == 'data/discoveries/antiwarsongs.json':
                data[0]['title_as_reported'] = heading
            return data

        with patch.object(build_catalogue, 'load', load):
            viewer = build_catalogue.build_outputs()['catalogue.html'].decode()
        payload = re.search(r'<script id="catalogue-data" type="application/json">(.*?)</script>', viewer, re.S)[1]
        self.assertNotIn('<', payload)
        self.assertEqual(json.loads(payload)['entries'][0]['title_as_reported'], heading)

    def test_check_rejects_stale_template_without_rewriting(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for folder in ['scripts', 'data', 'catalogue', 'docs']:
                shutil.copytree(ROOT / folder, root / folder)
            shutil.copy2(ROOT / 'catalogue.html', root / 'catalogue.html')
            template = root / 'scripts/catalogue.template.html'
            template.write_text(template.read_text() + '\n<!-- template changed -->\n')
            before = (root / 'catalogue.html').read_bytes()
            result = subprocess.run([sys.executable, str(root / 'scripts/build_catalogue.py'), '--check'], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('catalogue.html', result.stderr)
            self.assertEqual((root / 'catalogue.html').read_bytes(), before)

    def test_generated_markdown_contains_every_version_detail(self):
        versions = json.loads((ROOT / 'data/versions.json').read_text())
        text = build_catalogue.build_outputs()['catalogue/versions.md'].decode()
        for version in versions:
            self.assertIn(f"### {version['id']}\n", text)
            if version['lyrics_path']:
                self.assertIn(f"(../{version['lyrics_path']})", text)


if __name__ == '__main__':
    unittest.main()
