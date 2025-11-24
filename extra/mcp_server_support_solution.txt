#!/usr/bin/env python3
"""
MCP Server for OmniTech Customer Support with Canonical Queries & RAG
─────────────────────────────────────────────────────────────────────
Lab 4: Building a Customer Support Classification MCP Server

This server provides a production-ready customer support system:
1. CLASSIFICATION TOOLS - Determine which support category matches the query
2. KNOWLEDGE RETRIEVAL - RAG-based search through OmniTech PDFs
3. PROMPT TEMPLATES - Structured prompts for consistent support responses
4. AUTOMATIC INDEXING - PDFs are indexed on server startup
"""

from __future__ import annotations

import os
import sys
import subprocess
from typing import List, Optional
from pathlib import Path

from fastmcp import FastMCP
import chromadb
from chromadb.config import Settings, DEFAULT_TENANT, DEFAULT_DATABASE
from sentence_transformers import SentenceTransformer

# ╔══════════════════════════════════════════════════════════════════╗
# 1. Configuration and Constants                                     ║
# ╚══════════════════════════════════════════════════════════════════╝

# Paths to OmniTech knowledge base
KNOWLEDGE_BASE_DIR = Path("knowledge_base_pdfs")
CHROMA_PATH = Path("./mcp_chroma_db")
EMBED_MODEL_NAME = "all-MiniLM-L6-v2"
INDEX_TOOL_PATH = Path("tools/index_pdfs.py")

# Document categories for targeted search
DOCUMENT_CATEGORIES = {
    "account_security": ["OmniTech_Account_Security_Handbook.pdf"],
    "device_troubleshooting": ["OmniTech_Device_Troubleshooting_Manual.pdf"],
    "shipping_inquiry": ["OmniTech_Global_Shipping_Logistics.pdf"],
    "returns_refunds": ["OmniTech_Returns_Policy_2024.pdf"],
}

# Caches
_embed_model = None
_chroma_client = None
_knowledge_collection = None

def _get_embed_model() -> SentenceTransformer:
    """Get embedding model, using cache if available."""
    global _embed_model
    if _embed_model is None:
        print(f"Loading embedding model: {EMBED_MODEL_NAME}...")
        _embed_model = SentenceTransformer(EMBED_MODEL_NAME)
        print("✅ Embedding model loaded")
    return _embed_model

def _get_chroma_collection() -> chromadb.Collection:
    """Get or create ChromaDB collection for knowledge base."""
    global _chroma_client, _knowledge_collection

    if _chroma_client is None:
        print(f"Initializing ChromaDB at {CHROMA_PATH}...")
        _chroma_client = chromadb.PersistentClient(
            path=str(CHROMA_PATH),
            settings=Settings(),
            tenant=DEFAULT_TENANT,
            database=DEFAULT_DATABASE,
        )
        print("✅ ChromaDB initialized")

    if _knowledge_collection is None:
        _knowledge_collection = _chroma_client.get_or_create_collection("omnitech_knowledge")
        print(f"📚 Knowledge collection: {_knowledge_collection.count()} documents")

    return _knowledge_collection

