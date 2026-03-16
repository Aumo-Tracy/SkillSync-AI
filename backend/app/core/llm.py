import litellm
from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Configure LiteLLM
litellm.openai_key = settings.openai_api_key
litellm.gemini_key = settings.gemini_api_key

# Suppress verbose litellm logs in development
litellm.set_verbose = False

AVAILABLE_MODELS = {
    "openai": "gpt-4o-mini",
    "openai_large": "gpt-4o",
    "gemini": "gemini/gemini-2.0-flash",
    "gemini_large": "gemini/gemini-1.5-pro-latest",
}

async def call_llm(
    messages: list[dict],
    provider: str = None,
    temperature: float = 0.7,
    max_tokens: int = 2000,
    response_format: dict = None
) -> str:
    provider = provider or settings.default_llm_provider
    model = AVAILABLE_MODELS.get(provider, AVAILABLE_MODELS["openai"])
    
    kwargs = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    
    if response_format:
        kwargs["response_format"] = response_format
    
    try:
        response = await litellm.acompletion(**kwargs)
        content = response.choices[0].message.content
        
        # Log token usage
        if hasattr(response, "usage"):
            logger.info(
                f"LLM call | model={model} | "
                f"tokens={response.usage.total_tokens}"
            )
        
        return content
        
    except Exception as e:
        logger.error(f"LLM call failed | model={model} | error={e}")
        raise