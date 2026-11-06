from dataclasses import dataclass


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str                 # one sentence: what the tool is for (used by the fit check)
    risk: str                        # "read_only", "writes_data" or "external"
    max_input_length: int = 2000
    min_input_length: int = 0
    allowed_characters: str = ""     # if set, the input may contain only these characters


TOOL_REGISTRY = {
    "document_search": ToolSpec(
        name="document_search",
        description="Find facts, rules and policies in the stored documents",
        risk="read_only",
        max_input_length=500,
    ),
    "calculator": ToolSpec(
        name="calculator",
        description="Calculate numbers and solve math expressions",
        risk="read_only",
        max_input_length=200,
        allowed_characters="0123456789+-*/(). ",
    ),
    "summarizer": ToolSpec(
        name="summarizer",
        description="Shorten a piece of text into a brief summary",
        risk="read_only",
        max_input_length=5000,
        min_input_length=40,
    ),
}