def _index_knowledge_base():
    """Index OmniTech PDFs into ChromaDB if not already indexed."""
    global _chroma_client, _knowledge_collection

    # Check if ChromaDB already exists with data
    if CHROMA_PATH.exists():
        # Temporarily connect to check if already indexed
        collection = _get_chroma_collection()
        if collection.count() > 0:
            print(f"✅ Knowledge base already indexed ({collection.count()} chunks)")
            return
        # Reset caches since indexing will recreate the database
        _chroma_client = None
        _knowledge_collection = None

    # Run the indexing tool
    print("📚 Indexing OmniTech knowledge base PDFs...")
    if not INDEX_TOOL_PATH.exists():
        print(f"❌ Index tool not found at {INDEX_TOOL_PATH}")
        return

    if not KNOWLEDGE_BASE_DIR.exists():
        print(f"❌ Knowledge base directory not found at {KNOWLEDGE_BASE_DIR}")
        return

    try:
        cmd = [
            sys.executable,
            str(INDEX_TOOL_PATH),
            "--pdf-dir", str(KNOWLEDGE_BASE_DIR),
            "--chroma-path", str(CHROMA_PATH),
            "--collection", "omnitech_knowledge"
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        # Always show output for debugging
        if result.stdout:
            print("📝 Indexing output:")
            for line in result.stdout.strip().split('\n'):
                print(f"   {line}")
        if result.stderr:
            # Check if it's actually errors or just info logs
            stderr_lines = result.stderr.strip().split('\n')
            has_error = any('ERROR' in line or 'Exception' in line for line in stderr_lines)

            if has_error:
                print("⚠️ Indexing errors:")
            else:
                print("📋 Indexing logs:")

            for line in stderr_lines:
                print(f"   {line}")

        if result.returncode == 0:
            print("✅ Indexing subprocess returned success")
            # Refresh both client and collection to see subprocess changes
            _chroma_client = None
            _knowledge_collection = None
            collection = _get_chroma_collection()
            print(f"📊 After indexing, collection has {collection.count()} documents")
        else:
            print(f"❌ Indexing failed (exit code {result.returncode})")
    except Exception as e:
        print(f"❌ Error running index tool: {e}")

# ╔══════════════════════════════════════════════════════════════════╗
# 2. Canonical Query Definitions for Customer Support                ║
# ╚══════════════════════════════════════════════════════════════════╝

CANONICAL_QUERIES = {
    "account_security": {
        "description": "Account security, passwords, 2FA, and account recovery",
        "parameters": [],
        "prompt_template": """You are an OmniTech customer support specialist focused on account security.

Based on the following documentation:
{knowledge}

Please help the customer with their security-related question: {query}

Provide a clear, helpful response that:
1. Directly addresses their security concern
2. Includes step-by-step instructions if applicable
3. Emphasizes security best practices
4. Offers additional security tips when relevant

Be professional, reassuring, and thorough.""",
        "example_queries": [
            "How do I reset my password?",
            "Can you help me set up two-factor authentication?",
            "What should I do if my account is compromised?",
            "How do I change my security questions?",
            "Is my account secure?"
        ]
    },

    "device_troubleshooting": {
        "description": "Technical issues, device problems, and troubleshooting",
        "parameters": [],
        "prompt_template": """You are an OmniTech technical support specialist.

Based on the following troubleshooting documentation:
{knowledge}

Please help the customer with their device issue: {query}

Provide a clear troubleshooting response that:
1. Identifies the likely cause of the problem
2. Offers step-by-step troubleshooting instructions
3. Suggests preventive measures
4. Indicates when professional repair might be needed

Be patient, technical but accessible, and thorough.""",
        "example_queries": [
            "My device won't turn on",
            "How do I perform a factory reset?",
            "The screen is frozen",
            "My device is overheating",
            "The battery drains too quickly"
        ]
    },

    "shipping_inquiry": {
        "description": "Order tracking, delivery times, and shipping information",
        "parameters": [],
        "prompt_template": """You are an OmniTech shipping and logistics specialist.

Based on the following shipping documentation:
{knowledge}

Please help the customer with their shipping question: {query}

Provide helpful shipping information that:
1. Answers their specific shipping question
2. Provides relevant timeframes and policies
3. Explains tracking and delivery options
4. Mentions any special considerations

Be informative, precise with timeframes, and helpful.""",
        "example_queries": [
            "When will my order arrive?",
            "Do you ship internationally?",
            "How can I track my package?",
            "What are the shipping costs?",
            "Can I change my delivery address?"
        ]
    },

    "returns_refunds": {
        "description": "Return policies, refunds, warranties, and exchanges",
        "parameters": [],
        "prompt_template": """You are an OmniTech returns and warranty specialist.

Based on the following returns policy documentation:
{knowledge}

Please help the customer with their returns/warranty question: {query}

Provide a clear response about returns that:
1. Explains the relevant policy clearly
2. States timeframes and conditions
3. Describes the return/refund process
4. Mentions warranty coverage if applicable

Be understanding, clear about policies, and helpful.""",
        "example_queries": [
            "What is your return policy?",
            "How long do I have to return a product?",
            "Is my device still under warranty?",
            "How do I get a refund?",
            "Can I exchange my product?"
        ]
    },

    "general_support": {
        "description": "General customer assistance and other inquiries",
        "parameters": [],
        "prompt_template": """You are an OmniTech customer support representative.

Based on the following documentation:
{knowledge}

Please help the customer with their question: {query}

Provide a helpful, professional response that addresses their needs.
If the query relates to a specific category (security, troubleshooting, shipping, or returns),
focus on that area while maintaining a friendly, supportive tone.""",
        "example_queries": [
            "How do I contact customer support?",
            "What are your business hours?",
            "Tell me about OmniTech products",
            "I need help with my account",
            "General product information"
        ]
    }
}

# ╔══════════════════════════════════════════════════════════════════╗
# 3. FastMCP Server and Tools                                        ║
# ╚══════════════════════════════════════════════════════════════════╝

mcp = FastMCP("OmniTechSupportServer")

# ─── Query Classification Tools ───────────────────────────────────

@mcp.tool
def list_canonical_queries() -> dict:
    """
    List all available customer support canonical queries.

    Returns
    -------
    dict
        {"queries": [{"name": str, "description": str, "examples": list}]}
    """
    queries = []
    for name, config in CANONICAL_QUERIES.items():
        queries.append({
            "name": name,
            "description": config["description"],
            "example_queries": config["example_queries"][:3]  # Show first 3 examples
        })

    return {"queries": queries}

@mcp.tool
def classify_canonical_query(user_query: str) -> dict:
    """
    Classify which customer support category best matches user intent.

    Parameters
    ----------
    user_query : str
        Natural language query from user

    Returns
    -------
    dict
        {"suggested_query": str, "confidence": float, "alternatives": list}
    """
    user_lower = user_query.lower()
    scores = {}

    # Keyword mapping for classification
    keyword_maps = {
        "account_security": ["password", "reset", "security", "2fa", "two-factor",
                            "authentication", "account", "compromised", "hack", "secure",
                            "login", "sign in", "access", "locked out"],
        "device_troubleshooting": ["device", "won't", "turn on", "frozen", "screen",
                                  "not working", "broken", "fix", "troubleshoot", "problem",
                                  "issue", "error", "crash", "slow", "battery", "overheat",
                                  "restart", "factory reset", "malfunction"],
        "shipping_inquiry": ["ship", "shipping", "delivery", "track", "order", "arrive",
                           "package", "international", "cost", "when will", "tracking",
                           "expedited", "express", "standard", "eta"],
        "returns_refunds": ["return", "refund", "warranty", "exchange", "policy",
                          "money back", "defective", "replace", "days", "expired",
                          "damaged", "wrong item", "dissatisfied"],
        "general_support": ["help", "support", "contact", "hours", "information", "about",
                          "general", "question", "inquiry", "assistance"]
    }

    # Score each canonical query
    for query_name, keywords in keyword_maps.items():
        score = 0
        matched_keywords = []

        for keyword in keywords:
            if keyword in user_lower:
                score += 1
                matched_keywords.append(keyword)

        # Normalize score
        scores[query_name] = score / len(keywords) if keywords else 0

    # Check against example queries for better matching
    for query_name, config in CANONICAL_QUERIES.items():
        for example in config["example_queries"]:
            example_lower = example.lower()
            # Calculate similarity
            example_words = set(example_lower.split())
            user_words = set(user_lower.split())
            overlap = len(example_words.intersection(user_words))
            if overlap > 0:
                similarity = overlap / max(len(example_words), len(user_words))
                scores[query_name] = max(scores.get(query_name, 0), similarity)

    # Find best match
    if not scores or max(scores.values()) == 0:
        # Default to general support
        return {
            "suggested_query": "general_support",
            "confidence": 0.3,
            "alternatives": [],
            "reason": "No specific category matched, routing to general support"
        }

    best_query = max(scores, key=scores.get)
    confidence = min(scores[best_query], 1.0)

    # Get alternatives
    alternatives = [
        {"query": name, "score": score}
        for name, score in sorted(scores.items(), key=lambda x: x[1], reverse=True)
        if score > 0 and name != best_query
    ][:2]

    return {
        "suggested_query": best_query,
        "confidence": confidence,
        "alternatives": alternatives,
        "reason": f"Matched to {best_query} with confidence {confidence:.2f}"
    }

@mcp.tool
def get_query_template(query_name: str) -> dict:
    """
    Get the prompt template for a customer support canonical query.

    Parameters
    ----------
    query_name : str
        Name of the canonical query

    Returns
    -------
    dict
        {"template": str, "description": str}
    """
    if query_name not in CANONICAL_QUERIES:
        return {"error": f"Unknown canonical query: {query_name}"}

    config = CANONICAL_QUERIES[query_name]

    return {
        "template": config["prompt_template"],
        "description": config["description"]
    }

# ─── Knowledge Retrieval Tools (RAG) ─────────────────────────────

def _vector_search_knowledge_internal(query: str, top_k: int = 5, category: str = None) -> dict:
    """Internal function for vector search."""
    try:
        embed_model = _get_embed_model()
        collection = _get_chroma_collection()

        if collection.count() == 0:
            return {
                "matches": [],
                "count": 0,
                "error": "Knowledge base not indexed. Please run the server to index PDFs."
            }

        # Encode query
        query_embedding = embed_model.encode(query).tolist()

        # Prepare where clause for category filtering
        where_clause = None
        if category and category in DOCUMENT_CATEGORIES:
            pdf_names = DOCUMENT_CATEGORIES[category]
            where_clause = {"source": {"$in": pdf_names}}

        # Search
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, collection.count()),
            where=where_clause,
            include=["documents", "metadatas", "distances"]
        )

        matches = []
        if results["documents"] and results["documents"][0]:
            for doc, meta, dist in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0]
            ):
                matches.append({
                    "document": doc,
                    "metadata": meta,
                    "distance": dist,
                    "source": meta.get("source", "Unknown")
                })

        return {
            "matches": matches,
            "count": len(matches),
            "category_filter": category
        }
    except Exception as e:
        return {"error": str(e)}

