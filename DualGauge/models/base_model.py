class BaseModel():
    """Abstract base class for all model wrappers."""

    def __init__(self, model, api_key, temperature=0):
        raise NotImplementedError

    def generate(self, prompt):
        raise NotImplementedError

    def generate_with_web_search(self, prompt, max_searches=3):
        raise NotImplementedError
