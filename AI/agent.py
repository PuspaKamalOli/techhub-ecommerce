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

from AI.config import ChatbotConfig
from AI.services.rag_service import RAGService

from AI.tools import (
    get_user_orders, get_user_cart, add_to_cart, remove_from_cart,
    update_cart_item_quantity, get_user_wishlist, add_to_wishlist,
    remove_from_wishlist, search_products, get_product_details,
    get_user_profile, place_order,
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
   - To search: you MUST call search_products first.
   - To place an order: you MUST call place_order first.
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
    get_user_orders,
    get_user_cart,
    add_to_cart,
    remove_from_cart,
    update_cart_item_quantity,
    get_user_wishlist,
    add_to_wishlist,
    remove_from_wishlist,
    search_products,
    get_product_details,
    get_user_profile,
    place_order,
]


def _build_lc_history(raw_history: List[Dict]) -> List:
    """Convert session history [{user, assistant}] → LangChain messages."""
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

    def chat(self, message: str, chat_history: Optional[List[Dict]] = None) -> str:
        """
        Process a user message and return the agent's response.

        Args:
            message:      User input text
            chat_history: Session history as [{user: ..., assistant: ...}]

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

            agent = create_tool_calling_agent(llm, ALL_TOOLS, prompt)
            executor = AgentExecutor(
                agent=agent,
                tools=ALL_TOOLS,
                verbose=True,
                max_iterations=6,
                handle_parsing_errors=(
                    "Tool call validation failed. "
                    "CRITICAL: You must provide the tool name separate from the tool arguments. "
                    "Do NOT append JSON arguments to the tool name string. "
                    "Use ONLY the exact tool names provided in the schema."
                ),
            )

            # 4. Convert session history to LangChain messages
            lc_history = _build_lc_history(chat_history)

            # 5. Invoke with retry for transient Groq API errors
            import time
            max_retries = 2
            last_error = None
            for attempt in range(max_retries + 1):
                try:
                    result = executor.invoke({
                        "input": augmented_message,
                        "chat_history": lc_history,
                    })
                    raw_out = result.get("output", "I'm sorry, I couldn't process that. Please try again.")
                    
                    import re
                    # Strip markdown asterisks and hashes
                    cleaned_out = re.sub(r'[*#]', '', raw_out)
                    # Strip emojis (most are outside the basic multilingual plane)
                    cleaned_out = re.sub(r'[\U00010000-\U0010ffff]', '', cleaned_out)
                    
                    return cleaned_out
                except Exception as invoke_err:
                    last_error = invoke_err
                    err_str = str(invoke_err).lower()
                    # Retry on transient Groq tool-call validation errors
                    is_retryable = (
                        "failed to call a function" in err_str
                        or "tool call validation failed" in err_str
                        or "did not match schema" in err_str
                    )
                    # Retry on rate limit errors with backoff
                    is_rate_limited = "rate_limit" in err_str or "429" in err_str
                    if is_rate_limited and attempt < max_retries:
                        wait_secs = 15 * (attempt + 1)
                        print(f"[ChatbotAgent] Rate limited, waiting {wait_secs}s before retry ({attempt + 1}/{max_retries})")
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
            # Return user-friendly message for rate limit errors
            err_str = str(e).lower()
            if "rate_limit" in err_str or "429" in err_str:
                return "I'm currently experiencing high demand. Please try again in a minute or two."
            return f"I apologize, but I encountered an error. Please try again."


# ──────────────────────────────────────────────
# Factory (backward-compatible with views.py)
# ──────────────────────────────────────────────
def create_agent(user_id: Optional[int] = None) -> ChatbotAgent:
    """Create and return a ChatbotAgent instance."""
    return ChatbotAgent(user_id=user_id)
