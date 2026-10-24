import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from app.lg_agent.routing import route_query


class CustomerRoutingTests(unittest.TestCase):
    def test_customer_intents_select_the_corresponding_node(self):
        expected = {
            'general-query': 'respond_to_general_query',
            'additional-query': 'get_additional_info',
            'graphrag-query': 'create_research_plan',
            'image-query': 'create_image_query',
            'file-query': 'create_file_query',
        }
        for kind, node in expected.items():
            with self.subTest(intent=kind):
                self.assertEqual(route_query(SimpleNamespace(router={'type': kind})), node)

    def test_attached_image_takes_priority_over_text_classification(self):
        state = SimpleNamespace(router={'type': 'general-query'})
        config = {'configurable': {'image_path': 'uploads/example.png'}}
        self.assertEqual(route_query(state, config), 'create_image_query')

    def test_empty_image_configuration_keeps_text_route(self):
        for config in [None, {}, {'configurable': {}}, {'configurable': {'image_path': ''}}]:
            with self.subTest(config=config):
                state = SimpleNamespace(router={'type': 'additional-query'})
                self.assertEqual(route_query(state, config), 'get_additional_info')

    def test_unknown_intent_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Unknown router type'):
            route_query(SimpleNamespace(router={'type': 'unsupported'}))
