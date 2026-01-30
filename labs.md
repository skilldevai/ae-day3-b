# Applied AI Engineering for the Enterprise
## Day 3 - MCP
## Session labs 
## Revision 2.0 - 01/30/26

**Versions of dialogs, buttons, etc. shown in screenshots may differ from current version used in dev environments**

**Follow the startup instructions in the README.md file IF NOT ALREADY DONE!**

**NOTES:**
1. We will be working in the public GitHub.com, not a private instance.
2. Chrome may work better than Firefox for some tasks.
3. Substitute the appropriate key combinations for your operating system where needed.
4. The default environment will be a GitHub Codespace (with everything you need already installed). If you prefer to use your own environment, you are responsible for installing the needed apps and dependencies in it. Some things in the lab may be different if you use your own environment.
5. To copy and paste in the codespace, you may need to use keyboard commands - CTRL-C and CTRL-V.**
6. VPNs may interfere with the ability to run the codespace. It is recommended to not use a VPN if you run into problems.
7. When your cursor is in a file in the editor and you need to type a command, be sure to click back in *TERMINAL* before typing so you don't write over file contents. If you do inadvertently write over contents, you can use "git checkout <filename>" to get the most recent committed version.
</br></br></br>



**Lab 1 - MCP Jumpstart**

**Purpose: In this lab, we'll see how to go from hand-rolled API calls to an MCP implementation.**

1. For our labs in this workshop, we have different directories with related code. For this lab, it is the *lab1* directory. Change into that directory in the terminal.
   
```
cd lab1
```
<br><br>

2. Let's first create a simple code example to invoke an API math function in the "classic" way - using a raw REST call.
   In the terminal, run the first command below to create a new file called *classic_calc.py*. 

```
code classic_calc.py
```
</br></br>

3. Here's the code for our simple API call. Paste the code below into the *classic_calc.py* file.
   
```
import requests, urllib.parse, sys

expr = urllib.parse.quote_plus("12*8")
url  = f"https://api.mathjs.org/v4/?expr={expr}"
print("Calling:", url)
print("Result :", requests.get(url, timeout=10).text)
```

![Creating classic_calc.py](./images/mcp4.png?raw=true "Creating classic_calc.py")
</br></br>

4. Save your changes (CTRL/CMD/OPTION + S). Now, run the code using the command below. You should see the expected answer (96) printed out. Notice that you needed to **know the endpoint, URL-encode the call, and parse the response** yourself. This is only for one tool, but imagine doing this for multiple tools.

```
python classic_calc.py
```
<br><br>

