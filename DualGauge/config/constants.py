import os

OPENAI_API_KEY    = os.getenv('OPENAI_API_KEY', '')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
GEMINI_KEY        = os.getenv('GEMINI_API_KEY', '')
DEEPSEEK_KEY      = os.getenv('DEEPSEEK_API_KEY', '')
GROK_KEY          = os.getenv('GROK_API_KEY', '')
VLLM_BASE_URL     = os.getenv('VLLM_BASE_URL', '')       # e.g. http://your-server:8000/v1
VLLM_API_KEY      = os.getenv('VLLM_API_KEY', 'token-abc123')  # vLLM accepts any non-empty key
NUM_OF_WORKERS = 10

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BENCHMARKS_DIR = os.path.join(BASE_DIR, "DualGauge-Bench")
EXPERIMENTS_DIR = os.path.join(BASE_DIR, "BenchmarkingExperiments")

DEFAULT_AGENT_MODEL = "gpt-5-nano"
DEFAULT_WORKERS = 10
DEFAULT_MAX_RETRIES = 3
DEFAULT_DOCKER_IMAGE_PYTHON = "python-preloaded:3.11"
DEFAULT_DOCKER_IMAGE_C = "python-preloaded:3.11"
MAX_ERR_CHARS = 500
