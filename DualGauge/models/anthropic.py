"""
Anthropic API wrapper.
"""

import logging
import time
import anthropic

logger = logging.getLogger(__name__)


class AnthropicModel:
    
    def __init__(self, model_name, api_key, temperature=0, max_tokens=4096, thinking=None, output_config=None):
        self.model_name = model_name
        self.api_key = api_key
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.thinking = thinking
        self.output_config = output_config
        self.client = anthropic.Anthropic(api_key=api_key)
        self.web_search_version = "web_search_20250305"
        self.rate_limit_delay = 60
        # Sticky flag: once Anthropic rejects `temperature` for this model,
        # stop sending it on subsequent calls. Avoids a 400 + 60s retry sleep
        # on every prompt for newer models that have deprecated the param.
        self._supports_temperature = True
    
    def _build_request_kwargs(self, prompt):
        request_kwargs = {
            "model": self.model_name,
            "max_tokens": self.max_tokens,
            "messages": [
                {"role": "user", "content": prompt}
            ],
        }
        if self.thinking:
            request_kwargs["thinking"] = self.thinking
        if self.output_config:
            request_kwargs["output_config"] = self.output_config
        elif self._supports_temperature:
            request_kwargs["temperature"] = self.temperature
        return request_kwargs

    def _call_with_temperature_fallback(self, prompt):
        """Make the API call, transparently dropping `temperature` if the
        model rejects it (Anthropic deprecated it for newer reasoning-capable
        models). Sets a sticky flag so subsequent calls skip the param."""
        request_kwargs = self._build_request_kwargs(prompt)
        try:
            return self.client.messages.create(**request_kwargs)
        except Exception as e:
            msg = str(e).lower()
            if "temperature" in msg and ("deprecated" in msg or "unsupported" in msg or "not supported" in msg):
                logger.warning(
                    "Anthropic rejected `temperature` for %s; disabling for subsequent calls.",
                    self.model_name,
                )
                self._supports_temperature = False
                request_kwargs.pop("temperature", None)
                return self.client.messages.create(**request_kwargs)
            raise

    def generate(self, prompt, trial=0):
        try:
            response = self._call_with_temperature_fallback(prompt)
            texts = []
            for block in response.content:
                if getattr(block, "type", None) == "text":
                    texts.append(getattr(block, "text", ""))
            return "".join(texts)

        except Exception as e:
            if trial < 3:
                logger.warning(f"Anthropic API error (trial {trial}): {e}. Retrying after {self.rate_limit_delay}s...")
                time.sleep(self.rate_limit_delay)
                return self.generate(prompt, trial=trial + 1)
            else:
                logger.error(f"Anthropic API error after 3 trials: {e}")
                return "ERROR"

    def generate_with_metadata(self, prompt, trial=0):
        try:
            response = self._call_with_temperature_fallback(prompt)
            text_blocks = []
            thinking_blocks = []
            for block in response.content:
                block_type = getattr(block, "type", None)
                if block_type == "text":
                    text_blocks.append(getattr(block, "text", ""))
                elif block_type == "thinking":
                    thinking_blocks.append(getattr(block, "thinking", ""))
            reasoning = "\n".join(piece for piece in thinking_blocks if piece) or None
            return {"content": "".join(text_blocks), "reasoning": reasoning}
        except Exception as e:
            if trial < 3:
                logger.warning(f"Anthropic API error (trial {trial}): {e}. Retrying after {self.rate_limit_delay}s...")
                time.sleep(self.rate_limit_delay)
                return self.generate_with_metadata(prompt, trial=trial + 1)
            logger.error(f"Anthropic API error after 3 trials: {e}")
            return {"content": "ERROR", "reasoning": None, "error": str(e)}
    
    def generate_with_web_search(self, prompt, max_searches=3, trial=0):
        """
        Generate response with web search capability enabled.
        
        Args:
            prompt: Text prompt to send
            max_searches: Maximum number of web searches allowed (default: 3)
            trial: Retry attempt number (default: 0)
            
        Returns:
            Response text from the model with web search results
        """
        try:
            tools = [{
                "type": self.web_search_version,
                "name": "web_search",
                "max_uses": max_searches
            }]
            
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=self.max_tokens,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                tools=tools
            )
            return response.content[0].text
        
        except Exception as e:
            if trial < 3:
                logger.warning(f"Anthropic web search error (trial {trial}): {e}. Retrying after {self.rate_limit_delay}s...")
                time.sleep(self.rate_limit_delay)
                return self.generate_with_web_search(prompt, max_searches=max_searches, trial=trial + 1)
            else:
                logger.error(f"Anthropic web search error after 3 trials: {e}")
                return "ERROR"
