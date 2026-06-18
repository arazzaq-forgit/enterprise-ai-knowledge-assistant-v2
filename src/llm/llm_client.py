"""
LLM Client for Enterprise AI Knowledge Assistant.
Connects to Ollama and generates answers with streaming.
"""

import requests
import json
from typing import Generator, List, Dict, Any, Optional
from src.utils.logger import get_llm_logger

logger = get_llm_logger()


class LLMClient:
    """
    Connects to Ollama and generates AI responses.

    Features:
        ✅ Regular response (wait for full answer)
        ✅ Streaming response (word by word like ChatGPT)
        ✅ Checks if model is available
        ✅ Handles connection errors gracefully
        ✅ Tracks token usage
    """

    def __init__(self,
                 model_name: str = "llama3.2:3b",
                 base_url: str = "http://localhost:11434",
                 temperature: float = 0.1,
                 max_tokens: int = 2048):
        """
        Args:
            model_name:  Ollama model to use
            base_url:    Ollama server URL
            temperature: 0.0=focused, 1.0=creative
            max_tokens:  Max response length
        """
        self.model_name  = model_name
        self.base_url    = base_url
        self.temperature = temperature
        self.max_tokens  = max_tokens
        self.chat_url    = f"{base_url}/api/chat"
        self.generate_url = f"{base_url}/api/generate"

        logger.info(f"LLM Client ready: {model_name}")

    def generate(self,
                 prompt: str,
                 system_prompt: Optional[str] = None
                 ) -> str:
        """
        Generate a complete response (no streaming).

        Args:
            prompt:        User question with context
            system_prompt: Instructions for the AI

        Returns:
            Complete response as string
        """
        messages = []

        if system_prompt:
            messages.append({
                "role":    "system",
                "content": system_prompt
            })

        messages.append({
            "role":    "user",
            "content": prompt
        })

        try:
            response = requests.post(
                self.chat_url,
                json={
                    "model":    self.model_name,
                    "messages": messages,
                    "stream":   False,
                    "options": {
                        "temperature": self.temperature,
                        "num_predict": self.max_tokens,
                    }
                },
                timeout=120
            )
            response.raise_for_status()
            result = response.json()
            answer = result["message"]["content"]
            logger.info(f"Generated response: "
                       f"{len(answer)} characters")
            return answer

        except requests.exceptions.ConnectionError:
            logger.error("Ollama not running!")
            raise ConnectionError(
                "❌ Ollama is not running!\n"
                "Please run: ollama serve"
            )
        except Exception as e:
            logger.error(f"Generation failed: {str(e)}")
            raise

    def generate_stream(self,
                        prompt: str,
                        system_prompt: Optional[str] = None
                        ) -> Generator[str, None, None]:
        """
        Generate streaming response word by word.
        Like ChatGPT typing effect!

        Args:
            prompt:        User question with context
            system_prompt: Instructions for the AI

        Yields:
            Text chunks as they are generated
        """
        messages = []

        if system_prompt:
            messages.append({
                "role":    "system",
                "content": system_prompt
            })

        messages.append({
            "role":    "user",
            "content": prompt
        })

        try:
            response = requests.post(
                self.chat_url,
                json={
                    "model":    self.model_name,
                    "messages": messages,
                    "stream":   True,
                    "options": {
                        "temperature": self.temperature,
                        "num_predict": self.max_tokens,
                    }
                },
                stream=True,
                timeout=120
            )
            response.raise_for_status()

            # ── Stream chunks as they arrive ─────────────────────
            for line in response.iter_lines():
                if line:
                    try:
                        chunk = json.loads(line.decode("utf-8"))
                        if not chunk.get("done", False):
                            token = chunk.get(
                                "message", {}
                            ).get("content", "")
                            if token:
                                yield token
                    except json.JSONDecodeError:
                        continue

        except requests.exceptions.ConnectionError:
            logger.error("Ollama not running!")
            yield "❌ Ollama is not running! Please run: ollama serve"
        except Exception as e:
            logger.error(f"Streaming failed: {str(e)}")
            yield f"❌ Error: {str(e)}"

    def is_available(self) -> bool:
        """Check if Ollama and model are running."""
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            if response.status_code == 200:
                models = response.json().get("models", [])
                names  = [m["name"] for m in models]
                available = any(
                    self.model_name in n for n in names
                )
                if available:
                    logger.info(
                        f"✅ {self.model_name} is available"
                    )
                else:
                    logger.warning(
                        f"⚠️ {self.model_name} not found!\n"
                        f"Run: ollama pull {self.model_name}"
                    )
                return available
        except Exception:
            logger.error("❌ Ollama server not reachable")
            return False

    def get_available_models(self) -> List[str]:
        """Get list of all downloaded Ollama models."""
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            if response.status_code == 200:
                models = response.json().get("models", [])
                return [m["name"] for m in models]
        except Exception:
            pass
        return []