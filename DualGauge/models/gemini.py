"""
Google Gemini API wrapper.
"""

import logging
import time
import google.generativeai as genai

logger = logging.getLogger(__name__)


class GeminiModel:
    
    def __init__(self, model_name, api_key, temperature=0):
        self.model_name = model_name
        self.api_key = api_key
        self.temperature = temperature
        genai.configure(api_key=api_key)
        
        # Safety settings to allow security testing code generation
        safety_settings = [
            {
                "category": "HARM_CATEGORY_DANGEROUS",
                "threshold": "BLOCK_NONE",
            },
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_NONE",
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_NONE",
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_NONE",
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_NONE",
            },
        ]
        
        self.model = genai.GenerativeModel(model_name, safety_settings=safety_settings, generation_config={'temperature': self.temperature})
        self.rate_limit_delay = 60
    
    def generate(self, prompt, trial=0):
        """
        Send prompt to Gemini and return response.
        
        Args:
            prompt: Text prompt to send
            trial: Retry attempt number (default: 0)
            
        Returns:
            Response text from the model
        """
        try:
            response = self.model.generate_content(prompt)
            
            # Handle cases where response might not have text
            if response and hasattr(response, 'text'):
                return response.text
            elif response and hasattr(response, 'candidates') and response.candidates:
                # Try to extract text from candidates
                return response.candidates[0].content.parts[0].text
            
            logger.warning(f"Gemini returned empty response")
            return "ERROR"
        
        except Exception as e:
            if trial < 3:
                logger.warning(f"Gemini API error (trial {trial}): {e}. Retrying after {self.rate_limit_delay}s...")
                time.sleep(self.rate_limit_delay)
                return self.generate(prompt, trial=trial + 1)
            else:
                logger.error(f"Gemini API error after 3 trials: {e}")
                return "ERROR"
