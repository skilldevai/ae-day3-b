#!/usr/bin/env python3
"""
────────────────────────────────────────────────────────────

This agent uses the MCP server for ALL knowledge access (centralized knowledge layer):

CUSTOMER SUPPORT WORKFLOW (for classified queries):

EXPLORATORY SEARCH WORKFLOW (for general questions):

ARCHITECTURE:

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

# ANSI color codes for terminal output
BLUE = "\033[34m"      # Dark blue for LLM responses
CYAN = "\033[36m"      # Cyan for sources
GREEN = "\033[32m"     # Green for "Agent:" label
RESET = "\033[0m"      # Reset to default color

# Support category keywords for quick routing
SUPPORT_KEYWORDS = {
}

# ╔══════════════════════════════════════════════════════════════════╗
# 2. Helper Functions                                                ║
# ╚══════════════════════════════════════════════════════════════════╝
async def check_server_running() -> bool:
    """Check if the MCP classification server is running."""
    try:
        # Try to actually connect to the MCP server
        async with Client(MCP_ENDPOINT) as mcp:
            # Try to list available tools - if this works, server is running
            await mcp.list_tools()
            return True
    except Exception:
        return False

def unwrap(obj):
    """Unwrap FastMCP result objects."""
    if hasattr(obj, "structured_content") and obj.structured_content:
        return unwrap(obj.structured_content)
    if hasattr(obj, "data") and obj.data:
        return unwrap(obj.data)
    if isinstance(obj, list) and len(obj) == 1:
        return unwrap(obj[0])
    return obj

def format_response(response: str) -> str:
    """Format response with colors - blue for content, cyan for sources."""
    # Split on the sources divider
    if "\n---\n*Sources:" in response:
        parts = response.split("\n---\n*Sources:")
        content = parts[0]
        sources = "*Sources:" + parts[1]
        return f"{BLUE}{content}{RESET}\n---\n{CYAN}{sources}{RESET}"
    else:
        # No sources, just color the whole response
        return f"{BLUE}{response}{RESET}"

def is_support_query(query: str) -> bool:
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
            classification = unwrap(classify_result)

            if not isinstance(classification, dict):
                return f"Classification error: Expected dict, got {type(classification)}"

            confidence = classification.get("confidence", 0)

            if not suggested_category:
                return "I couldn't determine the type of support you need. Please try rephrasing your question."

            print(f"[Result] Category: {suggested_category} (confidence: {confidence:.2f})")

            # Step 2: Get the prompt template for this category
            template_info = unwrap(template_result)

            if "error" in template_info:
                return f"Template error: {template_info['error']}"

            template = template_info.get("template", "")
            description = template_info.get("description", "")

            # Step 3: Retrieve relevant knowledge
            knowledge_info = unwrap(knowledge_result)

            if "error" in knowledge_info:
                return f"Knowledge retrieval error: {knowledge_info['error']}"

            knowledge = knowledge_info.get("knowledge", "")
            sources = knowledge_info.get("sources", [])

            if not knowledge or knowledge == "No relevant documentation found.":
                print("[WARNING] No specific documentation found, using general template")
                knowledge = f"General support information for {description}"

            print(f"[INFO] Retrieved {len(sources)} source(s)")

            # Step 4: Execute LLM with template + knowledge

            try:
                llm = ChatOllama(model=MODEL, temperature=0.3)


                response = llm.invoke([
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": formatted_prompt}
                ])

                result = response.content.strip()

                # Add source attribution if available
                if sources:
                    result += "\n\n---\n*Sources: " + ", ".join(set(sources)) + "*"

                print(f"[SUCCESS] Response generated ({len(result)} chars)")
                return result

            except Exception as llm_error:
                print(f"[WARNING] LLM error: {llm_error}")
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

            search_data = unwrap(search_result)

            if "error" in search_data:
                return f"Search error: {search_data['error']}"

            matches = search_data.get("matches", [])
            if not matches:
                return (
                    "I couldn't find relevant information about that in our documentation. "
                    "Please try rephrasing your question or contact our support team."
                )

            print(f"[INFO] Found {len(matches)} relevant documents")

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
                )

                user_msg = (
                )

                response = llm.invoke([
                ])

                result = response.content.strip()

                # Add sources
                if sources:
                    source_list = [s.split('/')[-1] if '/' in s else s for s in sources]
                    result += f"\n\n---\n*Sources: {', '.join(source_list)}*"

                return result

            except Exception as llm_error:
                print(f"[WARNING] LLM unavailable: {llm_error}")
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
        formatted_result = format_response(result)
        print(f"{GREEN}Agent:{RESET}\n{formatted_result}")
        print()

if __name__ == "__main__":
    print("=" * 70)
    print("OmniTech Customer Support RAG Agent")
    print("=" * 70)
    print("\nArchitecture:")
    print("  * MCP Server = Knowledge Layer")
    print("     - Owns OmniTech PDF documentation")
    print("     - Manages vector database (ChromaDB)")
    print("     - Provides classification & search tools")
    print("  * RAG Agent = Orchestration Layer")
    print("     - Routes to support or exploratory workflows")
    print("     - Executes LLM with retrieved knowledge")
    print("     - NO local file reading or embeddings")
    print("\nKnowledge Base:")
    print("  * Account Security Handbook")
    print("  * Device Troubleshooting Manual")
    print("  * Global Shipping Logistics")
    print("  * Returns Policy 2024")

    # Check if server is running
    print("\n[INFO] Checking MCP server status...")
    server_running = asyncio.run(check_server_running())

    if not server_running:
        print("\n[WARNING] Prerequisites:")
        print("  * MCP classification server is NOT running!")
        print("     Run: python mcp_server_classification.py")
        print("     The agent will not work without the server.")
    else:
        print("[SUCCESS] MCP classification server is running and ready.")

    print("\nCommands:")
    print("  * Type 'exit' to quit")
    print("  * Type 'demo' for sample queries")
    print("\nExample Support Queries:")
    print("  * Security: 'How do I reset my password?'")
    print("  * Device: 'My device won't turn on'")
    print("  * Shipping: 'Track my order'")
    print("  * Returns: 'What is your return policy?'")
    print("  * General: 'Tell me about OmniTech'")
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
            formatted_result = format_response(result)
            print(f"\n{GREEN}Agent:{RESET}\n{formatted_result}\n")