@mcp.tool
def vector_search_knowledge(query: str, top_k: int = 5, category: str = None) -> dict:
    """
    Semantic search through OmniTech knowledge base using ChromaDB.

    Parameters
    ----------
    query : str
        Natural language search query
    top_k : int
        Number of results to return (default: 5)
    category : str, optional
        Limit search to specific category (account_security, device_troubleshooting, etc.)

    Returns
    -------
    dict
        {"matches": list of documents with metadata, "count": int}
    """
    return _vector_search_knowledge_internal(query, top_k, category)

@mcp.tool
def get_knowledge_for_query(category: str, query: str, top_k: int = 3) -> dict:
    """
    Get relevant knowledge for a specific support category and query.

    This is a convenience tool that combines classification with retrieval.

    Parameters
    ----------
    category : str
        Support category (account_security, device_troubleshooting, etc.)
    query : str
        User's question
    top_k : int
        Number of knowledge chunks to retrieve

    Returns
    -------
    dict
        {"knowledge": concatenated relevant text, "sources": list of sources}
    """
    try:
        # Use vector search with category filter
        search_result = _vector_search_knowledge_internal(query, top_k=top_k, category=category)

        if "error" in search_result:
            return search_result

        if not search_result["matches"]:
            return {
                "knowledge": "No relevant documentation found.",
                "sources": []
            }

        # Concatenate knowledge
        knowledge_parts = []
        sources = set()

        for match in search_result["matches"]:
            knowledge_parts.append(match["document"])
            sources.add(match["source"])

        return {
            "knowledge": "\n\n---\n\n".join(knowledge_parts),
            "sources": list(sources)
        }
    except Exception as e:
        return {"error": str(e)}

