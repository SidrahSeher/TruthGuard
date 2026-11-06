from app.detectors.common import make_result

LOOP_THRESHOLD = 3  # same call this many times = loop


def detect_loop(tool_calls: list, threshold: int = LOOP_THRESHOLD) -> dict:
    """tool_calls looks like [{"tool": "document_search", "input": "..."}, ...]"""
    counts = {}
    for call in tool_calls:
        key = (call["tool"], call["input"].strip().lower())
        counts[key] = counts.get(key, 0) + 1

    if counts:
        (tool, _), n = max(counts.items(), key=lambda item: item[1])
        if n >= threshold:
            severity = min(1.0, 0.6 + 0.1 * (n - threshold))
            return make_result(
                "loop", True, f"{tool} called {n} times with the same input", severity
            )

    return make_result("loop", False, "No repeated calls", 0.0)