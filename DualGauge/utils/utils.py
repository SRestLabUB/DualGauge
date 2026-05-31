from __future__ import annotations

"""
Shared utility functions for all components.
"""
import re
import json
import os
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml
from config.constants import MAX_ERR_CHARS, OPENAI_API_KEY, ANTHROPIC_API_KEY, GEMINI_KEY, DEEPSEEK_KEY, GROK_KEY, VLLM_BASE_URL, VLLM_API_KEY

logger = logging.getLogger(__name__)


class ProgressLogger:
    """
    Append-only progress log for a single pipeline phase.

    Each entry is one tab-separated line:
        [TIMESTAMP] EVENT  key=value  key=value  ...

    The file is always appended to (never overwritten), so it is safe
    for parallel runs and can be followed with `tail -f`.
    Stdio output is unaffected — this is purely additive.
    """

    def __init__(self, log_path: str):
        self.log_path = log_path
        os.makedirs(os.path.dirname(log_path) if os.path.dirname(log_path) else '.', exist_ok=True)

    def _write(self, event: str, **kwargs):
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        parts = [f"[{ts}]", f"{event:<12}"]
        parts += [f"{k}={v}" for k, v in kwargs.items()]
        line = "  ".join(parts) + "\n"
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(line)

    def log(self, event: str, **kwargs):
        self._write(event, **kwargs)

    def summary(self, lines: list):
        """Append a freeform summary block at the end of a run."""
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write("\n=== SUMMARY ===\n")
            for line in lines:
                f.write(line + "\n")
            f.write("\n")


def setup_logging(verbose=False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[logging.StreamHandler(sys.stdout)]
    )

