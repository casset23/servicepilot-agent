import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, END, StateGraph
from langgraph.types import Command
from app.lg_agent.lg_states import AgentState, InputState
from app.lg_agent.routing import route_after_additional, route_query
from app.lg_agent.customer_resume import wait_for_customer


class CustomerResumeTests(unittest.TestCase):
    def graph(self, needs_input=True):
        builder = StateGraph(AgentState, input=InputState)
        def clarify(state):
            return {'messages': [AIMessage(content='请提供订单号')], 'awaiting_customer': needs_input}
        def answer(state):
            return {'messages': [AIMessage(content='已收到：' + state.messages[-1].content)]}
        builder.add_node('clarify', clarify)
        builder.add_node(wait_for_customer)
        builder.add_node('respond', answer)
        builder.add_edge(START, 'clarify')
        builder.add_conditional_edges('clarify', route_after_additional)
        builder.add_edge('wait_for_customer', 'respond')
        builder.add_edge('respond', END)
        return builder.compile(checkpointer=MemorySaver())

    def test_real_graph_interrupts_and_resumes_with_customer_message(self):
        graph = self.graph()
        config = {'configurable': {'thread_id': 'resume-case'}}
        first = graph.invoke({'messages': [HumanMessage(content='订单到哪了')]}, config)
        self.assertEqual(graph.get_state(config).tasks[0].interrupts[0].value['question'], '请提供订单号')
        self.assertTrue(graph.get_state(config).tasks[0].interrupts)
        final = graph.invoke(Command(resume='ORDER-123'), config)
        self.assertEqual(final['messages'][-1].content, '已收到：ORDER-123')
        self.assertFalse(final['awaiting_customer'])

    def test_out_of_scope_response_does_not_wait_for_input(self):
        graph = self.graph(needs_input=False)
        result = graph.invoke({'messages': [HumanMessage(content='其他问题')]},
                              {'configurable': {'thread_id': 'no-input-case'}})
        self.assertNotIn('__interrupt__', result)
        self.assertEqual(result['messages'][-1].content, '请提供订单号')

    def test_real_state_reads_image_path_from_runtime_config(self):
        state = AgentState(messages=[], router={'type': 'general-query', 'logic': ''})
        self.assertFalse(hasattr(state, 'config'))
        self.assertEqual(route_query(state, {'configurable': {'image_path': 'uploads/photo.png'}}),
                         'create_image_query')


class CustomerStreamTests(unittest.IsolatedAsyncioTestCase):
    async def test_query_and_resume_streams_emit_protocol_events(self):
        from app.lg_agent.streaming import stream_customer_events
        graph = CustomerResumeTests().graph()
        config = {'configurable': {'thread_id': 'stream-resume'}}
        initial = [event async for event in stream_customer_events(
            graph, {'messages': [HumanMessage(content='order')]}, config)]
        self.assertIn('"interruption": true', ''.join(initial))
        self.assertEqual(initial[-1], 'data: [DONE]\n\n')
        resumed = [event async for event in stream_customer_events(graph, Command(resume='123'), config)]
        self.assertNotIn('"interruption": true', ''.join(resumed))
        self.assertEqual(resumed[-1], 'data: [DONE]\n\n')

    async def test_routing_receives_runtime_config_in_real_graph(self):
        graph = StateGraph(AgentState)
        graph.add_node('classify', lambda state: {})
        graph.add_node('create_image_query', lambda state: {'answer': 'image'})
        graph.add_node('respond_to_general_query', lambda state: {'answer': 'text'})
        graph.add_edge(START, 'classify')
        graph.add_conditional_edges('classify', route_query,
            {'create_image_query': 'create_image_query', 'respond_to_general_query': 'respond_to_general_query'})
        graph.add_edge('create_image_query', END)
        graph.add_edge('respond_to_general_query', END)
        result = await graph.compile().ainvoke({'messages': []},
            {'configurable': {'image_path': 'image.png'}})
        self.assertEqual(result['answer'], 'image')