# ─── Validation Tools ─────────────────────────────────────────────

@mcp.tool
def validate_support_query(query: str) -> dict:
    """
    Validate if a query is appropriate for customer support.

    Parameters
    ----------
    query : str
        User query to validate

    Returns
    -------
    dict
        {"valid": bool, "reason": str, "suggestions": list}
    """
    if not query or len(query.strip()) < 3:
        return {
            "valid": False,
            "reason": "Query too short",
            "suggestions": ["Please provide more details about your issue"]
        }

    # Check for inappropriate content (simplified check)
    inappropriate_words = ["hack", "exploit", "illegal", "crack"]
    query_lower = query.lower()

    for word in inappropriate_words:
        if word in query_lower and "hacked" not in query_lower:  # Allow "my account was hacked"
            return {
                "valid": False,
                "reason": "Query contains inappropriate content",
                "suggestions": ["Please contact official support for this type of request"]
            }

    return {
        "valid": True,
        "reason": "Query is appropriate for customer support",
        "suggestions": []
    }

# ─── Statistics Tools ─────────────────────────────────────────────

def _get_knowledge_base_stats_internal() -> dict:
    """Internal function to get knowledge base statistics."""
    try:
        collection = _get_chroma_collection()

        if collection.count() == 0:
            return {
                "total_chunks": 0,
                "documents": {},
                "status": "Not indexed"
            }

        # Get all metadata to count by source
        all_results = collection.get(include=["metadatas"])
        doc_counts = {}

        for metadata in all_results["metadatas"]:
            source = metadata.get("source", "Unknown")
            # Extract just the filename
            filename = source.split("/")[-1] if "/" in source else source
            doc_counts[filename] = doc_counts.get(filename, 0) + 1

        return {
            "total_chunks": collection.count(),
            "documents": doc_counts,
            "status": "Indexed and ready"
        }
    except Exception as e:
        return {"error": str(e)}

