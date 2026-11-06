from app.detectors.common import make_result
from app.detectors.similarity import similarity
from app.tools_registry import TOOL_REGISTRY

# Chosen from calibrate_tool_fit.py (10 examples). Tune with the red-team results.
FIT_MIN_BEST = 0.25   # another tool must clearly match the question...
FIT_MARGIN = 0.20     # ...and beat the used tool by at least this much


def _result(flagged, reason, severity, policy="none", blocked=False):
    result = make_result("tool_misuse", flagged, reason, severity)
    result["policy"] = policy    # which rule was violated
    result["blocked"] = blocked  # True = must not run, False = only flagged
    return result


def validate_input(spec, tool_input: str):
    """Return a description of the problem, or None if the input is fine."""
    if len(tool_input) > spec.max_input_length:
        return f"Input is {len(tool_input)} characters, the limit for {spec.name} is {spec.max_input_length}"
    if len(tool_input.strip()) < spec.min_input_length:
        return f"Input is too short for {spec.name} (needs at least {spec.min_input_length} characters)"
    if spec.allowed_characters:
        bad = sorted({ch for ch in tool_input if ch not in spec.allowed_characters})
        if bad:
            return f"Input has characters not allowed for {spec.name}: {''.join(bad[:8])}"
    return None


def detect_tool_misuse(question: str, tool_name: str, tool_input: str,
                       allowed_risks: tuple = ("read_only",)) -> dict:
    # 1. Is the tool registered at all?
    spec = TOOL_REGISTRY.get(tool_name)
    if spec is None:
        return _result(True, f"Tool '{tool_name}' is not in the registry", 1.0, "registry", True)

    # 2. Is this kind of tool allowed for this task?
    if spec.risk not in allowed_risks:
        return _result(True, f"{tool_name} has risk level '{spec.risk}', which is not allowed here",
                       1.0, "risk_level", True)

    # 3. Are the arguments valid?
    problem = validate_input(spec, tool_input)
    if problem:
        return _result(True, problem, 0.8, "arguments", True)

    # 4. Does the question fit this tool? (only a flag, never a block)
    used_fit = similarity(question, spec.description)
    best_name, best_fit = None, 0.0
    for name, other in TOOL_REGISTRY.items():
        if name == tool_name:
            continue
        fit = similarity(question, other.description)
        if fit > best_fit:
            best_name, best_fit = name, fit
    if best_fit >= FIT_MIN_BEST and best_fit - used_fit >= FIT_MARGIN:
        return _result(
            True,
            f"Question looks like a job for {best_name} (fit {best_fit:.2f}) but {tool_name} was used (fit {used_fit:.2f})",
            0.6, "fit", False,
        )

    return _result(False, f"{tool_name} is acceptable for this question", 0.0)