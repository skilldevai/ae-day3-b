#!/usr/bin/env python3
"""
OmniTech Customer Support RAG Agent with MCP Classification
────────────────────────────────────────────────────────────

This agent uses the MCP server for ALL knowledge access (centralized knowledge layer):

CUSTOMER SUPPORT WORKFLOW (for classified queries):
1. CLASSIFICATION: Ask MCP server to classify the support category
2. TEMPLATE: Get the appropriate prompt template from MCP
3. KNOWLEDGE: Retrieve relevant documentation from OmniTech PDFs via MCP
4. EXECUTION: Run LLM locally with template + knowledge

EXPLORATORY SEARCH WORKFLOW (for general questions):
1. RAG SEARCH: Use MCP server's vector_search_knowledge for semantic search
2. SYNTHESIS: Generate response from retrieved documentation

ARCHITECTURE:
• MCP Server = Knowledge Layer (owns vector DB, PDFs, embeddings)
• RAG Agent = Orchestration Layer (routing, LLM execution, workflow)
• All knowledge access goes through MCP tools (no direct file reading)

KNOWLEDGE SOURCES (all accessed via MCP):
• OmniTech_Account_Security_Handbook.pdf
• OmniTech_Device_Troubleshooting_Manual.pdf
• OmniTech_Global_Shipping_Logistics.pdf
• OmniTech_Returns_Policy_2024.pdf
"""

import asyncio
import json
import os
import re
from typing import Optional

from fastmcp import Client
from fastmcp.exceptions import ToolError
from langchain_ollama import ChatOllama

# ╔══════════════════════════════════════════════════════════════════╗
# 1. Configuration                                                   ║
# ╚══════════════════════════════════════════════════════════════════╝
MCP_ENDPOINT = "http://127.0.0.1:8000/mcp/"
TOP_K        = 3
MODEL        = os.getenv("OLLAMA_MODEL", "llama3.2")

# Support category keywords for quick routing
SUPPORT_KEYWORDS = {
    "password": ["password", "reset", "forgot", "login", "access"],
    "security": ["2fa", "two-factor", "authentication", "hacked", "compromised", "secure"],
    "device": ["device", "won't turn", "frozen", "screen", "factory reset", "broken"],
    "shipping": ["ship", "delivery", "track", "order", "arrive", "package"],
    "return": ["return", "refund", "warranty", "exchange", "money back"],
    "exploratory": ["product", "company", "omnitech", "tell me about", "what is"]
}

# ╔══════════════════════════════════════════════════════════════════╗
# 2. Helper Functions                                                ║
# ╚══════════════════════════════════════════════════════════════════╝
def unwrap(obj):
    """Unwrap FastMCP result objects."""
    if hasattr(obj, "structured_content") and obj.structured_content:
        return unwrap(obj.structured_content)
    if hasattr(obj, "data") and obj.data:
        return unwrap(obj.data)
    if isinstance(obj, list) and len(obj) == 1:
        return unwrap(obj[0])
    return obj

def is_support_query(query: str) -> bool:
    """Determine if this is a customer support query vs exploratory."""
    query_lower = query.lower()

    # Check for support-related keywords
    for category, keywords in SUPPORT_KEYWORDS.items():
        if category == "exploratory":
            continue
        for keyword in keywords:
            if keyword in query_lower:
                return True

    # Check for question patterns that indicate support need
    support_patterns = [
        r"how do i",
        r"how can i",
        r"what should i",
        r"can you help",
        r"i need help",
        r"my \w+ (is|isn't|won't)",
        r"problem with",
        r"issue with"
    ]

    for pattern in support_patterns:
        if re.search(pattern, query_lower):
            return True

    return False

