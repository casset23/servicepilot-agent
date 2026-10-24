import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SourceWiringTests(unittest.TestCase):
    def test_all_app_imports_resolve_to_published_modules(self):
        backend = ROOT / 'backend'
        for path in backend.rglob('*.py'):
            for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
                if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith('app.'):
                    target = backend / node.module.replace('.', '/')
                    with self.subTest(file=str(path.relative_to(ROOT)), module=node.module):
                        self.assertTrue(target.with_suffix('.py').is_file() or target.is_dir())

    def test_agent_api_and_preview_entry_points_are_present(self):
        main = (ROOT / 'backend/main.py').read_text(encoding='utf-8')
        self.assertIn('@app.post("/api/langgraph/query")', main)
        self.assertIn('@app.post("/api/langgraph/resume")', main)
        builder = (ROOT / 'backend/app/lg_agent/lg_builder.py').read_text(encoding='utf-8')
        self.assertIn('from app.lg_agent.routing import route_query', builder)
        self.assertIn('add_conditional_edges("analyze_and_route_query", route_query)', builder)
