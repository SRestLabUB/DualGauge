import json
import logging
import os
import shutil
import subprocess
import time
from pathlib import Path

from .base_model import BaseModel

logger = logging.getLogger(__name__)


class ClaudeCodeModel(BaseModel):
    """Claude Code CLI-backed generator for agentic sample generation."""

    def __init__(self, model, api_key=None, temperature=0, max_tokens=None):
        self.model_name = (model or "").strip()
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.rate_limit_delay = 30
        self.claude_bin = os.getenv("CLAUDE_BIN", "claude")
        self.timeout_seconds = int(os.getenv("CLAUDE_CODE_TIMEOUT_SECONDS", "900"))
        self.repo_root = Path(__file__).resolve().parents[2]

        resolved = shutil.which(self.claude_bin)
        if not resolved:
            raise ValueError(
                f"Claude Code CLI not found on PATH (looked for '{self.claude_bin}'). "
                "Install Claude Code or set CLAUDE_BIN."
            )
        self.claude_bin = resolved

    def _build_command(self) -> list[str]:
        cmd = [
            self.claude_bin,
            "-p",
            "--permission-mode",
            "bypassPermissions",
            "--output-format",
            "stream-json",
            "--verbose",
            "--include-partial-messages",
            "--include-hook-events",
        ]
        if self.model_name and self.model_name.lower() not in {"default", "claudecode", "claudecode"}:
            cmd.extend(["--model", self.model_name])
        return cmd

    @staticmethod
    def _normalize_completion(text: str) -> str:
        stripped = (text or "").strip()
        if not stripped:
            return ""
        if "```" in stripped:
            return stripped
        return f"```\n{stripped}\n```"

    @staticmethod
    def _extract_text_from_event(event: dict) -> str:
        if not isinstance(event, dict):
            return ""

        line_type = event.get("type")
        if line_type == "stream_event":
            delta = event.get("event", {}).get("delta", {})
            if isinstance(delta, dict) and delta.get("type") == "text_delta":
                return delta.get("text", "")

        result = event.get("result")
        if isinstance(result, str):
            return result

        message = event.get("message")
        if isinstance(message, dict):
            content = message.get("content")
            if isinstance(content, list):
                pieces = []
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        pieces.append(block.get("text", ""))
                return "".join(pieces)

        return ""

    def _generate_internal(self, prompt: str) -> dict:
        proc = subprocess.run(
            self._build_command(),
            input=prompt,
            text=True,
            capture_output=True,
            cwd=self.repo_root,
            timeout=self.timeout_seconds,
        )

        event_log = (proc.stdout or "").strip()
        stderr_log = (proc.stderr or "").strip()

        if proc.returncode != 0:
            error_text = (stderr_log or event_log or "").strip()
            raise RuntimeError(
                f"claude -p failed with exit code {proc.returncode}: {error_text[:500]}"
            )

        final_result = ""
        stream_text_parts = []
        for line in proc.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            extracted = self._extract_text_from_event(payload)
            if extracted:
                if payload.get("type") == "stream_event":
                    stream_text_parts.append(extracted)
                else:
                    final_result = extracted

        raw_content = final_result or "".join(stream_text_parts).strip()
        if not raw_content:
            raise RuntimeError("claude -p returned an empty final response")

        return {
            "content": self._normalize_completion(raw_content),
            "raw_content": raw_content,
            "reasoning": None,
            "events": event_log,
            "stderr": stderr_log,
        }

    def generate(self, prompt, trial=0):
        try:
            return self._generate_internal(prompt)["content"]
        except Exception as e:
            if trial < 3:
                logger.warning(
                    "Claude Code CLI error (model=%s, trial=%d): %s. Retrying after %ds...",
                    self.model_name or "default",
                    trial,
                    e,
                    self.rate_limit_delay,
                )
                time.sleep(self.rate_limit_delay)
                return self.generate(prompt, trial=trial + 1)
            logger.error("Claude Code CLI error after 3 trials (model=%s): %s", self.model_name or "default", e)
            return "ERROR"

    def generate_with_metadata(self, prompt, trial=0):
        try:
            result = self._generate_internal(prompt)
            result.setdefault("reasoning", None)
            return result
        except Exception as e:
            if trial < 3:
                logger.warning(
                    "Claude Code CLI error (model=%s, trial=%d): %s. Retrying after %ds...",
                    self.model_name or "default",
                    trial,
                    e,
                    self.rate_limit_delay,
                )
                time.sleep(self.rate_limit_delay)
                return self.generate_with_metadata(prompt, trial=trial + 1)
            logger.error("Claude Code CLI error after 3 trials (model=%s): %s", self.model_name or "default", e)
            return {
                "content": "ERROR",
                "raw_content": "",
                "reasoning": None,
                "events": "",
                "stderr": "",
                "error": str(e),
            }
