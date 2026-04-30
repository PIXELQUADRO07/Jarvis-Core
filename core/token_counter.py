#!/usr/bin/env python3
"""
Token counter for LLM token usage estimation.
Estimates tokens based on character count using model-specific ratios.
"""

from typing import Optional


class TokenCounter:
    """Estimate LLM token count from text"""
    
    # Token ratios (approximate chars per token for different models)
    TOKEN_RATIOS = {
        "mistral": 1.33,
        "neural-chat": 1.35,
        "llama2": 1.30,
        "openchat": 1.32,
        "dolphin": 1.34,
        "orca": 1.31,
        "default": 1.33,  # Default ratio
    }
    
    @classmethod
    def estimate_tokens(cls, text: str, model: str = "mistral") -> int:
        """
        Estimate token count for text
        
        Args:
            text: Text to estimate
            model: Model name (determines ratio)
        
        Returns:
            Estimated token count
        """
        if not text:
            return 0
        
        ratio = cls.TOKEN_RATIOS.get(model.lower(), cls.TOKEN_RATIOS["default"])
        tokens = max(1, int(len(text) / ratio))
        return tokens
    
    @classmethod
    def format_usage(cls, prompt_tokens: int, completion_tokens: int) -> str:
        """
        Format token usage for display
        
        Args:
            prompt_tokens: Tokens in prompt
            completion_tokens: Tokens in response
        
        Returns:
            Formatted usage string
        """
        total = prompt_tokens + completion_tokens
        return f"📊 Tokens: {prompt_tokens} (prompt) + {completion_tokens} (response) = {total}"
    
    @classmethod
    def estimate_cost(
        cls, 
        prompt_tokens: int, 
        completion_tokens: int, 
        model: str = "mistral"
    ) -> Optional[str]:
        """
        Estimate API cost (if using external API)
        
        Args:
            prompt_tokens: Tokens in prompt
            completion_tokens: Tokens in response
            model: Model name
        
        Returns:
            Cost string or None if using local Ollama
        """
        # For local Ollama, no cost
        if model.lower() in ["mistral", "llama2", "neural-chat", "orca"]:
            return None
        
        # Placeholder for external API costs
        return None


if __name__ == "__main__":
    # Test token counter
    print("🧪 Token Counter Test")
    print("=" * 40)
    
    test_text = "Ciao JARVIS, come stai? Mi piacerebbe sapere il meteo di oggi."
    
    for model in ["mistral", "llama2", "neural-chat", "default"]:
        tokens = TokenCounter.estimate_tokens(test_text, model)
        print(f"{model:12} → {tokens} tokens")
    
    print("\n" + "=" * 40)
    print("Format test:")
    usage = TokenCounter.format_usage(50, 150)
    print(usage)