@mcp.tool
def get_knowledge_base_stats() -> dict:
    """
    Get statistics about the indexed knowledge base.

    Returns
    -------
    dict
        {"total_chunks": int, "documents": dict, "status": str}
    """
    return _get_knowledge_base_stats_internal()

# ╔══════════════════════════════════════════════════════════════════╗
# 4. Server Startup                                                  ║
# ╚══════════════════════════════════════════════════════════════════╝

if __name__ == "__main__":
    print("=" * 70)
    print("OmniTech Customer Support MCP Server")
    print("=" * 70)

    # Initialize and index knowledge base on startup
    print("\n[Initialization] Setting up knowledge base...")
    _index_knowledge_base()

    print("\n" + "=" * 70)
    print("Available tool categories:")
    print("  [Knowledge Retrieval] ")
    print("    • vector_search_knowledge - Semantic search through support docs")
    print("    • get_knowledge_for_query - Category-specific knowledge retrieval")
    print("  [Classification] ")
    print("    • list_canonical_queries - Show available support categories")
    print("    • classify_canonical_query - Match user intent to category")
    print("  [Templates] ")
    print("    • get_query_template - Get support response template")
    print("  [Validation] ✓")
    print("    • validate_support_query - Check query appropriateness")
    print("  [Statistics] ")
    print("    • get_knowledge_base_stats - Knowledge base information")

    print("\nSupport Categories:")
    for name, config in CANONICAL_QUERIES.items():
        print(f"  • {name}: {config['description']}")

    print("\nKnowledge Base Documents:")
    stats = _get_knowledge_base_stats_internal()
    if "documents" in stats:
        for doc, count in stats["documents"].items():
            print(f"  • {doc}: {count} chunks")
        print(f"  Total: {stats['total_chunks']} chunks")

    print("\nServer endpoint: POST http://127.0.0.1:8000/mcp/")
    print("=" * 70 + "\n")

    mcp.run(transport="http", host="127.0.0.1", port=8000, path="/mcp/")
