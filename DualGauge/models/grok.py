"""
Grok (xAI) API wrapper.
Grok uses OpenAI-compatible API.
"""

import logging
import time
from openai import OpenAI

logger = logging.getLogger(__name__)


class GrokModel:
    
    def __init__(self, model_name, api_key):
        self.model_name = model_name
        self.api_key = api_key
        
        # Grok uses OpenAI-compatible API with custom base URL
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.x.ai/v1"
        )
        self.rate_limit_delay = 60
    
    def generate(self, prompt, trial=0):
        """
        Send prompt to Grok and return response.
        
        Args:
            prompt: Text prompt to send
            trial: Retry attempt number (default: 0)
            
        Returns:
            Response text from the model
        """
        try:
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful Assistant. When generating code ensure to put the code within ``` tags."},
                    {"role": "user", "content": prompt}
                ]
            )
            return completion.choices[0].message.content
        
        except Exception as e:
            if trial < 3:
                logger.warning(f"Grok API error (trial {trial}): {e}. Retrying after {self.rate_limit_delay}s...")
                time.sleep(self.rate_limit_delay)
                return self.generate(prompt, trial=trial + 1)
            else:
                logger.error(f"Grok API error after 3 trials: {e}")
                return "ERROR"
    
    def generate_with_web_search(self, prompt, max_searches=3, trial=0):
        """
        Generate response with web search capability enabled.
        
        Note: Grok supports web search but implementation may vary.
        This falls back to regular generation for now.
        
        Args:
            prompt: Text prompt to send
            max_searches: Maximum number of web searches (not used)
            trial: Retry attempt number (default: 0)
            
        Returns:
            Response text from the model
        """
        logger.warning("Grok web search not yet implemented. Falling back to regular generation.")
        return self.generate(prompt, trial=trial)

