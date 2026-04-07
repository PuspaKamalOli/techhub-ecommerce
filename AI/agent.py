"""
Fully Agentic Chatbot using LangChain's tool-calling AgentExecutor.

The LLM (ChatGroq / llama-3.3-70b-versatile) autonomously:
  - Selects which tools to call
  - Loops over multiple tool calls until the task is done
  - Uses conversation history for multi-turn context
  - Retrieves knowledge-base context via RAG

Replaces: intent_detector, all handlers, tool_executor, prompt_builder.
"""
import os
from typing import List, Optional, Dict

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

from langchain_groq import ChatGroq
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import BaseTool
import asyncio

from AI.config import ChatbotConfig
from AI.services.rag_service import RAGService

from AI.tools import (
    get_user_orders, get_user_cart, add_to_cart, remove_from_cart,
    update_cart_item_quantity, get_user_wishlist, add_to_wishlist,
    remove_from_wishlist, search_products, get_product_details,
    get_user_profile, generate_checkout_link, semantic_search_products
)

# ──────────────────────────────────────────────
# System prompt – TechHub persona
# ──────────────────────────────────────────────
SYSTEM_PROMPT = """You are TechHub Assistant, a helpful and friendly AI shopping assistant for TechHub, \
a premium electronics e-commerce store.

You help customers with:
- Searching and browsing products
- Managing their shopping cart (view, add, update quantities, remove items)
- Managing their wishlist (view, add, remove items)
- Viewing their orders and order status
- Viewing their profile information
- Placing orders from their cart

You have access to tools that connect directly to the TechHub database. Always use the tools \
to get real, accurate data — never make up product names, prices, or order details.

ABSOLUTE RULES (NEVER BREAK THESE):
1. You MUST call a tool BEFORE you claim the action was done.
   - To add an item: you MUST call add_to_cart first.
   - To remove an item: you MUST call remove_from_cart first.
   - To search exactly: you MUST call search_products first.
   - To discover abstract AI matching: you MUST call semantic_search_products first.
   - To place an order: you MUST call generate_checkout_link first.
   If you did NOT call the tool, do NOT say the action was completed.
   NEVER say "removed" or "added" unless you see the tool result confirming it.

2. Product ID matching — follow these steps EVERY TIME:
   Step 1: Look at the product name the user mentioned.
   Step 2: Find that EXACT product name in the search results or cart data.
   Step 3: Read the "id" or "product_id" number next to that EXACT name.
   Step 4: Use THAT number in your tool call.
   EXAMPLE: If results show One Plus 15 id=2, Samsung Galaxy S26 id=3 and the user says \
   "add One Plus", use product_id=2 (NOT 3). Match the NAME first, then get the ID.

3. NEVER use markdown formatting like asterisks (** or *) or hashes (#). Output plain text only.
4. NEVER use any emojis in your responses.
5. When listing products, ALWAYS show: name, product_id, price, availability.
6. When calling tools, use the correct built-in tool calling format. NEVER append JSON arguments \
   directly to the tool name string.

7. REASONING FIRST (CHAIN OF THOUGHT): Before you answer the user or call a tool, you MUST plan your steps out loud. Wrap your step-by-step thinking in a <think> ... </think> block. This enables you to process complex instructions safely and calculate constraints efficiently.

Other guidelines:
- For greetings, respond warmly WITHOUT calling any tools.
- Be concise (2-4 sentences max unless listing items).
- Always use the authenticated user_id provided in context.
- If you are unsure which product the user means, ASK for clarification. Do NOT guess.

{rag_context}"""


# ──────────────────────────────────────────────
# Tool list
# ──────────────────────────────────────────────
ALL_TOOLS = [
    # Standard TechHub DB tools
    get_user_orders,
    get_user_cart,
    add_to_cart,
    remove_from_cart,
    update_cart_item_quantity,
    get_user_wishlist,
    add_to_wishlist,
    remove_from_wishlist,
    search_products,
    semantic_search_products,
    get_product_details,
    get_user_profile,
    generate_checkout_link,
]

