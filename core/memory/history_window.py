from typing import Dict, List


DEFAULT_MAX_TURNS = 10
DEFAULT_MAX_MESSAGE_CHARS = 8000


def resolve_limits(max_turns=None, max_message_chars=None) -> Dict[str, int]:
    """解析调用方指定的历史窗口上限，非法值回退默认配置。"""
    resolved_limits = {
        "max_turns": DEFAULT_MAX_TURNS,
        "max_message_chars": DEFAULT_MAX_MESSAGE_CHARS,
    }
    if isinstance(max_turns, int) and not isinstance(max_turns, bool) and 1 <= max_turns <= 100:
        resolved_limits["max_turns"] = max_turns
    if (
        isinstance(max_message_chars, int)
        and not isinstance(max_message_chars, bool)
        and 100 <= max_message_chars <= 100000
    ):
        resolved_limits["max_message_chars"] = max_message_chars
    return resolved_limits


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
