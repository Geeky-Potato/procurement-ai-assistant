"""LangGraph ReAct agent that answers questions over the procurement data.

The agent is given read-only MongoDB tools and a description of the collection
schema. It decides which queries to run, executes them, and writes a natural
-language answer grounded in the results.
"""
from __future__ import annotations

from functools import lru_cache

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.prebuilt import create_react_agent

from app.agent.schema import COLLECTION_SCHEMA
from app.agent.tools import TOOLS
from app.core.config import get_settings

SYSTEM_PROMPT = f"""\
You are a data analyst assistant for the State of California large-purchases
procurement dataset. You answer the user's questions by querying a MongoDB
collection through the provided tools, then explaining the results clearly.

{COLLECTION_SCHEMA}

How to work:
- Use the `aggregate` tool for sums, counts, averages, grouping and top-N
  questions (this is the common case). Use `find` to inspect example
  documents, `count` for simple totals, and `distinct` to discover the exact
  spelling of category values before filtering on them.
- Build queries only against the fields listed above. Never invent field names.
- When matching user-provided names (departments, suppliers), consider a
  case-insensitive regex, since exact casing may differ.
- Monetary amounts are in US dollars; sum `total_price` for spend questions.
- Prefer `fiscal_year` over raw dates for year-based questions.
- If a query returns nothing, reconsider the field/value (try `distinct`)
  rather than guessing repeatedly.

How to answer:
- Ground every number in tool results — never fabricate figures.
- Be concise. Format money with thousands separators and a $ sign.
- When useful, briefly note the query approach (e.g. "grouped by supplier,
  summed total_price"). Do not dump raw JSON at the user.
- If the question is ambiguous or outside this dataset, say so.
"""


def _build_llm() -> BaseChatModel:
    """Construct the chat model for the configured provider."""
    settings = get_settings()
    provider = settings.llm_provider.lower()

    if provider == "groq":
        from langchain_groq import ChatGroq

        return ChatGroq(
            model=settings.groq_model,
            api_key=settings.groq_api_key,
            temperature=0,
            max_tokens=2048,
        )

    raise ValueError(
        f"Unknown LLM_PROVIDER '{settings.llm_provider}'. "
        "Use 'groq'."
    )


@lru_cache
def get_agent():
    """Build (once) the compiled ReAct agent."""
    return create_react_agent(_build_llm(), TOOLS, state_modifier=SYSTEM_PROMPT)


def _to_messages(history: list[dict] | None, question: str) -> list:
    """Convert prior turns + the new question into LangChain messages."""
    messages = []
    for turn in history or []:
        role = turn.get("role")
        content = turn.get("content", "")
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))
    messages.append(HumanMessage(content=question))
    return messages


def ask(question: str, history: list[dict] | None = None) -> str:
    """Run the agent on a question and return the final answer text."""
    agent = get_agent()
    result = agent.invoke({"messages": _to_messages(history, question)})
    final = result["messages"][-1]
    content = final.content
    if isinstance(content, list):
        content = "".join(
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in content
        )
    return content