# ──────────────────────────────────────────────
# MCP (Model Context Protocol) Registry Builder
# ──────────────────────────────────────────────
def fetch_mcp_tools(server_script_paths: List[str]) -> List[BaseTool]:
    """
    Dynamically boot up local MCP servers via STDIO and load their tools into LangChain.
    This drastically expands the Agent's reasoning execution layers.
    """
    try:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
        from langchain_mcp_adapters.tools import load_mcp_tools

        async def _load():
            mcp_tools = []
            for script_path in server_script_paths:
                if not os.path.exists(script_path):
                    continue
                server_params = StdioServerParameters(command="python", args=[script_path])
                async with stdio_client(server_params) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        tools = await load_mcp_tools(session)
                        mcp_tools.extend(tools)
            return mcp_tools

        loop = asyncio.new_event_loop()
        return loop.run_until_complete(_load())
    except Exception as e:
        print(f"[MCP Warning] Failed to fetch external MCP tools: {e}")
        return []

# Initialize External MCP Tools from configured scripts (if any exist)
EXTERNAL_MCP_SERVERS = [os.path.join(os.path.dirname(__file__), "mcp_servers", "calculator_server.py")]
EXTENDED_TOOLS = ALL_TOOLS + fetch_mcp_tools(EXTERNAL_MCP_SERVERS)


def _build_lc_history(raw_history: List[Dict], session_id: str = "default_session") -> List:
    """
    Connects directly to the Redis backbone to retrieve true persistent memory.
    This replaces the shallow HTTP Session history capping with infinite storage.
    """
    try:
        from langchain_community.chat_message_histories import RedisChatMessageHistory
        redis_url = os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1')
        history = RedisChatMessageHistory(session_id, url=redis_url)
        
        # If Redis history is populated, we return it as LC format (it does this natively)
        # But we must format it to memory arrays.
        if len(history.messages) > 0:
            return history.messages
    except Exception as e:
        print(f"[Memory Warning] Redis Persistent Memory Offline. Using Volatile RAM: {e}")

    # Fallback volatile processing
    messages = []
    for entry in raw_history:
        if entry.get("user"):
            messages.append(HumanMessage(content=entry["user"]))
        if entry.get("assistant"):
            messages.append(AIMessage(content=entry["assistant"]))
    return messages


def _build_prompt(rag_context: str) -> ChatPromptTemplate:
    """Build the agent ChatPromptTemplate with injected RAG context."""
    system_text = SYSTEM_PROMPT.format(
        rag_context=f"\n---\nStore information:\n{rag_context}\n---" if rag_context else ""
    )
    return ChatPromptTemplate.from_messages([
        ("system", system_text),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])


def _build_executor(config: ChatbotConfig, user_id: int) -> AgentExecutor:
    """Build a fresh AgentExecutor bound to the given user."""
    if config.llm.use_ollama:
        from langchain_ollama import ChatOllama
        llm = ChatOllama(
            model=config.llm.ollama_model,
            temperature=config.llm.temperature,
        )
    else:
        llm = ChatGroq(
            api_key=config.groq_api_key,
            model=config.llm.model_name,
            temperature=config.llm.temperature,
            max_tokens=config.llm.max_tokens,
        )

    # Inject user_id context into every tool call via a partial wrapper
    # Tools receive user_id as an explicit argument; we rely on the LLM to
    # pass it correctly when given the authenticated user_id in the system prompt.
    # We add the user_id to the system prompt as contextual info.
    return llm, ALL_TOOLS