def get_model(model_spec, temperature=0, max_tokens=None, extra_body=None, system_prompt_prefix=None, thinking=None, reasoning_effort=None, output_config=None):
    """
    Get the appropriate model wrapper.

    model_spec format: "provider:model-name" or legacy bare model name.
      openai:gpt-4o
      anthropic:claude-3-5-sonnet-20241022
      gemini:gemini-1.5-pro
      deepseek:deepseek-chat
      grok:grok-beta
      vllm:meta-llama/Llama-3.1-8B-Instruct
      codex:gpt-5
      claudecode:sonnet
      openhands:claude-opus-4-7
      openhands:claude-opus-4-7

    temperature defaults to 0. Models that don't support it (e.g. o-series, gpt-5-nano)
    silently ignore it at call time.
    """
    explicit_provider = ':' in model_spec
    if explicit_provider:
        provider, model = model_spec.split(':', 1)
        provider = provider.lower().strip()
    else:
        # Legacy bare name — infer provider from name as before
        model = model_spec
        if 'gpt' in model.lower():
            provider = 'openai'
        elif 'claude' in model.lower():
            provider = 'anthropic'
        elif 'gemini' in model.lower():
            provider = 'gemini'
        elif 'deepseek' in model.lower():
            provider = 'deepseek'
        elif 'grok' in model.lower():
            provider = 'grok'
        elif 'qwen' in model.lower():
            provider = 'qwen'
        elif 'llama' in model.lower():
            provider = 'llama'
        elif 'codex' in model.lower():
            provider = 'codex'
            # Treat bare Codex labels as experiment aliases, not as the
            # underlying Codex model name. This lets Codex fall back to the
            # user's configured default model unless they explicitly pass
            # `codex:<model>` via --model_spec.
            model = ''
        elif 'claudecode' in model.lower() or 'claude-code' in model.lower():
            provider = 'claudecode'
            # Same behavior as Codex: bare experiment labels should not
            # force a CLI model override unless explicitly requested.
            model = ''
        elif 'openhands' in model.lower():
            provider = 'openhands'
            # Bare OpenHands labels are experiment aliases. The actual model
            # should come from `--model_spec openhands:<model>` or the user's
            # OpenHands settings file.
            model = ''
        elif VLLM_BASE_URL:
            provider = 'vllm'
        else:
            raise NotImplementedError(
                f"Cannot infer provider for model '{model}'. "
                f"Use explicit format: openai:<model>, anthropic:<model>, gemini:<model>, "
                f"deepseek:<model>, grok:<model>, vllm:<model>, codex:<model>, claudecode:<model>, openhands:<model>, sweagent:<model>"
            )

    if provider == 'openai':
        from models.openai import OpenAIModel
        return OpenAIModel(
            model,
            OPENAI_API_KEY,
            temperature=temperature,
            max_tokens=max_tokens,
            extra_body=extra_body,
            system_prompt_prefix=system_prompt_prefix,
            reasoning_effort=reasoning_effort,
        )
    elif provider == 'anthropic':
        from models.anthropic import AnthropicModel
        return AnthropicModel(
            model,
            ANTHROPIC_API_KEY,
            temperature=temperature,
            max_tokens=max_tokens or 4096,
            thinking=thinking,
            output_config=output_config,
        )
    elif provider == 'gemini':
        from models.gemini import GeminiModel
        return GeminiModel(model, GEMINI_KEY, temperature=temperature)
    elif provider == 'deepseek':
        from models.deepseek import DeepSeekModel
        return DeepSeekModel(model, DEEPSEEK_KEY, temperature=temperature)
    elif provider == 'grok':
        from models.grok import GrokModel
        return GrokModel(model, GROK_KEY)
    elif provider == 'vllm':
        from models.openai import OpenAIModel
        if not VLLM_BASE_URL:
            raise ValueError("VLLM_BASE_URL env var must be set to use vllm provider")
        return OpenAIModel(
            model,
            api_key=VLLM_API_KEY,
            base_url=VLLM_BASE_URL,
            temperature=temperature,
            max_tokens=max_tokens,
            extra_body=extra_body,
            system_prompt_prefix=system_prompt_prefix,
            reasoning_effort=reasoning_effort,
        )
    elif provider == 'qwen':
        from models.qwen import Qwen
        return Qwen(model)
    elif provider == 'llama':
        from models.llama import Llama3Instruct
        return Llama3Instruct(model)
    elif provider == 'codex':
        from models.codex import CodexModel
        return CodexModel(
            model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    elif provider == 'claudecode':
        from models.claudecode import ClaudeCodeModel
        return ClaudeCodeModel(
            model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    elif provider == 'openhands':
        from models.openhands import OpenHandsModel
        return OpenHandsModel(
            model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    else:
        raise NotImplementedError(f"Unknown provider '{provider}'. Supported: openai, anthropic, gemini, deepseek, grok, vllm, codex, claudecode, openhands")


def load_generation_profile(model_alias: str, config_path: Optional[str] = None) -> dict:
    """Load per-model generation settings from experiments/models.yaml when available."""
    if not model_alias:
        return {}

    if config_path is None:
        config_path = str(Path(__file__).resolve().parents[2] / "experiments" / "models.yaml")

    if not os.path.exists(config_path):
        return {}

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    model_cfg = (config.get("models", {}) or {}).get(model_alias, {}) or {}
    defaults = config.get("defaults", {}) or {}
    serve_cfg = model_cfg.get("serve", {}) or {}

    profile = {
        "provider": model_cfg.get("provider"),
        "model_id": model_cfg.get("model_id"),
        "reasoning_effort": model_cfg.get("reasoning_effort"),
        "max_tokens": model_cfg.get("max_new_tokens", defaults.get("max_new_tokens")),
        "system_prompt_prefix": model_cfg.get("system_prompt_prefix"),
        "extra_body": None,
        "thinking": None,
        "output_config": None,
    }

    if "enable_thinking" in serve_cfg:
        profile["extra_body"] = {
            "chat_template_kwargs": {
                "enable_thinking": bool(serve_cfg["enable_thinking"]),
            }
        }

    if model_cfg.get("extended_thinking"):
        budget_tokens = int(model_cfg.get("thinking_budget_tokens") or 0)
        if budget_tokens <= 0:
            budget_tokens = 1024
        if str(model_cfg.get("model_id", "")).startswith("claude-opus-4-7"):
            profile["thinking"] = {
                "type": "adaptive",
                "display": "summarized",
            }
            profile["output_config"] = {
                "effort": "xhigh",
            }
        else:
            profile["thinking"] = {
                "type": "enabled",
                "budget_tokens": budget_tokens,
            }
        profile["max_tokens"] = max(int(profile["max_tokens"] or 0), budget_tokens + 1)

    return profile

def extract_code_blocks(text):
    """Extract code snippets from fenced blocks after stripping Qwen-style reasoning tags."""
    if not text:
        return []
    sanitized = re.sub(r'<think>.*?</think>\s*', '', text, flags=re.DOTALL | re.IGNORECASE)
    code_blocks = re.findall(r'```(?:\w*\n)?(.*?)```', sanitized, re.DOTALL)
    return [block.strip() for block in code_blocks] if code_blocks else []

def save_text(text, path):
    """Save text to a file, creating directories as needed."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text.strip() + "\n")

def read_item_json(path):
    """Read and parse an item.json file."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def determine_file_extension(code: str) -> str | None:
    """
    Determine if the given code is Python (.py), C (.c), or C++ (.cpp).
    Returns None if it can't decide.
    """
    if not code or not code.strip():
        return None

    text = code.lower()

    # --- Python ---
    if any(kw in text for kw in ["def ", "import ", "from ", "self", "__init__"]):
        return ".py"

    # --- C/C++ shared ---
    if "#include" in text or "int main(" in text:
        # --- Definitely C++ ---
        cpp_indicators = ["std::", "cout <<", "cin >>", "template<", "using namespace std"]
        if any(marker in text for marker in cpp_indicators):
            return ".cpp"
        # --- Probably C ---
        c_indicators = ["#include <stdio.h>", "#include <stdlib.h>", "printf(", "scanf("]
        if any(marker in text for marker in c_indicators):
            return ".c"
        # Default: if it has #include but no clear C++ features
        return ".c"

    # --- JavaScript ---
    js_indicators = ["function ", "const ", "let ", "var ", "console.log", "require(", "module.exports", "=>"]
    if any(marker in text for marker in js_indicators):
        return ".js"

    return None


def determine_language_from_text(text: str) -> str | None:
    """
    Infer the programming language from a natural language description.
    Returns the file extension (e.g., '.py', '.js', '.cpp') or None.
    """
    if not text:
        return None
    
    text = text.lower()
    
    # Python
    if any(kw in text for kw in ["python", "hashlib", "boto3", "flask", "django", "pytest"]):
        return ".py"
        
    # JavaScript
    if any(kw in text for kw in ["javascript", "node.js", "node", "npm", "express", "react", "typescript"]):
        return ".js"
        
    # C++
    if any(kw in text for kw in ["c++", "cpp", "std::", "vector<"]):
        return ".cpp"
        
    # C — match "language: c", "language: c.", " c ", "c " etc.
    if re.search(r'\bc\b', text):
        return ".c"
        
    return None



def truncate_middle(s, limit=MAX_ERR_CHARS):
    """Truncate string to prevent huge prompts."""
    if not s or len(s) <= limit:
        return s
    half = limit // 2
    return s[:half] + "\n...<truncated>...\n" + s[-half:]


def read_json(filepath):
    """Read JSON file and return data."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def write_json(filepath, data):
    """Write data to JSON file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def read_file(filepath):
    """Read text file and return content."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()


def write_file(filepath, content):
    """Write content to a file, creating parent directories as needed."""
    # Make sure parent directory exists
    parent = os.path.dirname(filepath)
    if parent:
        os.makedirs(parent, exist_ok=True)

    # Support text and binary content
    is_bytes = isinstance(content, (bytes, bytearray))
    mode = 'wb' if is_bytes else 'w'
    kwargs = {} if is_bytes else {'encoding': 'utf-8'}
    with open(filepath, mode, **kwargs) as f:
        f.write(content)


def ensure_dir(directory):
    """Create directory if it doesn't exist."""
    os.makedirs(directory, exist_ok=True)


def log_to_file(log_file, level, message, llm_context=None):
    """
    Write to unified log file.
    
    Args:
        log_file: Path to execution.log
        level: INFO, ERROR, WARN, LLM
        message: Log message
        llm_context: Optional dict with {"type": "prompt/response", "call": "...", "content": "..."}
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    
    if llm_context:
        if llm_context["type"] == "prompt":
            log_line = f"[{timestamp}] [LLM] >>> PROMPT ({llm_context['call']}):\n{llm_context['content']}\n\n"
        else:
            log_line = f"[{timestamp}] [LLM] <<< RESPONSE:\n{llm_context['content']}\n\n"
    else:
        log_line = f"[{timestamp}] [{level}] {message}\n"
    
    os.makedirs(os.path.dirname(log_file) if os.path.dirname(log_file) else '.', exist_ok=True)
    
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(log_line)

def format_test_result(test, execution_result, success, language=None):
    """Format test result into standardized structure."""
    exit_code = execution_result.get("exit_code", 1)
    if exit_code == 124:
        outcome = "timeout"
    elif exit_code == 137:
        outcome = "oom"
    elif success:
        outcome = "pass"
    else:
        outcome = "fail"

    test_case = {
        "input": test.get("input"),
        "category": test.get("category", "unknown"),
        "expected_behavior": test.get("expected_behavior",
                                      test.get("expected_behavior/output", "")),
        "expected_output": test.get("expected_output"),
        "cwe": test.get("CWE", ""),
    }
    if test.get("input_file_path"):
        test_case["input_file_path"] = test["input_file_path"]

    return {
        "timestamp": datetime.now().isoformat(),
        "test_case": test_case,
        "observed": {
            "return_value": execution_result.get("return_value"),
            "exception": (execution_result.get("exception") or "")[:1000],
            "printed_output": (execution_result.get("printed_output") or "")[:1000],
            "file_output": (execution_result.get("file_output") or "")[:5000],
            "trace": (execution_result.get("trace") or "")[:1000],
            "coverage": execution_result.get("coverage", ""),
            "http_response": execution_result.get("http_response", ""),
            "outcome": outcome,
        },
        "passed": success,
        "exit_code": exit_code,
        "language": language or "",
    }


def extract_structured_result(llm_response):
    """
    Extract a structured JSON result from an LLM response.

    Supports:
      1. ```json ... ``` fenced JSON
      2. ``` ... ``` fenced JSON without a language tag
      3. RESULT: {...}
      4. bare JSON: {...}
      5. first JSON-looking object in a longer response

    Returns the parsed dict, or None if no valid JSON object is found.
    """
    if not llm_response:
        return None

    text = llm_response.strip()

    # 1. Fenced JSON blocks, with or without an explicit json tag.
    matches = re.findall(
        r'```(?:json)?\s*\n?(.*?)\n?```',
        text,
        re.DOTALL | re.IGNORECASE,
    )
    for candidate in reversed(matches):
        try:
            parsed = json.loads(candidate.strip())
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

    # 2. RESULT: {...}
    result_match = re.search(
        r'RESULT:\s*(\{.*\})\s*$',
        text,
        re.DOTALL | re.IGNORECASE,
    )
    if result_match:
        try:
            parsed = json.loads(result_match.group(1).strip())
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

    # 3. Entire response as bare JSON.
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass

    # 4. Fallback: first JSON-looking object.
    # This is intentionally last because it can be confused by prose containing braces.
    object_match = re.search(r'\{.*\}', text, re.DOTALL)
    if object_match:
        try:
            parsed = json.loads(object_match.group(0).strip())
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

    return None

def extract_script(llm_response):
    """Extract bash script from LLM response."""
    code_block_pattern = r'```(?:bash|sh|python|py)?\s*\n(.*?)\n```'
    matches = re.findall(code_block_pattern, llm_response, re.DOTALL)
    
    if matches:
        return matches[0]
    
    return llm_response.strip()


def detect_language(filepath):
    """Detect language from file extension."""
    if filepath.endswith('.py'):
        return 'py'
    elif filepath.endswith('.c'):
        return 'c'
    elif filepath.endswith(('.cpp', '.cc', '.cxx', '.C')):
        return 'cpp'
    elif filepath.endswith('.h'):
        return 'c'
    elif filepath.endswith(('.hpp', '.hh', '.hxx')):
        return 'cpp'
    elif filepath.endswith('.java'):
        return 'java'
    elif filepath.endswith('.js'):
        return 'js'
    else:
        return 'unknown'
    
# TODO: Remove below (currently used by generate_samples.py)
def log_message(log_path, message):
    """Append a message to the log file with timestamp."""
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")
