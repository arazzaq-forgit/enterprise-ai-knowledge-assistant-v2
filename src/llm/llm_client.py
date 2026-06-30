import os
from groq import Groq
from src.utils.logger import setup_logger

logger = setup_logger("LLMClient")

class LLMClient:
    def __init__(self, model_name: str = "llama3-8b-8192", base_url: str = None, temperature: float = 0.2, max_tokens: int = 1024, **kwargs):
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        api_key = os.environ.get("GROQ_API_KEY", "")
        self.client = Groq(api_key=api_key)
        logger.info(f"LLM ready: Groq/{model_name}")

    def generate_stream(self, prompt: str, system_prompt: str = ""):
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                stream=True,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            for chunk in response:
                token = chunk.choices[0].delta.content
                if token:
                    yield token
        except Exception as e:
            logger.error(f"Groq stream failed: {str(e)}")
            raise

    def generate(self, prompt: str, system_prompt: str = ""):
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                stream=False,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq generate failed: {str(e)}")
            raise

    def is_available(self) -> bool:
        try:
            self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=5,
            )
            return True
        except Exception:
            return False
