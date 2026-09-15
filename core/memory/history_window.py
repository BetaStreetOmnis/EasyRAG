from typing import Dict, List


DEFAULT_MAX_TURNS = 10
DEFAULT_MAX_MESSAGE_CHARS = 8000


def trim_history(history, max_turns=DEFAULT_MAX_TURNS,
                 max_message_chars=DEFAULT_MAX_MESSAGE_CHARS) -> List[Dict[str, str]]:
    """过滤、配对并窗口化服务端接收到的对话历史。"""
    if not history:
        return []

    valid_messages = []
    for message in history:
        if not isinstance(message, dict):
            continue
        if message.get("role") not in ("user", "assistant"):
            continue
        content = message.get("content")
        if not isinstance(content, str):
            continue
        valid_messages.append({
            "role": message["role"],
            "content": content[:max_message_chars],
        })

    pairs = []
    index = 0
    while index < len(valid_messages) - 1:
        user_message = valid_messages[index]
        assistant_message = valid_messages[index + 1]
        if user_message["role"] == "user" and assistant_message["role"] == "assistant":
            pairs.append([user_message, assistant_message])
            index += 2
        else:
            index += 1

    recent_pairs = pairs[-max_turns:] if max_turns > 0 else []
    return [message for pair in recent_pairs for message in pair]
