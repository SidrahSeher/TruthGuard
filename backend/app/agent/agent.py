import time
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from app.agent.llm import get_llm
from app.agent.tools import calculator, document_search, summarizer
from app.detectors.tool_misuse import detect_tool_misuse

TOOL_NAMES = ["document_search", "calculator", "summarizer"]
MIN_SUMMARY_TEXT = 40          # same limit as the summarizer rule in the tool registry
NO_RESULT = "No matching document found."
BLOCKED_PREFIX = "Blocked by policy"


class AgentState(TypedDict):
    question: str
    tool: str
    tool_input: str
    tool_output: str
    evidence: str
    tool_calls: list
    answer: str
    steps: list


def make_event(step: str, detail) -> dict:
    """One entry of the trace log."""
    return {"step": step, "detail": str(detail)[:300], "time": time.time()}


DECIDE_PROMPT = """You have three tools:
- document_search: find facts in university policy documents.
- calculator: do math calculations.
- summarizer: shorten a piece of text.

Choose the best tool for the question. Reply with only one word:
document_search, calculator, or summarizer.

Question: {question}"""

MATH_PROMPT = """Write only the math expression for this question, using numbers
and + - * / ( ) only. No words, no equals sign.

Question: {question}"""

ANSWER_PROMPT = """Answer the question using ONLY the information below.
If the information does not contain the answer, say you could not find it.
Keep the answer to one or two sentences.

Information:
{tool_output}

Question: {question}"""


# ---------- Node 1: decide which tool to use ----------
def decide(state: AgentState):
    llm = get_llm()
    reply = llm.invoke(DECIDE_PROMPT.format(question=state["question"])).content.lower()
    tool = next((name for name in TOOL_NAMES if name in reply), "document_search")

    tool_input = state["question"]
    if tool == "calculator":
        direct = "".join(ch for ch in state["question"] if ch in "0123456789+-*/(). ").strip()
        if any(c.isdigit() for c in direct) and any(op in direct for op in "+-*/"):
            tool_input = direct
        else:
            raw = llm.invoke(MATH_PROMPT.format(question=state["question"])).content
            cleaned = "".join(ch for ch in raw if ch in "0123456789+-*/(). ")
            tool_input = cleaned.strip() or state["question"]

    return {"tool": tool, "tool_input": tool_input}


# ---------- Running one tool, after the policy check ----------
def _execute(question, tool, text, steps, calls):
    """Check the policy FIRST. A blocked call never runs. Returns (output, blocked)."""
    calls.append({"tool": tool, "input": text})
    steps.append(make_event("tool_called", f"{tool}({text})"))

    check = detect_tool_misuse(question, tool, text)
    if check["blocked"]:
        output = f"{BLOCKED_PREFIX} ({check['policy']}): {check['reason']}"
        steps.append(make_event("tool_blocked", output))
        return output, True
    if check["flagged"]:
        steps.append(make_event("tool_flagged", check["reason"]))

    if tool == "calculator":
        output = calculator(text)
    elif tool == "summarizer":
        output = summarizer(text)
    else:
        results = document_search(text)
        output = "\n".join(p["text"] for p in results) if results else NO_RESULT

    steps.append(make_event("tool_result", output))
    return output, False


# ---------- Node 2: run the chosen tool ----------
def run_tool(state: AgentState):
    question, tool, text = state["question"], state["tool"], state["tool_input"]
    steps, calls = list(state["steps"]), list(state["tool_calls"])

    if tool == "summarizer":
        # The summarizer needs a real text: pasted after a colon, or found in the documents.
        pasted = question.split(":", 1)[1].strip() if ":" in question else ""
        if len(pasted) >= MIN_SUMMARY_TEXT:
            source = pasted
        else:
            found = document_search(question[:500])
            source = "\n".join(p["text"] for p in found) if found else NO_RESULT
            steps.append(make_event("evidence_retrieved", source))
            if source == NO_RESULT:
                return {"tool_output": source, "evidence": source,
                        "tool_calls": calls, "steps": steps}
        output, blocked = _execute(question, "summarizer", source[:5000], steps, calls)
        return {"tool_output": output, "evidence": output if blocked else source,
                "tool_calls": calls, "steps": steps}

    output, blocked = _execute(question, tool, text, steps, calls)
    return {"tool_output": output, "evidence": output, "tool_calls": calls, "steps": steps}


# ---------- Node 3: write the final answer ----------
def answer(state: AgentState):
    if state["tool_output"].startswith(BLOCKED_PREFIX):
        text = "Sorry, this request was blocked by the safety policy."
    else:
        llm = get_llm()
        prompt = ANSWER_PROMPT.format(tool_output=state["tool_output"], question=state["question"])
        text = llm.invoke(prompt).content.strip()
    return {"answer": text, "steps": state["steps"] + [make_event("answer_generated", text)]}


def build_agent():
    graph = StateGraph(AgentState)
    graph.add_node("decide", decide)
    graph.add_node("run_tool", run_tool)
    graph.add_node("answer", answer)
    graph.add_edge(START, "decide")
    graph.add_edge("decide", "run_tool")
    graph.add_edge("run_tool", "answer")
    graph.add_edge("answer", END)
    return graph.compile()


def run_agent(question: str, on_update=None) -> dict:
    """Run the agent. If on_update is given, it is called after every step of the flowchart
    (decide, run_tool, answer) with the state so far, so a page can show live progress."""
    agent = build_agent()
    state = {
        "question": question,
        "tool": "",
        "tool_input": "",
        "tool_output": "",
        "evidence": "",
        "tool_calls": [],
        "answer": "",
        "steps": [make_event("task_started", question)],
    }
    if on_update is None:
        return agent.invoke(state)
    for update in agent.stream(state, stream_mode="updates"):
        for changes in update.values():
            state.update(changes)
        on_update(dict(state))
    return state