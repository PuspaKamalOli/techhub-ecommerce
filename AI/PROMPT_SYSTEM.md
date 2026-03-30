# Advanced Prompt System

## Overview
The chatbot now uses a sophisticated, context-aware prompt building system that handles most situations dynamically. This system follows SOLID principles and provides better responses across various scenarios.

## Architecture

### PromptBuilder Service
Located in `AI/services/prompt_builder.py`, this service is responsible for:
- Building context-aware prompts based on user intent
- Handling different conversation scenarios
- Providing clear instructions to the LLM
- Managing conversation history and RAG context

### Key Features

#### 1. **System Persona**
Every prompt includes a consistent system persona that defines:
- Role: E-commerce assistant for TechHub
- Responsibilities: Product info, cart management, orders, general questions
- Guidelines: Polite, professional, concise (1-3 sentences max)
- Security: Never share other users' information

#### 2. **Context-Aware Prompt Types**

##### Greeting Prompts
- Warm, friendly responses
- Brief (1-2 sentences)
- Invites users to ask questions
- Uses conversation history for context

##### Tool Result Prompts
- Parses JSON tool results
- Extracts specific numbers, names, prices
- Formats information clearly
- Provides examples of good responses
- Handles errors gracefully

##### Product Query Prompts
- Uses RAG context when available
- Falls back to general knowledge if context insufficient
- Provides specific product names and prices
- Acknowledges when information is unavailable

##### General Question Prompts
- Uses RAG context from knowledge base
- Adapts based on context quality
- Falls back gracefully when context is poor
- Maintains conversation flow

##### Database Query Prompts
- Includes tool descriptions
- Provides clear instructions for tool calling
- Includes examples of tool usage
- Emphasizes security (user_id scoping)

##### Error Handling Prompts
- Acknowledges errors briefly
- Suggests alternatives
- Reassuring and helpful
- Maintains user confidence

##### Clarification Prompts
- Asks for missing information politely
- Provides examples
- Brief and specific

#### 3. **Dynamic Context Building**

The system automatically:
- Extracts conversation history (last 5 exchanges)
- Retrieves relevant RAG context
- Includes tool results when available
- Adapts prompt complexity based on context quality

## Prompt Structure

### Standard Prompt Format

```
[System Persona]
[Conversation Context (if available)]
[RAG Context (if available)]
[Tool Results (if applicable)]
[User Message]
[Specific Instructions]
```

### Example: Greeting Prompt

```
You are a helpful, professional e-commerce assistant for TechHub...

Previous conversation:
User: hello
Assistant: Hi! How can I help?

User: hello again
Respond warmly but briefly (1-2 sentences max). Be friendly and invite them to ask questions.
```

### Example: Tool Result Prompt

```
You are a helpful, professional e-commerce assistant for TechHub...

User asked: check my cart

Tool execution results:
{"success": true, "cart": {"total_items": 2, "items": [...]}}

Instructions:
1. Parse the JSON results carefully
2. Extract specific numbers, names, prices, and quantities
3. Present the information in a clear, user-friendly format
4. Keep response BRIEF (2-3 sentences max)
5. Don't mention tool names or technical details

Examples of good responses:
- "You have 3 items in your cart: iPhone 15 Pro, MacBook Pro 14", Dell XPS 13. Total: $4099.97."
```

## Benefits

### 1. **Consistency**
- All prompts follow the same structure
- System persona is consistent across all interactions
- Response style is uniform

### 2. **Context Awareness**
- Uses conversation history effectively
- Leverages RAG context when available
- Adapts to context quality

### 3. **Better Instructions**
- Clear, specific instructions for the LLM
- Examples of good responses
- Handles edge cases gracefully

### 4. **Error Handling**
- Graceful degradation when context is poor
- Helpful error messages
- Suggests alternatives

### 5. **Security**
- Emphasizes user data privacy
- Scopes operations to authenticated user
- Never shares other users' information

## Usage in Handlers

All handlers now use the `PromptBuilder` service:

```python
from AI.services.prompt_builder import PromptContext

context = PromptContext(
    message=message,
    intent=intent,
    conversation_history=chat_history,
    rag_context=rag_context,
    user_id=user_id,
    max_history=5
)

prompt = self.prompt_builder.build_greeting_prompt(context)
response = self.llm_service.invoke(prompt)
```

## Customization

### Modifying System Persona

Edit `SYSTEM_PERSONA` in `PromptBuilder` class:

```python
SYSTEM_PERSONA = """Your custom persona here..."""
```

### Adding New Prompt Types

1. Create a new method in `PromptBuilder`:
```python
def build_custom_prompt(self, context: PromptContext) -> str:
    # Build your custom prompt
    return prompt
```

2. Use it in the appropriate handler:
```python
prompt = self.prompt_builder.build_custom_prompt(context)
```

### Adjusting Response Length

Modify `max_response_sentences` in `PromptContext` or update instructions in prompt methods.

## Best Practices

1. **Always include system persona** - Provides consistent behavior
2. **Use conversation history** - Maintains context across exchanges
3. **Include examples** - Helps LLM understand desired format
4. **Handle errors gracefully** - Provides helpful fallbacks
5. **Keep instructions clear** - Specific, actionable guidance
6. **Adapt to context quality** - Different prompts for different situations

## Testing

Test different scenarios:
- Greetings
- Product queries
- Cart operations
- Order inquiries
- Error cases
- Edge cases (empty cart, no products, etc.)

## Future Enhancements

Potential improvements:
- Multi-turn conversation tracking
- Sentiment analysis integration
- Dynamic prompt selection based on user behavior
- A/B testing different prompt variations
- Prompt caching for common scenarios

