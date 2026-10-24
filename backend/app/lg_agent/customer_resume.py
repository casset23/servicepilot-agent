from langchain_core.messages import HumanMessage
from langgraph.types import interrupt


def wait_for_customer(state):
    # Keep the model's clarification in the previous node so resume does not call the model twice.
    answer = interrupt({'type': 'customer_input', 'question': state.messages[-1].content})
    if not isinstance(answer, str) or not answer.strip():
        raise ValueError('Customer response must be non-empty text')
    return {'messages': [HumanMessage(content=answer)], 'awaiting_customer': False}
