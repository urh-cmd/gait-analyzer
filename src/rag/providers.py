"""
Haile - LLM Provider Clients
=============================
Support for OpenAI, Alibaba Cloud (Qwen), and Anthropic.
"""

import os
from abc import ABC, abstractmethod
from typing import Optional, List, Dict
import json


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or self._get_default_api_key()
    
    @abstractmethod
    def _get_default_api_key(self) -> Optional[str]:
        """Get API key from environment."""
        pass
    
    @abstractmethod
    def generate(self, prompt: str, system: str = "", **kwargs) -> str:
        """Generate text from prompt."""
        pass
    
    @abstractmethod
    def generate_structured(self, prompt: str, schema: Dict, system: str = "") -> Dict:
        """Generate structured output."""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.model = model
        super().__init__(api_key)
        self._client = None
    
    def _get_default_api_key(self) -> Optional[str]:
        return os.environ.get("OPENAI_API_KEY")
    
    def _get_client(self):
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError("Please install openai: pip install openai")
        return self._client
    
    def generate(self, prompt: str, system: str = "", **kwargs) -> str:
        client = self._get_client()
        
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            **kwargs
        )
        
        return response.choices[0].message.content
    
    def generate_structured(self, prompt: str, schema: Dict, system: str = "") -> Dict:
        client = self._get_client()
        
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)


class QwenProvider(LLMProvider):
    """Alibaba Cloud Qwen provider (DashScope)."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "qwen-max"):
        self.model = model
        super().__init__(api_key)
        self._initialized = False
    
    def _get_default_api_key(self) -> Optional[str]:
        return os.environ.get("DASHSCOPE_API_KEY") or os.environ.get("ALIBABA_API_KEY")
    
    def _init_sdk(self):
        if not self._initialized:
            try:
                import dashscope
                dashscope.api_key = self.api_key
                self._initialized = True
            except ImportError:
                raise ImportError("Please install dashscope: pip install dashscope")
    
    def generate(self, prompt: str, system: str = "", **kwargs) -> str:
        self._init_sdk()
        import dashscope
        from dashscope import Generation
        
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        response = Generation.call(
            model=self.model,
            messages=messages,
            result_format='message'
        )
        
        if response.status_code == 200:
            return response.output.choices[0].message.content
        else:
            raise Exception(f"Qwen API error: {response.code} - {response.message}")
    
    def generate_structured(self, prompt: str, schema: Dict, system: str = "") -> Dict:
        # Qwen supports JSON mode
        self._init_sdk()
        import dashscope
        from dashscope import Generation
        
        system_prompt = system + "\n\nAntworte NUR mit validem JSON im folgenden Format:\n" + json.dumps(schema, indent=2)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt + "\n\nAntworte ausschließlich mit JSON, ohne zusätzlichen Text."}
        ]
        
        response = Generation.call(
            model=self.model,
            messages=messages,
            result_format='message'
        )
        
        if response.status_code == 200:
            content = response.output.choices[0].message.content
            # Clean up potential markdown code blocks
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            return json.loads(content.strip())
        else:
            raise Exception(f"Qwen API error: {response.code} - {response.message}")


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-haiku-20240307"):
        self.model = model
        super().__init__(api_key)
        self._client = None
    
    def _get_default_api_key(self) -> Optional[str]:
        return os.environ.get("ANTHROPIC_API_KEY")
    
    def _get_client(self):
        if self._client is None:
            try:
                from anthropic import Anthropic
                self._client = Anthropic(api_key=self.api_key)
            except ImportError:
                raise ImportError("Please install anthropic: pip install anthropic")
        return self._client
    
    def generate(self, prompt: str, system: str = "", **kwargs) -> str:
        client = self._get_client()
        
        message = client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        )
        
        return message.content[0].text
    
    def generate_structured(self, prompt: str, schema: Dict, system: str = "") -> Dict:
        client = self._get_client()
        
        system_prompt = system + "\n\nAntworte NUR mit validem JSON im folgenden Format:\n" + json.dumps(schema, indent=2)
        
        message = client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system_prompt,
            messages=[{
                "role": "user", 
                "content": prompt + "\n\nAntworte ausschließlich mit JSON, ohne zusätzlichen Text oder Markdown."
            }]
        )
        
        content = message.content[0].text
        # Clean up potential markdown code blocks
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        
        return json.loads(content.strip())


def get_provider(name: str, api_key: Optional[str] = None) -> LLMProvider:
    """Factory function to get provider by name."""
    providers = {
        "openai": OpenAIProvider,
        "qwen": QwenProvider,
        "alibaba": QwenProvider,
        "anthropic": AnthropicProvider,
        "claude": AnthropicProvider,
    }
    
    if name.lower() not in providers:
        raise ValueError(f"Unknown provider: {name}. Available: {list(providers.keys())}")
    
    return providers[name.lower()](api_key=api_key)
