import time
import os
import re
import logging
from .base_model import BaseModel
from openai import OpenAI

logger = logging.getLogger(__name__)


class OpenAIModel(BaseModel):
    """OpenAI API code generator."""

    def __init__(self, model, api_key=None, base_url=None, temperature=0, max_tokens=None, extra_body=None, system_prompt_prefix=None, reasoning_effort=None):
        if api_key is None:
            api_key = os.getenv('OPENAI_API_KEY', '') or os.getenv('OPEN_AI_KEY', '')
            if not api_key and not base_url:
                raise ValueError("OPENAI_API_KEY not found")
        kwargs = {"api_key": api_key or "token-abc123"}
        if base_url:
            kwargs["base_url"] = base_url
        self.model = OpenAI(**kwargs)
        self.rate_limit_delay = 60
        self.original_model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.extra_body = extra_body
        self.system_prompt_prefix = system_prompt_prefix.strip() if system_prompt_prefix else None
        # Explicit reasoning_effort wins; otherwise fall back to legacy
        # name-suffix parsing (e.g. "gpt-5-medium").
        if reasoning_effort:
            self.version = model
            self.reasoning_effort = reasoning_effort
        else:
            self.version, self.reasoning_effort = self._parse_model_and_effort(model)

    @staticmethod
    def _parse_model_and_effort(model: str):
        match = re.match(r"^(gpt-[^\s]+?)-(high|medium|low)$", model, re.IGNORECASE)
        if match:
            base_model = match.group(1)
            effort = match.group(2).lower()
            return base_model, effort
        return model, None

    @staticmethod
    def _supports_temperature(model_name: str) -> bool:
        """Return False for models/endpoints that reject the temperature parameter."""
        normalized = (model_name or "").lower()
        return not (
            normalized.startswith("gpt-5")
            or normalized.startswith("o1")
            or normalized.startswith("o3")
            or normalized.startswith("o4")
        )

    @staticmethod
    def _supports_system_role(model_name: str) -> bool:
        # Gemma / Mistral chat templates require strict user/assistant
        # alternation and reject a `system` role outright.
        normalized = (model_name or "").lower()
        return not ("gemma" in normalized or "mistral" in normalized)

    def _build_messages(self, system_prompt, user_content):
        if self._supports_system_role(self.version):
            return [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ]
        return [
            {"role": "user", "content": f"{system_prompt}\n\n{user_content}"},
        ]

    _HELPER_TEXT = "You are a helpful Assistant. When generating code ensure to put the code within ``` tags."

    def _build_system_prompt(self):
        # Default behaviour: helper text in system role.
        # Only diverges when system_prompt_prefix is set (e.g. Nemotron's
        # "detailed thinking on/off" toggle, which the model was trained to
        # parse as the entire system prompt). In that case the toggle stands
        # alone in the system role and the helper is moved to the user prompt
        # by _build_user_content. This keeps non-prefixed models (all current
        # closed and open models other than Nemotron) on the existing path.
        if self.system_prompt_prefix:
            return self.system_prompt_prefix
        return self._HELPER_TEXT

    def _build_user_content(self, prompt):
        if self.system_prompt_prefix:
            return f"{self._HELPER_TEXT}\n\n{prompt}"
        return prompt

    @staticmethod
    def _coerce_text(value):
        if value is None:
            return None
        if isinstance(value, str):
            return value
        if isinstance(value, list):
            pieces = []
            for item in value:
                if isinstance(item, str):
                    pieces.append(item)
                else:
                    text = getattr(item, "text", None)
                    if text:
                        pieces.append(text)
            return "".join(pieces) or None
        text = getattr(value, "text", None)
        if text:
            return text
        return str(value)

    def _extract_chat_reasoning(self, message):
        reasoning = getattr(message, "reasoning", None)
        if reasoning is not None:
            return self._coerce_text(reasoning)
        reasoning_content = getattr(message, "reasoning_content", None)
        if reasoning_content is not None:
            return self._coerce_text(reasoning_content)
        return None

    def _extract_response_reasoning(self, response):
        output = getattr(response, "output", None) or []
        pieces = []
        for item in output:
            content = getattr(item, "content", None) or []
            for block in content:
                block_type = getattr(block, "type", None)
                if block_type == "reasoning":
                    text = getattr(block, "text", None) or getattr(block, "summary", None)
                    if text:
                        pieces.append(self._coerce_text(text))
        combined = "\n".join(piece for piece in pieces if piece)
        return combined or None

    def _generate_internal(self, prompt):
        system_prompt = self._build_system_prompt()
        user_content = self._build_user_content(prompt)
        if self.reasoning_effort:
            response_kwargs = {
                "model": self.version,
                "reasoning": {"effort": self.reasoning_effort},
                "input": self._build_messages(system_prompt, user_content),
            }
            if self.max_tokens is not None:
                response_kwargs["max_output_tokens"] = self.max_tokens
            try:
                response = self.model.responses.create(**response_kwargs)
                return {
                    "content": response.output_text,
                    "reasoning": self._extract_response_reasoning(response),
                }
            except AttributeError:
                # Fall back to chat completions if responses API is unavailable.
                pass
            except TypeError as e:
                if "reasoning" in str(e).lower():
                    response_kwargs.pop("reasoning", None)
                    response = self.model.responses.create(**response_kwargs)
                    return {
                        "content": response.output_text,
                        "reasoning": self._extract_response_reasoning(response),
                    }
                raise

        create_kwargs = dict(
            model=self.version,
            messages=self._build_messages(system_prompt, user_content),
        )
        if self.max_tokens is not None:
            create_kwargs["max_tokens"] = self.max_tokens
        if self.extra_body:
            create_kwargs["extra_body"] = self.extra_body
        # Some models (e.g. gpt-5-nano / o-series) don't accept temperature
        try:
            create_kwargs["temperature"] = self.temperature
            completion = self.model.chat.completions.create(**create_kwargs)
        except Exception as temp_err:
            if "temperature" in str(temp_err).lower() or "unsupported" in str(temp_err).lower():
                create_kwargs.pop("temperature", None)
                completion = self.model.chat.completions.create(**create_kwargs)
            else:
                raise
        message = completion.choices[0].message
        return {
            "content": self._coerce_text(message.content) or "",
            "reasoning": self._extract_chat_reasoning(message),
        }
    
    def generate(self, prompt, trial=0):
        try:
            return self._generate_internal(prompt)["content"]

        except Exception as e:
            if trial < 3:
                logger.warning(
                    "OpenAI API error (model=%s, trial=%d): %s. Retrying after %ds...",
                    self.version, trial, e, self.rate_limit_delay,
                )
                time.sleep(self.rate_limit_delay)
                return self.generate(prompt, trial=trial + 1)
            else:
                logger.error("OpenAI API error after 3 trials (model=%s): %s", self.version, e)
                return "ERROR"

    def generate_with_metadata(self, prompt, trial=0):
        try:
            result = self._generate_internal(prompt)
            result.setdefault("reasoning", None)
            return result
        except Exception as e:
            if trial < 3:
                logger.warning(
                    "OpenAI API error (model=%s, trial=%d): %s. Retrying after %ds...",
                    self.version, trial, e, self.rate_limit_delay,
                )
                time.sleep(self.rate_limit_delay)
                return self.generate_with_metadata(prompt, trial=trial + 1)
            logger.error("OpenAI API error after 3 trials (model=%s): %s", self.version, e)
            return {"content": "ERROR", "reasoning": None, "error": str(e)}
    
    def generate_with_web_search(self, prompt, max_searches=3):
        """
        Generate with web search using OpenAI's responses API.
        
        Args:
            prompt: Text prompt to send
            max_searches: Maximum number of web searches (not used by OpenAI API)
            
        Returns:
            Response text from the model with web search results
        """
        try:
            response_kwargs = {
                "model": self.version,
                "tools": [{"type": "web_search"}],
                "input": prompt,
            }
            if self._supports_temperature(self.version):
                response_kwargs["temperature"] = self.temperature
            if self.reasoning_effort:
                response_kwargs["reasoning"] = {"effort": self.reasoning_effort}
            response = self.model.responses.create(**response_kwargs)
            return response.output_text
        except Exception as e:
            raise Exception(f"OpenAI web search error: {e}")
