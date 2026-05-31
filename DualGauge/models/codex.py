import json
import logging
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from .base_model import BaseModel

logger = logging.getLogger(__name__)


class CodexModel(BaseModel):
    """Codex CLI-backed generator for agentic sample generation."""

    def __init__(self, model, api_key=None, temperature=0, max_tokens=None):
        self.model_name = (model or "").strip()
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.rate_limit_delay = 30
        self.codex_bin = os.getenv("CODEX_BIN", "codex")
        self.timeout_seconds = int(os.getenv("CODEX_TIMEOUT_SECONDS", "900"))
        self.repo_root = Path(__file__).resolve().parents[2]

        resolved = shutil.which(self.codex_bin)
        if not resolved:
            raise ValueError(
                f"Codex CLI not found on PATH (looked for '{self.codex_bin}'). "
                "Install Codex or set CODEX_BIN."
            )
        self.codex_bin = resolved

    def _build_command(self, schema_path: str, output_path: str) -> list[str]:
        cmd = [
            self.codex_bin,
            "--ask-for-approval",
            "never",
            "exec",
            "--cd",
            str(self.repo_root),
            "--sandbox",
            "read-only",
            "--skip-git-repo-check",
            "--ephemeral",
            "--ignore-rules",
            "--color",
            "never",
            "--json",
            "--output-schema",
            schema_path,
            "--output-last-message",
            output_path,
            "-",
        ]
        if self.model_name and self.model_name.lower() not in {"default", "codex"}:
            cmd.extend(["--model", self.model_name])
        return cmd

    @staticmethod
    def _schema() -> dict:
        return {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Complete source code for the requested benchmark solution.",
                }
            },
            "required": ["code"],
        }

    @staticmethod
    def _wrap_code(code: str) -> str:
        stripped = (code or "").strip()
        return f"```\n{stripped}\n```" if stripped else ""

    def _generate_internal(self, prompt: str) -> dict:
        with tempfile.TemporaryDirectory(prefix="dualgauge_codex_") as tmpdir:
            schema_path = os.path.join(tmpdir, "schema.json")
            output_path = os.path.join(tmpdir, "response.txt")

            with open(schema_path, "w", encoding="utf-8") as f:
                json.dump(self._schema(), f)

            proc = subprocess.run(
                self._build_command(schema_path, output_path),
                input=prompt,
                text=True,
                capture_output=True,
                cwd=self.repo_root,
                timeout=self.timeout_seconds,
            )

            raw_content = ""
            if os.path.exists(output_path):
                with open(output_path, "r", encoding="utf-8") as f:
                    raw_content = f.read().strip()
            event_log = (proc.stdout or "").strip()
            stderr_log = (proc.stderr or "").strip()

            if proc.returncode != 0:
                error_text = (stderr_log or event_log or raw_content or "").strip()
                raise RuntimeError(
                    f"codex exec failed with exit code {proc.returncode}: {error_text[:500]}"
                )

            if not raw_content:
                raise RuntimeError("codex exec returned an empty final message")

            try:
                payload = json.loads(raw_content)
                code = payload.get("code", "")
            except json.JSONDecodeError:
                payload = None
                code = raw_content

            return {
                "content": self._wrap_code(code),
                "raw_content": raw_content if payload is not None else code,
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
                    "Codex CLI error (model=%s, trial=%d): %s. Retrying after %ds...",
                    self.model_name or "default",
                    trial,
                    e,
                    self.rate_limit_delay,
                )
                time.sleep(self.rate_limit_delay)
                return self.generate(prompt, trial=trial + 1)
            logger.error("Codex CLI error after 3 trials (model=%s): %s", self.model_name or "default", e)
            return "ERROR"

    def generate_with_metadata(self, prompt, trial=0):
        try:
            result = self._generate_internal(prompt)
            result.setdefault("reasoning", None)
            return result
        except Exception as e:
            if trial < 3:
                logger.warning(
                    "Codex CLI error (model=%s, trial=%d): %s. Retrying after %ds...",
                    self.model_name or "default",
                    trial,
                    e,
                    self.rate_limit_delay,
                )
                time.sleep(self.rate_limit_delay)
                return self.generate_with_metadata(prompt, trial=trial + 1)
            logger.error("Codex CLI error after 3 trials (model=%s): %s", self.model_name or "default", e)
            return {
                "content": "ERROR",
                "raw_content": "",
                "reasoning": None,
                "events": "",
                "stderr": "",
                "error": str(e),
            }
