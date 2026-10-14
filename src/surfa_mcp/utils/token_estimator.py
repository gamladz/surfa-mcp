"""Token estimation and cost calculation utilities."""

from typing import Any, Dict


# Tool-specific token estimates (tune these over time based on actual usage)
TOOL_ESTIMATES = {
    # Common patterns
    "get_user": 150,
    "get_session": 200,
    "search_database": 400,
    "list_items": 350,
    "fetch_data": 250,
    "update_record": 180,
    "delete_record": 120,
    
    # Add more as you learn patterns
}

# Default estimate if tool not in TOOL_ESTIMATES
DEFAULT_TOKEN_ESTIMATE = 200


# Model pricing per 1M tokens (as of 2026)
MODEL_PRICING = {
    # OpenAI
    "gpt-4": 0.03,
    "gpt-4-turbo": 0.01,
    "gpt-4o": 0.005,
    "gpt-3.5-turbo": 0.0015,
    
    # Anthropic
    "claude-3-opus": 0.015,
    "claude-3-sonnet": 0.003,
    "claude-3-haiku": 0.00025,
    "claude-3.5-sonnet": 0.003,
    "claude-3-5-sonnet-20241022": 0.003,
    
    # Fallback
    "unknown": 0.01,  # Assume GPT-4 Turbo pricing
}


def estimate_tokens_for_call(tool_name: str) -> int:
    """
    Estimate tokens for a tool call based on typical patterns.
    
    Args:
        tool_name: Name of the tool
        
    Returns:
        Estimated token count
    """
    return TOOL_ESTIMATES.get(tool_name, DEFAULT_TOKEN_ESTIMATE)


def calculate_cost(tokens: int, model: str) -> float:
    """
    Calculate cost in USD based on model pricing.
    
    Args:
        tokens: Number of tokens
        model: Model name (e.g., "gpt-4-turbo", "claude-3-sonnet")
        
    Returns:
        Cost in USD
    """
    # Normalize model name (handle variations)
    model_lower = model.lower()
    
    # Try exact match first
    if model_lower in MODEL_PRICING:
        price_per_million = MODEL_PRICING[model_lower]
    else:
        # Try partial match (e.g., "claude-3-sonnet-20240229" -> "claude-3-sonnet")
        price_per_million = None
        for known_model, price in MODEL_PRICING.items():
            if known_model in model_lower:
                price_per_million = price
                break
        
        # Fallback to unknown pricing
        if price_per_million is None:
            price_per_million = MODEL_PRICING["unknown"]
    
    return (tokens / 1_000_000) * price_per_million


def get_model_from_execution(execution: Dict[str, Any]) -> str:
    """
    Extract model name from execution metadata with fallback.
    
    Args:
        execution: Execution object with metadata
        
    Returns:
        Model name (e.g., "claude-3-sonnet", "gpt-4-turbo", or "unknown")
    """
    # Try to get from metadata.runtime.model
    metadata = execution.get("metadata", {})
    runtime = metadata.get("runtime", {})
    model = runtime.get("model")
    
    if model:
        return model
    
    # Try to infer from provider
    provider = runtime.get("provider", "").lower()
    if "anthropic" in provider or "claude" in provider:
        return "claude-3-sonnet"  # Most common Claude model
    elif "openai" in provider or "gpt" in provider:
        return "gpt-4-turbo"  # Most common GPT model
    
    # Fallback
    return "unknown"


def calculate_multi_model_costs(tokens: int) -> Dict[str, float]:
    """
    Calculate costs for multiple common models for comparison.
    
    Args:
        tokens: Number of tokens
        
    Returns:
        Dictionary of model -> cost in USD
    """
    return {
        "gpt_4": calculate_cost(tokens, "gpt-4"),
        "gpt_4_turbo": calculate_cost(tokens, "gpt-4-turbo"),
        "gpt_4o": calculate_cost(tokens, "gpt-4o"),
        "claude_opus": calculate_cost(tokens, "claude-3-opus"),
        "claude_sonnet": calculate_cost(tokens, "claude-3-sonnet"),
        "claude_haiku": calculate_cost(tokens, "claude-3-haiku"),
    }


def format_savings_estimate(
    calls_saved: int,
    tool_name: str | None = None,
    model: str = "unknown"
) -> Dict[str, Any]:
    """
    Format a savings estimate with tokens and costs.
    
    Args:
        calls_saved: Number of calls that could be saved
        tool_name: Optional tool name for better estimation
        model: Model name for cost calculation
        
    Returns:
        Formatted savings object
    """
    # Estimate tokens
    tokens_per_call = estimate_tokens_for_call(tool_name) if tool_name else DEFAULT_TOKEN_ESTIMATE
    tokens_saved = calls_saved * tokens_per_call
    
    # Calculate cost for detected model
    cost_for_model = calculate_cost(tokens_saved, model)
    
    # Calculate costs for comparison
    multi_model_costs = calculate_multi_model_costs(tokens_saved)
    
    return {
        "calls_saved": calls_saved,
        "tokens": {
            "estimated": tokens_saved,
            "is_estimated": True,
            "note": "Estimated based on typical tool usage. Enable token tracking for actual values."
        },
        "cost_usd": {
            **multi_model_costs,
            "detected_model": model,
            "detected_model_cost": cost_for_model,
        }
    }
