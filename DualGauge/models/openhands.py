import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from .base_model import BaseModel

logger = logging.getLogger(__name__)


class _OpenHandsRunError(RuntimeError):
    """RuntimeError that carries the raw event log and stderr for post-failure inspection."""

    def __init__(self, msg: str, event_log: str = "", stderr_log: str = ""):
        super().__init__(msg)
        self.event_log = event_log
        self.stderr_log = stderr_log


class OpenHandsModel(BaseModel):
    """OpenHands CLI-backed generator for agentic sample generation."""

    CODE_FILE_EXTENSIONS = (".py", ".js", ".c", ".cpp", ".cc", ".h", ".hpp")

    def __init__(self, model, api_key=None, temperature=0, max_tokens=None):
        self.model_name = (model or "").strip()
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.rate_limit_delay = 30
        self.openhands_bin = os.getenv("OPENHANDS_BIN", "openhands")
        self.timeout_seconds = int(os.getenv("OPENHANDS_TIMEOUT_SECONDS", "1800"))

        resolved = shutil.which(self.openhands_bin)
        if not resolved:
            raise ValueError(
                f"OpenHands CLI not found on PATH (looked for '{self.openhands_bin}'). "
                "Install OpenHands or set OPENHANDS_BIN."
            )
        self.openhands_bin = resolved

    def _build_command(self, prompt: str) -> list[str]:
        return [
            self.openhands_bin,
            "--headless",
            "--json",
            "--exit-without-confirmation",
            "-t",
            prompt,
        ]

    @staticmethod
    def _normalize_completion(text: str) -> str:
        stripped = (text or "").strip()
        if not stripped:
            return ""
        if "```" in stripped:
            return stripped
        return f"```\n{stripped}\n```"

    @staticmethod
    def _extract_code_blocks(text: str) -> list[str]:
        if not text:
            return []
        return [block.strip() for block in re.findall(r"```(?:\w*\n)?(.*?)```", text, re.DOTALL)]

    def _choose_code_file(self, workdir: str) -> str:
        candidates = []
        for ext in self.CODE_FILE_EXTENSIONS:
            candidates.extend(Path(workdir).rglob(f"*{ext}"))

        candidates = [path for path in candidates if path.is_file() and path.stat().st_size > 0]
        if not candidates:
            return ""

        best = max(candidates, key=lambda p: p.stat().st_mtime)
        return best.read_text(encoding="utf-8")

    @staticmethod
    def _extract_text_fields(payload: dict) -> list[str]:
        texts = []

        def walk(value):
            if isinstance(value, dict):
                for key, child in value.items():
                    if key in {"text", "content", "message", "result", "output"} and isinstance(child, str):
                        texts.append(child)
                    else:
                        walk(child)
            elif isinstance(value, list):
                for item in value:
                    walk(item)

        walk(payload)
        return texts

    _ANSI_RE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]|\r")

    def _extract_text_from_events(self, event_log: str) -> str:
        clean = self._ANSI_RE.sub("", event_log)
        collected = []
        # Events are separated by "--JSON Event--" markers; each chunk is a
        # multi-line JSON object, NOT one object per line.
        _decoder = json.JSONDecoder()
        chunks = re.split(r"--JSON Event--", clean)
        for chunk in chunks:
            chunk = chunk.strip()
            if not chunk:
                continue
            try:
                # Use raw_decode so trailing text like "Agent is working"
                # after the closing } doesn't cause a parse failure.
                payload, _ = _decoder.raw_decode(chunk)
                # Only extract text from agent-sourced events; user events
                # contain the prompt which pollutes code extraction.
                if payload.get("source") == "user":
                    continue
                collected.extend(self._extract_text_fields(payload))
            except (json.JSONDecodeError, ValueError):
                # Fall back to extracting any code blocks directly from raw text
                collected.extend(self._extract_code_blocks(chunk))

        joined = "\n".join(piece for piece in collected if piece).strip()
        if not joined:
            return ""

        code_blocks = self._extract_code_blocks(joined)
        if code_blocks:
            return "\n\n".join(code_blocks)
        return joined

    _CHEAP_CONDENSER = {
        "anthropic": "anthropic/claude-haiku-4-5-20251001",
        "openai": "openai/gpt-4o-mini",
    }

    def _api_key_for(self, prefix: str) -> str:
        if prefix == "anthropic":
            return os.environ.get("ANTHROPIC_API_KEY", "")
        if prefix in ("openai", "gpt"):
            return os.environ.get("OPENAI_API_KEY", "")
        return ""

    def _write_settings(self, settings_dir: str) -> None:
        """Write a per-run agent_settings.json so main LLM and condenser use the same provider."""
        base = os.path.expanduser("~/.openhands/agent_settings.json")
        with open(base) as f:
            settings = json.load(f)

        if self.model_name:
            prefix = self.model_name.split("/")[0].lower()
            api_key = self._api_key_for(prefix)
            condenser_model = self._CHEAP_CONDENSER.get(prefix, self.model_name)

            settings["llm"]["model"] = self.model_name
            settings["llm"]["api_key"] = api_key
            settings["llm"]["base_url"] = None

            if "condenser" in settings and "llm" in settings["condenser"]:
                settings["condenser"]["llm"]["model"] = condenser_model
                settings["condenser"]["llm"]["api_key"] = api_key
                settings["condenser"]["llm"]["base_url"] = None

        os.makedirs(settings_dir, exist_ok=True)
        with open(os.path.join(settings_dir, "agent_settings.json"), "w") as f:
            json.dump(settings, f)

    def _generate_internal(self, prompt: str) -> dict:
        with tempfile.TemporaryDirectory(prefix="dualgauge_openhands_") as tmpdir:
            env = os.environ.copy()
            settings_dir = os.path.join(tmpdir, ".openhands_settings")
            self._write_settings(settings_dir)
            env["OPENHANDS_PERSISTENCE_DIR"] = settings_dir
            env["OPENHANDS_CONVERSATIONS_DIR"] = os.path.join(settings_dir, "conversations")
            # Tell Rich/Textual that this is a headless-compatible terminal so
            # it doesn't send SIGINT to itself (exit -2) on non-TTY stderr.
            env["TTY_INTERACTIVE"] = "1"
            env["TTY_COMPATIBLE"] = "1"
            command = self._build_command(prompt)

            proc = subprocess.run(
                command,
                text=True,
                capture_output=True,
                cwd=tmpdir,
                timeout=self.timeout_seconds,
                env=env,
            )

            event_log = (proc.stdout or "").strip()
            stderr_log = (proc.stderr or "").strip()

            # Exit code -2 means killed by SIGINT (Textual self-signal on bad TTY).
            # If events were already emitted, attempt recovery rather than hard-failing.
            if proc.returncode != 0 and proc.returncode != -2:
                error_text = (stderr_log or event_log or "").strip()
                raise _OpenHandsRunError(
                    f"OpenHands CLI failed with exit code {proc.returncode}: {error_text[:500]}",
                    event_log=event_log,
                    stderr_log=stderr_log,
                )

            if proc.returncode == -2 and not event_log:
                error_text = (stderr_log or "").strip()
                raise _OpenHandsRunError(
                    f"OpenHands CLI killed by SIGINT with no output: {error_text[:500]}",
                    event_log=event_log,
                    stderr_log=stderr_log,
                )

            code_from_files = self._choose_code_file(tmpdir)
            text_from_events = self._extract_text_from_events(event_log)

            raw_content = code_from_files or text_from_events
            if not raw_content:
                raise _OpenHandsRunError(
                    "OpenHands headless run returned no recoverable code output",
                    event_log=event_log,
                    stderr_log=stderr_log,
                )

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
                    "OpenHands CLI error (model=%s, trial=%d): %s. Retrying after %ds...",
                    self.model_name or "default",
                    trial,
                    e,
                    self.rate_limit_delay,
                )
                time.sleep(self.rate_limit_delay)
                return self.generate(prompt, trial=trial + 1)
            logger.error("OpenHands CLI error after 3 trials (model=%s): %s", self.model_name or "default", e)
            return "ERROR"

    def generate_with_metadata(self, prompt, trial=0):
        try:
            result = self._generate_internal(prompt)
            result.setdefault("reasoning", None)
            return result
        except Exception as e:
            if trial < 3:
                logger.warning(
                    "OpenHands CLI error (model=%s, trial=%d): %s. Retrying after %ds...",
                    self.model_name or "default",
                    trial,
                    e,
                    self.rate_limit_delay,
                )
                time.sleep(self.rate_limit_delay)
                return self.generate_with_metadata(prompt, trial=trial + 1)
            logger.error("OpenHands CLI error after 3 trials (model=%s): %s", self.model_name or "default", e)
            return {
                "content": "ERROR",
                "raw_content": "",
                "reasoning": None,
                "events": getattr(e, "event_log", ""),
                "stderr": getattr(e, "stderr_log", ""),
                "error": str(e),
            }
