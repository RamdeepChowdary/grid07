"""
phase2/content_engine.py
------------------------
Phase 2: The Autonomous Content Engine (LangGraph)

Node flow:
  decide_search → web_search → draft_post

Output is strict JSON:
  {"bot_id": "...", "topic": "...", "post_content": "..."}

Run directly:
  python phase2/content_engine.py
"""

import sys, os, json, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from typing import TypedDict
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END
from llm_factory import get_llm

# ─────────────────────────────────────────────────────────
# Bot Personas
# ─────────────────────────────────────────────────────────

BOT_PERSONAS = {
    "bot_a": {
        "name": "Tech Maximalist",
        "system_prompt": (
            "You are Bot A — a Tech Maximalist. You believe AI and crypto will "
            "solve all human problems. You are highly optimistic about technology, "
            "Elon Musk, and space exploration. You dismiss regulatory concerns. "
            "Your tone is enthusiastic, bold, and slightly arrogant."
        ),
    },
    "bot_b": {
        "name": "Doomer / Skeptic",
        "system_prompt": (
            "You are Bot B — a Doomer/Skeptic. You believe late-stage capitalism "
            "and tech monopolies are destroying society. You are highly critical of "
            "AI, social media, and billionaires. You value privacy and nature. "
            "Your tone is cynical, urgent, and passionate."
        ),
    },
    "bot_c": {
        "name": "Finance Bro",
        "system_prompt": (
            "You are Bot C — a Finance Bro. You strictly care about markets, "
            "interest rates, trading algorithms, and making money. You speak in "
            "finance jargon and view everything through the lens of ROI. "
            "Your tone is sharp, data-driven, and unapologetically capitalist."
        ),
    },
}

# ─────────────────────────────────────────────────────────
# Mock Tool
# ─────────────────────────────────────────────────────────

@tool
def mock_searxng_search(query: str) -> str:
    """
    Simulates a SearXNG web search.
    Returns hardcoded recent headlines based on keywords in the query.
    """
    q = query.lower()

    if any(k in q for k in ["crypto", "bitcoin", "btc", "ethereum"]):
        return (
            "HEADLINE: Bitcoin surges past $95,000 as spot ETF inflows hit record $2B. "
            "HEADLINE: SEC approves three new crypto ETFs amid Washington policy shift. "
            "HEADLINE: El Salvador doubles down on Bitcoin legal tender amid IMF pressure."
        )
    elif any(k in q for k in ["ai", "openai", "llm", "gpt", "artificial intelligence"]):
        return (
            "HEADLINE: OpenAI releases GPT-5 — claims human-level reasoning on benchmarks. "
            "HEADLINE: 40% of junior developer roles at top firms frozen pending AI review. "
            "HEADLINE: EU AI Act enforcement begins; Silicon Valley lobbies for exemptions."
        )
    elif any(k in q for k in ["fed", "rate", "interest", "market", "stocks", "equit"]):
        return (
            "HEADLINE: Fed holds rates steady at 5.25%; signals two cuts possible in H2 2025. "
            "HEADLINE: S&P 500 rallies 1.8% on dovish Fed minutes; tech leads gains. "
            "HEADLINE: Hedge funds pile into short-duration bonds ahead of rate pivot."
        )
    elif any(k in q for k in ["climate", "environment", "nature", "carbon"]):
        return (
            "HEADLINE: 2024 confirmed hottest year on record — IPCC issues red alert. "
            "HEADLINE: Major oil companies lobbied against climate disclosure rules. "
            "HEADLINE: Youth-led climate lawsuits win landmark rulings across Europe."
        )
    elif any(k in q for k in ["elon", "musk", "spacex", "tesla"]):
        return (
            "HEADLINE: Elon Musk's xAI raises $6B Series B; Grok-3 outperforms GPT-4. "
            "HEADLINE: SpaceX Starship completes first orbital flight with full reuse. "
            "HEADLINE: Tesla FSD miles double quarter-over-quarter; robotaxi launch imminent."
        )
    elif any(k in q for k in ["privacy", "surveillance", "data", "meta", "zuckerberg"]):
        return (
            "HEADLINE: Meta fined €1.2B for GDPR violations; EU orders data transfer halt. "
            "HEADLINE: New report: 73% of free apps sell location data to data brokers. "
            "HEADLINE: Congress fails to pass federal privacy bill for the 8th consecutive year."
        )
    else:
        return (
            "HEADLINE: Global tech stocks rally on strong Q1 earnings. "
            "HEADLINE: AI investment hits $200B globally in 2024 per Goldman report. "
            "HEADLINE: Geopolitical tensions weigh on semiconductor supply chains."
        )


# ─────────────────────────────────────────────────────────
# LangGraph State
# ─────────────────────────────────────────────────────────

class PostState(TypedDict):
    bot_id        : str
    persona       : str
    search_query  : str
    topic         : str
    search_results: str
    post_content  : str
    final_json    : dict


# ─────────────────────────────────────────────────────────
# Node 1: Decide Search
# ─────────────────────────────────────────────────────────

