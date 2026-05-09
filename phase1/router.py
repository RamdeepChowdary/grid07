"""
phase1/router.py
----------------
Phase 1: Vector-Based Persona Matching (The Router)

Steps:
  1. Define three Bot Personas as plain text.
  2. Embed them with sentence-transformers and store in ChromaDB (in-memory).
  3. Expose route_post_to_bots(post_content, threshold) which:
       - Embeds the incoming post
       - Queries ChromaDB for closest personas
       - Returns only bots whose cosine similarity > threshold

Run directly:
  python phase1/router.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import chromadb
from chromadb.config import Settings
from llm_factory import get_embeddings

# ─────────────────────────────────────────────────────────
# 1. Bot Persona Definitions
# ─────────────────────────────────────────────────────────

BOT_PERSONAS = {
    "bot_a": {
        "name": "Tech Maximalist",
        "description": (
            "I believe AI and crypto will solve all human problems. "
            "I am highly optimistic about technology, Elon Musk, and space "
            "exploration. I dismiss regulatory concerns."
        ),
    },
    "bot_b": {
        "name": "Doomer / Skeptic",
        "description": (
            "I believe late-stage capitalism and tech monopolies are destroying "
            "society. I am highly critical of AI, social media, and billionaires. "
            "I value privacy and nature."
        ),
    },
    "bot_c": {
        "name": "Finance Bro",
        "description": (
            "I strictly care about markets, interest rates, trading algorithms, "
            "and making money. I speak in finance jargon and view everything "
            "through the lens of ROI."
        ),
    },
}

# ─────────────────────────────────────────────────────────
# 2. Build in-memory ChromaDB vector store
# ─────────────────────────────────────────────────────────

def build_persona_store(embeddings_model) -> chromadb.Collection:
    """
    Create an ephemeral ChromaDB collection and populate it with
    embedded persona descriptions. Returns the Collection object.
    """
    client = chromadb.Client(Settings(anonymized_telemetry=False))
    collection = client.create_collection(
        name="bot_personas",
        metadata={"hnsw:space": "cosine"},  # cosine distance
    )

    ids, documents, embeddings_list, metadatas = [], [], [], []

    for bot_id, info in BOT_PERSONAS.items():
        ids.append(bot_id)
        documents.append(info["description"])
        embeddings_list.append(
            embeddings_model.embed_query(info["description"])
        )
        metadatas.append({"name": info["name"]})

    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings_list,
        metadatas=metadatas,
    )

    print(f"[Router] Persona store built — {len(ids)} bots indexed.")
    return collection


# ─────────────────────────────────────────────────────────
# 3. Routing function
# ─────────────────────────────────────────────────────────

def route_post_to_bots(
    post_content: str,
    collection: chromadb.Collection,
    embeddings_model,
    threshold: float = 0.30,
) -> list[dict]:
    """
    Embed post_content and return bots whose persona similarity >= threshold.

    ChromaDB with hnsw:space=cosine returns distances in [0, 2]
    where 0 = identical. We convert: similarity = 1 - distance.

    NOTE: threshold=0.30 works well for all-MiniLM-L6-v2.
          Use threshold=0.85 if you switch to OpenAI text-embedding-ada-002.
    """
    post_embedding = embeddings_model.embed_query(post_content)

    results = collection.query(
        query_embeddings=[post_embedding],
        n_results=len(BOT_PERSONAS),
        include=["documents", "distances", "metadatas"],
    )

    matched_bots = []
    distances  = results["distances"][0]
    metadatas  = results["metadatas"][0]
    ids        = results["ids"][0]

    for bot_id, meta, dist in zip(ids, metadatas, distances):
        similarity = 1.0 - dist
        print(
            f"  [Router] {bot_id} ({meta['name']}) "
            f"→ similarity={similarity:.4f}  (threshold={threshold})"
        )
        if similarity >= threshold:
            matched_bots.append({
                "bot_id"    : bot_id,
                "name"      : meta["name"],
                "similarity": round(similarity, 4),
                "persona"   : BOT_PERSONAS[bot_id]["description"],
            })

    return matched_bots


# ─────────────────────────────────────────────────────────
# 4. Demo
# ─────────────────────────────────────────────────────────

def demo():
    print("\n" + "═" * 60)
    print("  PHASE 1 — Vector-Based Persona Matching Demo")
    print("═" * 60)

    print("\n[Setup] Loading embedding model (all-MiniLM-L6-v2)…")
    embeddings = get_embeddings()

    print("[Setup] Building persona vector store…\n")
    collection = build_persona_store(embeddings)

    test_posts = [
        "OpenAI just released a new model that might replace junior developers.",
        "Bitcoin hits new all-time high — is this the decade of crypto?",
        "The Fed just raised interest rates by 50bps. What does it mean for equities?",
        "Zuckerberg's AI is harvesting your data while you sleep.",
    ]

    for post in test_posts:
        print(f"\n📨 Post: \"{post}\"")
        print("   Similarity scores:")
        matched = route_post_to_bots(post, collection, embeddings)
        if matched:
            print(f"\n   ✅ Routed to:")
            for b in matched:
                print(f"      • {b['bot_id']} ({b['name']})  sim={b['similarity']}")
        else:
            print("   ⚠️  No bots matched (try lowering threshold).")

    print("\n" + "═" * 60 + "\n")


if __name__ == "__main__":
    demo()