5. Now, let's see how we can use an MCP server to do this. There is an existing MCP server for simple calculator functions that we're going to be using in this lab. It is named *calculator-mcp* from *wrtnlabs*. (The code for it is in GitHub at https://github.com/wrtnlabs/calculator-mcp if you are interested.) Start a running instance of the server by using *npx* (a Node.js CLI). We'll start it running on port 8931. Run the command below and you should see output like the screenshot shown.

```
npx -y @wrtnlabs/calculator-mcp@latest --port 8931
```

![Running remote MCP server](./images/mcp5.png?raw=true "Running remote MCP server")
<br><br>


6. Now, let's open an additional terminal so we can run our custom code. You can use the "+" control in the upper right of the terminal to add a new terminal or just split the terminal. As shown here, we're splitting the terminal by clicking on the "down arrow" to the immediate right of the plus and selecting *Split terminal*.

![Splitting terminal](./images/mcp96.png?raw=true "Splitting terminal")
<br><br>

7. We have a small program that uses a MCP client to connect to a server and display information about available tools from the server. Let's use it to see what functions this MCP server provides. It assumes localhost and takes a port and transport as arguments. Run it with the command below:

```
python ../tools/discover_tools.py  8931 sse
```

![Discovering tools](./images/ae58.png?raw=true "Discovering tools")

<br><br>


8. Next, let's see how we can create a minimal client to use the MCP server. Create a new file called *mcp_client.py*. We'll add code for this in the next step.

```
code mcp_client.py
```
</br></br>

9. Now paste the code below into the file. Make sure to save your changes when done.

```
import asyncio
from fastmcp import Client

# latest version of FastMCP is async, so we need the async block
async def main():
    # The string URL is enough – FastMCP picks Streamable HTTP/SSE transport
    async with Client("http://127.0.0.1:8931/sse") as client:
        # Discover available tools
        tools = await client.list_tools()
        print("Discovered tools:", [t.name for t in tools])

        # invoke 'mul' w/o worrying about HTTP, auth, or schema
        result = await client.call_tool("mul", {"a": 12, "b": 8})
        print("12 × 8 =", result)        # → 96

if __name__ == "__main__":
    asyncio.run(main())
```
<br><br>

10. Notice that within this code we didn't have to code in endpoint formats, juggle query strings, or handcraft JSON schemas. Also, the server advertises all tools dynamically. In the second terminal, run the client with the command below and you should see output similar to the screenshot below. 

```
python mcp_client.py
```

![Running client](./images/ae59.png?raw=true "Running client")
</br></br>

11. Finally, let's build out a simple agent implementation that uses tools from this server in conjunction with a local LLM to respond to a prompt. We'll assemble the agent code again using the *diff and merge* approach. Run the command below and you can scroll down through the differences and merge them in to complete the code. When done, just click the "X" in the tab at the top to close this view.

```
code -d ../extra/agent_mcp.txt agent_mcp.py
```

![Diff view](./images/ae60.png?raw=true "Diff view")
</br></br>

12. Now, you can run the agent to see it in action. When this runs, it will show you the LLM's output and also the various tool calls and results. Note that it will take a while for the LLM to process things since it is running against a local model in our codespace. Also, since we are not using a very powerful or tuned model here, it is possible that you will see a mistake in the final output. If so, try running the agent code again. (Notice that we are using a different problem this time: 12x8/3)

```
python agent_mcp.py
```

![Running agent](./images/ae61.png?raw=true "Running agent")
</br></br>

You can stop the MCP server in the original terminal via CTRL-C.

<p align="center">
<b>[END OF LAB]</b>
</p>
</br></br></br>

**Lab 2 - MCP Features**

**Purpose: - In this lab, we'll use the Explorer tool to understand more about the different features that can be provided by MCP servers**

1. Change into the *lab2* directory in the terminal.
   
```
cd ../lab2
```
<br><br>

2. In this directory, we have an example MCP server with tools, a prompt, and a resource.  It's designed as a "travel assistant" example. Open the file and take a look at the code. You can use the command below for that or click on it in the files list. The numbered comments highlight the key parts.

```
code mcp_travel_server.py
```
<br><br>

3. Now, let's start the server running. Issue the command below in the terminal to run a startup script. You should see the code start up and say it is running on localhost (127.0.0.1) and availale on port 8000. (

```
python mcp_travel_server.py
```

![Running server](./images/mcp111.png?raw=true "Running server")
<br><br>


4. Let's use the MCP Explorer tool to look at items in the server. The server will be running in one terminal. In another terminal, start the explorer with the command below. Once it starts, you'll see a popup with a button to "*Open in Browser". Click on that to open it. (As shown the command assumes you are in the root directory. If not, use *../scripts* instead of *scripts*.)

```
python scripts/mcp_explorer.py http://localhost:8000/mcp 8080
```

![Start explorer](./images/ae62.png?raw=true "Start explorer")
<br><br>


5. You should automatically be connected to the server. The *Prompts* item will be selected by default. (If the prompt is not shown, you can click on *Prompts*.)

![Resources](./images/ae63.png?raw=true "Resources") 
<br><br>


6. As shown in the *Arguments* section below the prompt text, this prompt takes a *city* as an argument. Click on the *Get Prompt* button and you'll see a dialog pop up at the top. It's asking for an argument to fill in to show what the instantiated prompt would look like. Enter the text below (note this is in JSON format).

```
{"city": "Paris"}
```

![Prompt](./images/ae64.png?raw=true "Prompt") 
<br><br>

7. Click *OK* and you'll see the prompt result (with your argument) displayed. Click OK when done.

![Completed prompt](./images/ae65.png?raw=true "Completed prompt") 
<br><br>

8. Next, let's take a look at the resources available from the server. Click on the *Resources* button, then *Read Resource*. What you'll see is the resource with the major cities provided by the server.

![Resources](./images/ae66.png?raw=true "Resources") 
<br><br>

9. Finally, let's take a look at the tools available from the server. Click on *Tools*. You'll see two tools defined - one to calculate distance and one to convert currency.

![Tools](./images/mcp112.png?raw=true "Tools") 
<br><br>


10. Let's try running the distance_between tool. Select the tool in the list. Underneath, you'll see the input fields for the tool. You can try any latitude and longitude values you want and then click *Execute to see the results. (The example used in the screeshot - 40,74 and 51, .12 - equates roughly to New York and London.)

![Running tool](./images/mcp113.png?raw=true "Running tool") 
<br><br>

11. In preparation for other labs, you can stop (CTRL+C) the running instance of mcp_travel_server.py in your terminal to free up port 8000. You can also close the browser tab that has the explorer running in it.

<br><br>

<p align="center">
<b>[END OF LAB]</b>
</p>
</br></br></br>




**Lab 4 - Building a Customer Support Classification MCP Server**

**Purpose: In this lab, we'll build an MCP server that uses classifications and prompt templates for OmniTech customer support. The server will index the OmniTech knowledge base PDFs and provide RAG-based support for common customer queries.**

1. First, let's understand what we're building. The classification approach for customer support:
   - **Server**: Support query catalog, PDF indexing, knowledge retrieval, prompt templates
   - **Client**: LLM execution, workflow orchestration, response generation

   This creates a production-ready customer support system - just update server configuration to add new support categories.

   First, change back to the root directory of the project if not there.

```
cd /workspaces/ae-day3-b
```

<br><br>

2. We have a skeleton file for our new classification server that shows the structure. Let's examine it and then build it out using our familiar diff-and-merge approach.

```
code -d extra/mcp_server_support_solution.txt mcp_server_classification.py
```

<br>

As you review the differences, note the key components:
   - **CANONICAL_QUERIES**: A catalog of customer support query types:
     * `account_security`: Password resets, 2FA, account recovery
     * `device_troubleshooting`: Technical issues and device problems
     * `shipping_inquiry`: Order tracking and delivery information
     * `returns_refunds`: Return policies and warranty claims
     * `general_support`: General customer assistance
   - **PDF Indexing**: Automatic indexing of OmniTech knowledge base PDFs on startup
   - **Classification tools**: `classify_canonical_query()` matches customer questions to support categories
   - **Knowledge retrieval**: `vector_search_knowledge()` and `get_knowledge_for_query()` for RAG
   - **Template tools**: `get_query_template()` returns customer support prompts

<br>

![Updating the MCP server](./images/aia-2-31.png?raw=true "Updating the MCP server") 

<br><br>

3. Merge each section by clicking the arrows. Pay attention to:
   - How customer support queries are defined with category-specific templates
   - The PDF indexing process that runs automatically on startup
   - How each support category searches only relevant PDF documents
   - The keyword matching logic that identifies support intent
   - How templates use `{knowledge}` placeholder for retrieved documentation

<br><br>

4. When finished merging, save the file by closing the tab. Now start the new server:

```
python mcp_server_classification.py
```

![Running the MCP server](./images/ae74.png?raw=true "Running the MCP server") 

<br><br>

5. The server should start and initialize its knowledge base. (You can scroll back up to see some output.) It will do:

   - Loading of the embedding model (all-MiniLM-L6-v2)
   - Initialization of ChromaDB at ./mcp_chroma_db
   - **PDF Indexing**: Automatic indexing of OmniTech knowledge base:
     * Account Security Handbook
     * Device Troubleshooting Manual
     * Global Shipping Logistics
     * Returns Policy 2024
   - Creation of vector collection with categorized chunks

  The server now provides customer support tools:
   - **Knowledge Search** : RAG-based semantic search through PDFs
   - **Classification** : Support query intent classification
   - **Templates** : Customer support prompt templates
   - **Knowledge Retrieval** : Category-specific documentation retrieval
   - **Validation** : Query validation tools
   - **Statistics** : Knowledge base statistics
  

![Running the MCP server](./images/ae75.png?raw=true "Running the MCP server") 

<br><br>

6. Here's the knowledge base architecture:
    - The MCP server owns and manages the entire knowledge base
    - All OmniTech PDFs are automatically indexed into ChromaDB
    - Each document chunk is categorized (security, troubleshooting, shipping, returns)
    - Semantic search enables intelligent answer retrieval
    - Multiple support agents can share the same knowledge base

Let's see the list of tools the MCP server makes available. We can run the discover tool again for this.  Run it in a separate terminal as shown below (adjust the path if needed).

```
python tools/discover_tools.py 8000 mcp
```

<br><br>

7.  You should see several customer support tool categories:
   - **Knowledge search tools**: `vector_search_knowledge`, `get_knowledge_for_query`
   - **Classification tools**: `classify_canonical_query`, `get_query_template`, `list_canonical_queries`
   - **Validation tools**: `validate_support_query`
   - **Statistics tools**: `get_knowledge_base_stats`

![Discover tools](./images/ae76.png?raw=true "Discover tools") 

<br><br>

8. The server is now ready to handle customer support queries using the OmniTech knowledge base. It can classify support requests, retrieve relevant documentation, and provide structured templates for consistent responses. In the next lab, we'll build an agent that leverages these capabilities, so you can leave it running.

9. (**OPTIONAL**) If you have extra time and want to explore the server more, you can start up our MCP Explorer tool and play with running some of the tools in the server. If you run the command below (from the root of the project), and it tries to open up another codespace instance, just close that and then run the command again.

```
 $ python ./scripts/mcp_explorer.py http://localhost:8000/mcp 8080
```

![Discover tools](./images/aia-2-46.png?raw=true "Discover tools") 


<p align="center">
<b>[END OF LAB]</b>
</p>
</br></br>

**Lab 5 - Building a Customer Support RAG Agent**

**Purpose: In this lab, we'll build a customer support agent that uses the classification server from Lab 4. This agent demonstrates the 4-step support workflow: classify → template → retrieve knowledge → execute.**

1.  Let's build out the customer support agent using our skeleton file. This agent demonstrates a **production RAG architecture** where:
   - The MCP server owns all knowledge (vector DB, PDFs, embeddings)
   - The agent is pure orchestration (no local files, no local vector DB)
   - Support queries are classified and answered using the OmniTech knowledge base
   - Direct RAG search handles exploratory questions

   This represents best practices for production customer support systems with clear separation of concerns. From the ```/workspaces/ae-day3-b``` directory, run the following command:

```
code -d extra/rag_agent_classification_solution.txt rag_agent_classification.py
```

<br>

As you review and merge the differences, observe the key architectural patterns:
   - **Simplified imports**: No chromadb, pdfplumber, or sentence-transformers needed
   - **MCP-centric knowledge access**: All documentation comes from MCP server
   - **Query routing**: Keywords determine support category vs. exploratory search
   - **Support workflow**: 4-step process (classify → template → retrieve knowledge → execute)
   - **RAG workflow**: Direct semantic search through knowledge base
   - **Local LLM execution**: Agent only runs the LLM, knowledge comes from server

<br>

![Updating the RAG agent](./images/aia-2-40.png?raw=true "Updating the RAG agent") 

<br><br>

2.  Merge each section carefully. Notice two key functions:
   - `handle_canonical_query_with_classification()`: Orchestrates the 4-step support workflow for classified queries (around line 132)
   - `handle_rag_search()`: Performs direct semantic search for exploratory questions (around line 242)

   The agent has no local file reading, no embeddings, no vector database - everything comes from MCP.

<br><br>

3. When finished merging, save the file. Make sure your classification server from Lab 4 is still running (if not, restart it).

```
(if needed) python mcp_server_classification.py
```

Reminder: This can take a while to start...

<br><br>

4. Now start the classification agent in a second terminal with the command below. The agent will start and show some information about its architecture and sources.
   
```
python rag_agent_classification.py
```

![Running the RAG agent](.ae77.png?raw=true "Running the RAG agent") 

<br><br>

5. You can try out some of the queries shown below. Note that some may take multiple minutes to process and respond.

**Account Security Questions:**
```
How do I reset my password?
Can you help me set up two-factor authentication?
What should I do if my account is compromised?
```

**Device Troubleshooting:**
```
My device won't turn on, what should I do?
How do I perform a factory reset?
The screen is frozen, how can I fix it?
```

**Shipping & Orders:**
```
When will my order arrive?
Do you ship internationally?
How can I track my package?
```

**Returns & Refunds:**
```
What is your return policy?
How long do I have to return a product?
Is my device still under warranty?
```

![Running the RAG agent](./images/aia-2-41.png?raw=true "Running the RAG agent") 

<br><br>

6. Observe the workflow differences:

    **Classified Support Queries** ("How do I reset my password?"):
    - Agent calls MCP's `classify_canonical_query(...)`
    - MCP returns: "account_security"
    - Agent calls `get_query_template("account_security")`
    - Agent calls `get_knowledge_for_query("account_security", "password reset")`
    - MCP searches only security-related documentation
    - Agent executes LLM locally with template + knowledge

    **Direct RAG Search** ("Tell me about your products"):
    - Agent calls MCP's `vector_search_knowledge("products")`
    - MCP performs semantic search across all PDFs
    - Returns relevant documentation chunks
    - Agent synthesizes response from retrieved knowledge

    **Category-Specific Search**:
    - Security queries search only Account Security Handbook
    - Troubleshooting queries search Device Manual
    - Shipping queries search Logistics documentation
    - Returns queries search Returns Policy


![Running the RAG agent](./images/aia-2-42.png?raw=true "Running the RAG agent") 


<br><br>

7. Notice the architectural benefits:
   - **Classified queries**: Use category-specific search for accurate, focused answers
   - **RAG search**: Semantic search across entire knowledge base for exploratory questions
   - **No duplication**: MCP server owns all knowledge, agent is pure orchestration
   - **Scalability**: Multiple support agents can share the same knowledge base
   - **Consistency**: Templates ensure uniform support responses
   - **Maintainability**: Update PDFs on server, all agents get new knowledge

   This centralized architecture follows best practices for production customer support systems.

  The power of this architecture is that you can add new support categories or update documentation just by modifying the server - no agent code changes needed. Type 'exit' when done to stop the agent.



<p align="center">
<b>[END OF LAB]</b>
</p>
</br></br>

<br><br>
**THE END**