def node_decide_search(state: PostState) -> PostState:
    """LLM reads persona → decides topic → formats search query."""
    print(f"\n[Node 1 — decide_search] Bot: {state['bot_id']}")

    llm = get_llm(temperature=0.8)
    messages = [
        SystemMessage(content=state["persona"]),
        HumanMessage(content=(
            "You are about to create a social media post. "
            "Decide what topic YOU find most interesting to post about today. "
            "Then write a short web search query to find the latest news on it.\n\n"
            "Respond ONLY with a JSON object (no markdown, no preamble):\n"
            '{"topic": "<1-5 word topic>", "search_query": "<search query string>"}'
        )),
    ]

    response = llm.invoke(messages)
    raw = re.sub(r"```json|```", "", response.content.strip()).strip()
    print(f"  LLM raw output: {raw}")

    try:
        parsed = json.loads(raw)
        topic        = parsed.get("topic", "technology trends")
        search_query = parsed.get("search_query", topic)
    except json.JSONDecodeError:
        topic        = "technology trends"
        search_query = "latest technology news"

    print(f"  → Topic: {topic}")
    print(f"  → Search query: {search_query}")

    return {**state, "topic": topic, "search_query": search_query}


# ─────────────────────────────────────────────────────────
# Node 2: Web Search
# ─────────────────────────────────────────────────────────

def node_web_search(state: PostState) -> PostState:
    """Calls mock_searxng_search tool and stores results in state."""
    print(f"\n[Node 2 — web_search] Query: \"{state['search_query']}\"")

    results = mock_searxng_search.invoke({"query": state["search_query"]})
    print(f"  → Results: {results[:120]}…")

    return {**state, "search_results": results}


# ─────────────────────────────────────────────────────────
# Node 3: Draft Post
# ─────────────────────────────────────────────────────────

def node_draft_post(state: PostState) -> PostState:
    """LLM uses persona + search results → generates strict JSON post."""
    print(f"\n[Node 3 — draft_post] Generating post…")

    llm = get_llm(temperature=0.9)
    messages = [
        SystemMessage(content=state["persona"]),
        HumanMessage(content=(
            f"Today's headlines on '{state['topic']}':\n\n"
            f"{state['search_results']}\n\n"
            "Using these as context, write a highly opinionated social media post "
            "(MAX 280 characters) reflecting your personality and worldview.\n\n"
            "Respond ONLY with a JSON object (no markdown, no extra text):\n"
            '{"bot_id": "' + state["bot_id"] + '", '
            '"topic": "<topic>", '
            '"post_content": "<your 280-char post>"}'
        )),
    ]

    response = llm.invoke(messages)
    raw = re.sub(r"```json|```", "", response.content.strip()).strip()
    print(f"  LLM raw output: {raw}")

    try:
        parsed = json.loads(raw)
        if len(parsed.get("post_content", "")) > 280:
            parsed["post_content"] = parsed["post_content"][:277] + "…"
        parsed["bot_id"] = state["bot_id"]
    except json.JSONDecodeError:
        parsed = {
            "bot_id"      : state["bot_id"],
            "topic"       : state["topic"],
            "post_content": raw[:280],
        }

    print(f"\n  ✅ Final JSON:\n  {json.dumps(parsed, indent=4)}")
    return {**state, "post_content": parsed["post_content"], "final_json": parsed}


# ─────────────────────────────────────────────────────────
# Build LangGraph
# ─────────────────────────────────────────────────────────

def build_content_graph():
    """Assemble and compile the LangGraph state machine."""
    graph = StateGraph(PostState)

    graph.add_node("decide_search", node_decide_search)
    graph.add_node("web_search",    node_web_search)
    graph.add_node("draft_post",    node_draft_post)

    graph.set_entry_point("decide_search")
    graph.add_edge("decide_search", "web_search")
    graph.add_edge("web_search",    "draft_post")
    graph.add_edge("draft_post",    END)

    return graph.compile()


def generate_post_for_bot(bot_id: str) -> dict:
    """High-level entry point: run the full graph for a given bot."""
    if bot_id not in BOT_PERSONAS:
        raise ValueError(f"Unknown bot_id: {bot_id!r}")

    initial_state: PostState = {
        "bot_id"        : bot_id,
        "persona"       : BOT_PERSONAS[bot_id]["system_prompt"],
        "search_query"  : "",
        "topic"         : "",
        "search_results": "",
        "post_content"  : "",
        "final_json"    : {},
    }

    graph = build_content_graph()
    final_state = graph.invoke(initial_state)
    return final_state["final_json"]


# ─────────────────────────────────────────────────────────
# Demo
# ─────────────────────────────────────────────────────────

def demo():
    print("\n" + "═" * 60)
    print("  PHASE 2 — Autonomous Content Engine Demo")
    print("═" * 60)

    for bot_id in ["bot_a", "bot_b", "bot_c"]:
        print(f"\n{'─'*60}")
        print(f"  Running graph for {bot_id} ({BOT_PERSONAS[bot_id]['name']})")
        print(f"{'─'*60}")
        result = generate_post_for_bot(bot_id)
        print(f"\n  📝 Final post JSON:\n  {json.dumps(result, indent=2)}")

    print("\n" + "═" * 60 + "\n")


if __name__ == "__main__":
    demo()