# ╔══════════════════════════════════════════════════════════════════╗
# 3. Customer Support Classification Workflow                        ║
# ╚══════════════════════════════════════════════════════════════════╝
async def handle_canonical_query_with_classification(user_query: str) -> str:
    """
    Handle customer support queries using the 4-step classification workflow.
    """
    async with Client(MCP_ENDPOINT) as mcp:
        try:
            print("[1/4] Classifying support query...")
            classify_result = await mcp.call_tool("classify_canonical_query", {
                "user_query": user_query
            })
            classification = unwrap(classify_result)

            if not isinstance(classification, dict):
                return f"Classification error: Expected dict, got {type(classification)}"

            suggested_category = classification.get("suggested_query")
            confidence = classification.get("confidence", 0)

            if not suggested_category:
                return "I couldn't determine the type of support you need. Please try rephrasing your question."

            print(f"[Result] Category: {suggested_category} (confidence: {confidence:.2f})")

            # Step 2: Get the prompt template for this category
            print("[2/4] Getting support template...")
            template_result = await mcp.call_tool("get_query_template", {
                "query_name": suggested_category
            })
            template_info = unwrap(template_result)

            if "error" in template_info:
                return f"Template error: {template_info['error']}"

            template = template_info.get("template", "")
            description = template_info.get("description", "")

            # Step 3: Retrieve relevant knowledge
            print(f"[3/4] Retrieving knowledge for {suggested_category}...")
            knowledge_result = await mcp.call_tool("get_knowledge_for_query", {
                "category": suggested_category,
                "query": user_query,
                "top_k": TOP_K
            })
            knowledge_info = unwrap(knowledge_result)

            if "error" in knowledge_info:
                return f"Knowledge retrieval error: {knowledge_info['error']}"

            knowledge = knowledge_info.get("knowledge", "")
            sources = knowledge_info.get("sources", [])

            if not knowledge or knowledge == "No relevant documentation found.":
                print("⚠️ No specific documentation found, using general template")
                knowledge = f"General support information for {description}"

            print(f"📚 Retrieved {len(sources)} source(s)")

            # Step 4: Execute LLM with template + knowledge
            print("[4/4] Generating response with LLM...")

            # Format the prompt with knowledge
            formatted_prompt = template.format(
                query=user_query,
                knowledge=knowledge
            )

            try:
                llm = ChatOllama(model=MODEL, temperature=0.3)

                system_msg = (
                    "You are an OmniTech customer support specialist. "
                    "Provide helpful, accurate, and friendly assistance based on the company documentation provided. "
                    "Be concise but thorough. If the documentation doesn't contain the answer, "
                    "politely suggest contacting support directly."
                )

                response = llm.invoke([
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": formatted_prompt}
                ])

                result = response.content.strip()

                # Add source attribution if available
                if sources:
                    result += "\n\n---\n*Sources: " + ", ".join(set(sources)) + "*"

                print(f"✅ Response generated ({len(result)} chars)")
                return result

            except Exception as llm_error:
                print(f"⚠️ LLM error: {llm_error}")
                # Fallback response
                fallback = f"**Support Category: {suggested_category.replace('_', ' ').title()}**\n\n"
                fallback += f"{description}\n\n"
                if knowledge and knowledge != "No relevant documentation found.":
                    fallback += "**Relevant Information:**\n"
                    fallback += knowledge[:500] + "..." if len(knowledge) > 500 else knowledge
                else:
                    fallback += "Please contact our support team for assistance with your specific issue."
                return fallback

        except ToolError as e:
            return f"MCP error: {e}"
        except Exception as e:
            return f"Unexpected error: {e}"

