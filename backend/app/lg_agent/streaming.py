import json


def has_pending_input(snapshot):
    return any(task.interrupts for task in snapshot.tasks)


async def stream_customer_events(graph, graph_input, config):
    async for message, metadata in graph.astream(graph_input, stream_mode="messages", config=config):
        if (message.content and "research_plan" not in metadata.get("tags", [])
                and not message.additional_kwargs.get("tool_calls")):
            yield "data: " + json.dumps(message.content, ensure_ascii=False) + "\n\n"
    if has_pending_input(graph.get_state(config)):
        payload = {"interruption": True, "conversation_id": config["configurable"]["thread_id"]}
        yield "data: " + json.dumps(payload) + "\n\n"
    yield "data: [DONE]\n\n"