class ChatbotAgent:
    """
    Fully agentic chatbot.
    One instance per request (stateless); conversation history comes from the Django session.
    """

    def __init__(self, user_id: Optional[int] = None, config: Optional[ChatbotConfig] = None):
        self.user_id = user_id or 0
        self.config = config or ChatbotConfig()
        self.rag_service = RAGService(
            config=self.config.rag,
            knowledge_base_path=self.config.get_knowledge_base_path(),
        )

    def chat(self, message: str, chat_history: Optional[List[Dict]] = None, session_id: str = "default_session") -> str:
        """
        Process a user message and return the agent's response.

        Args:
            message:      User input text
            chat_history: Session history as [{user: ..., assistant: ...}]
            session_id:   The Redis tracking ID for persistent memory

        Returns:
            Agent response string
        """
        if chat_history is None:
            chat_history = []

        try:
            # 1. Retrieve RAG context
            rag_context = self.rag_service.retrieve_context(message, limit=2)

            # 2. Build prompt with RAG context baked in
            # Inject the authenticated user_id into the message so the LLM
            # knows which user_id to pass to every tool.
            augmented_message = (
                f"[Authenticated user_id: {self.user_id}]\n{message}"
            )

            prompt = _build_prompt(rag_context)

            # 3. Build LLM + agent
            if self.config.llm.use_ollama:
                from langchain_ollama import ChatOllama
                llm = ChatOllama(
                    model=self.config.llm.ollama_model,
                    temperature=self.config.llm.temperature,
                )
            else:
                llm = ChatGroq(
                    api_key=self.config.groq_api_key,
                    model=self.config.llm.model_name,
                    temperature=self.config.llm.temperature,
                    max_tokens=self.config.llm.max_tokens,
                )

            agent = create_tool_calling_agent(llm, EXTENDED_TOOLS, prompt)
            executor = AgentExecutor(
                agent=agent,
                tools=EXTENDED_TOOLS,
                verbose=True,
                max_iterations=8, # Bumped iterations to allow for deep CoT loops
                handle_parsing_errors=True
            )

            # 4. Convert history to LangChain format (with persistent Redis ID)
            chat_history_lc = _build_lc_history(chat_history, session_id=session_id)

            import time
            max_retries = 2
            last_error = None
            for attempt in range(max_retries + 1):
                try:
                    result = executor.invoke({
                        "input": augmented_message,
                        "chat_history": chat_history_lc,
                    })
                    raw_out = result.get("output", "Sorry, an error occurred in reasoning.")
                    
                    import re
                    cleaned_out = re.sub(r'[*#]', '', raw_out)
                    cleaned_out = re.sub(r'[\U00010000-\U0010ffff]', '', cleaned_out)
                    
                    return cleaned_out
                except Exception as invoke_err:
                    last_error = invoke_err
                    err_str = str(invoke_err).lower()
                    is_retryable = (
                        "failed to call a function" in err_str
                        or "tool call validation failed" in err_str
                        or "did not match schema" in err_str
                    )
                    is_rate_limited = "rate_limit" in err_str or "429" in err_str
                    if is_rate_limited and attempt < max_retries:
                        wait_secs = 15 * (attempt + 1)
                        print(f"[ChatbotAgent] Rate limited, waiting {wait_secs}s before retry")
                        time.sleep(wait_secs)
                        continue
                    if is_retryable and attempt < max_retries:
                        print(f"[ChatbotAgent] Retrying ({attempt + 1}/{max_retries}) after: {invoke_err}")
                        continue
                    raise last_error
        except Exception as e:
            import traceback
            print(f"[ChatbotAgent] Error: {e}")
            print(traceback.format_exc())
            err_str = str(e).lower()
            if "rate_limit" in err_str or "429" in err_str:
                return "I'm currently experiencing high demand. Please try again in a minute or two."
            return f"I apologize, but I encountered an error. Please try again."

    async def astream_chat(self, message: str, session_id: str = "default_session"):
        """
        [NEW] Asynchronous Streaming Execution for Server-Sent Events / WebSockets.
        Allows the frontend to stream <think> blocks and text responses in real-time.
        """
        rag_context = self.rag_service.retrieve_context(message, limit=2)
        augmented_message = f"[Authenticated user_id: {self.user_id}]\n{message}"
        prompt = _build_prompt(rag_context)
        
        # Build LLM + agent
        if self.config.llm.use_ollama:
            from langchain_ollama import ChatOllama
            llm = ChatOllama(
                model=self.config.llm.ollama_model,
                temperature=self.config.llm.temperature,
            )
        else:
            from langchain_groq import ChatGroq
            llm = ChatGroq(
                api_key=self.config.groq_api_key,
                model=self.config.llm.model_name,
                temperature=self.config.llm.temperature,
                max_tokens=self.config.llm.max_tokens,
            )
            
        agent = create_tool_calling_agent(llm, EXTENDED_TOOLS, prompt)
        executor = AgentExecutor(agent=agent, tools=EXTENDED_TOOLS, verbose=True, max_iterations=8)
        chat_history_lc = _build_lc_history([], session_id=session_id)

        try:
            async for event in executor.astream_events(
                {"input": augmented_message, "chat_history": chat_history_lc},
                version="v1"
            ):
                kind = event["event"]
                if kind == "on_chat_model_stream":
                    content = event["data"]["chunk"].content
                    if content:
                        yield content
        except Exception as e:
            yield f"\n[Stream Execution Error]: {str(e)}"


# ──────────────────────────────────────────────
# Factory (backward-compatible with views.py)
# ──────────────────────────────────────────────
def create_agent(user_id: Optional[int] = None) -> ChatbotAgent:
    """Create and return a ChatbotAgent instance."""
    return ChatbotAgent(user_id=user_id)