# ╔══════════════════════════════════════════════════════════════════╗
# 4. Direct RAG Search Workflow                                      ║
# ╚══════════════════════════════════════════════════════════════════╝
async def handle_rag_search(user_query: str) -> str:
    """
    Handle exploratory queries using direct semantic search across all documentation.
    """
    async with Client(MCP_ENDPOINT) as mcp:
        try:
            print(f"[RAG] Searching knowledge base for: '{user_query}'")

            # Perform vector search across all documentation
            search_result = await mcp.call_tool("vector_search_knowledge", {
                "query": user_query,
                "top_k": TOP_K * 2  # Get more results for exploratory queries
            })
            search_data = unwrap(search_result)

            if "error" in search_data:
                return f"Search error: {search_data['error']}"

            matches = search_data.get("matches", [])
            if not matches:
                return (
                    "I couldn't find relevant information about that in our documentation. "
                    "Please try rephrasing your question or contact our support team."
                )

            print(f"📚 Found {len(matches)} relevant documents")

            # Compile knowledge from matches
            knowledge_parts = []
            sources = set()
            for match in matches[:TOP_K]:  # Use top results
                knowledge_parts.append(match["document"])
                if "metadata" in match and "source" in match["metadata"]:
                    sources.add(match["metadata"]["source"])

            combined_knowledge = "\n\n---\n\n".join(knowledge_parts)

            # Generate response using LLM
            try:
                llm = ChatOllama(model=MODEL, temperature=0.3)

                system_msg = (
                    "You are an OmniTech information assistant. "
                    "Answer the user's question based on the provided documentation. "
                    "Be informative and helpful. If the documentation doesn't fully answer the question, "
                    "acknowledge what you found and suggest where they might find more information."
                )

                user_msg = (
                    f"User Question: {user_query}\n\n"
                    f"Relevant Documentation:\n{combined_knowledge}\n\n"
                    "Please provide a helpful answer based on this documentation."
                )

                response = llm.invoke([
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg}
                ])

                result = response.content.strip()

                # Add sources
                if sources:
                    source_list = [s.split('/')[-1] if '/' in s else s for s in sources]
                    result += f"\n\n---\n*Sources: {', '.join(source_list)}*"

                return result

            except Exception as llm_error:
                print(f"⚠️ LLM unavailable: {llm_error}")
                # Fallback: Return the raw knowledge
                fallback = "**Relevant Information Found:**\n\n"
                for i, part in enumerate(knowledge_parts[:3], 1):
                    fallback += f"{i}. {part[:200]}...\n\n"
                if sources:
                    fallback += f"\n*Sources: {', '.join(sources)}*"
                return fallback

        except Exception as e:
            return f"Search error: {e}"

# ╔══════════════════════════════════════════════════════════════════╗
# 5. Main Query Router                                               ║
# ╚══════════════════════════════════════════════════════════════════╝
async def process_query(user_query: str) -> str:
    """
    Route queries to appropriate workflow based on intent.
    """
    # Determine if this is a support query or exploratory
    if is_support_query(user_query):
        print("[INFO] Detected customer support query - using classification workflow")
        return await handle_canonical_query_with_classification(user_query)
    else:
        print("[INFO] Detected exploratory query - using RAG search")
        return await handle_rag_search(user_query)

# ╔══════════════════════════════════════════════════════════════════╗
# 6. Command-line Interface                                          ║
# ╚══════════════════════════════════════════════════════════════════╝
async def demo_support_queries():
    """Demonstrate the classification workflow with sample support queries."""
    print("\nCustomer Support Demo")
    print("=" * 50)

    sample_queries = [
        "How do I reset my password?",
        "My device won't turn on, what should I do?",
        "When will my order arrive?",
        "What is your return policy?",
        "Can you tell me about OmniTech products?",
    ]

    for query in sample_queries:
        print(f"\nUser: {query}")
        print("-" * 40)
        result = await process_query(query)
        print(f"Agent: {result}")
        print()

if __name__ == "__main__":
    print("=" * 70)
    print("OmniTech Customer Support RAG Agent")
    print("=" * 70)
    print("\nArchitecture:")
    print("  🔹 MCP Server = Knowledge Layer")
    print("     - Owns OmniTech PDF documentation")
    print("     - Manages vector database (ChromaDB)")
    print("     - Provides classification & search tools")
    print("  🔹 RAG Agent = Orchestration Layer")
    print("     - Routes to support or exploratory workflows")
    print("     - Executes LLM with retrieved knowledge")
    print("     - NO local file reading or embeddings")
    print("\nKnowledge Base:")
    print("  • Account Security Handbook")
    print("  • Device Troubleshooting Manual")
    print("  • Global Shipping Logistics")
    print("  • Returns Policy 2024")
    print("\nPrerequisites:")
    print("  ⚠️  MCP classification server MUST be running first!")
    print("     Run: python mcp_server_classification.py")
    print("\nCommands:")
    print("  • Type 'exit' to quit")
    print("  • Type 'demo' for sample queries")
    print("\nExample Support Queries:")
    print("  🔐 Security: 'How do I reset my password?'")
    print("  🔧 Device: 'My device won't turn on'")
    print("  📦 Shipping: 'Track my order'")
    print("  ↩️  Returns: 'What is your return policy?'")
    print("  🔍 General: 'Tell me about OmniTech'")
    print("=" * 70)
    print()

    while True:
        user_input = input("Query: ").strip()
        if user_input.lower() == "exit":
            break
        elif user_input.lower() == "demo":
            asyncio.run(demo_support_queries())
        elif user_input:
            result = asyncio.run(process_query(user_input))
            print(f"\n{result}\n")
