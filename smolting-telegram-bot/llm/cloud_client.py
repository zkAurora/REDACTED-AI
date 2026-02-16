# smolting-telegram-bot/llm/cloud_client.py
import os
import asyncio
import aiohttp
import json
from typing import Optional, Dict, Any

class CloudLLMClient:
    """Cloud LLM client supporting multiple providers"""
    
    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "openai")  # openai, anthropic, together
        self.api_key = self._get_api_key()
        self.base_url = self._get_base_url()
        
    def _get_api_key(self) -> str:
        """Get API key based on provider"""
        keys = {
            "openai": os.getenv("OPENAI_API_KEY"),
            "anthropic": os.getenv("ANTHROPIC_API_KEY"),
            "together": os.getenv("TOGETHER_API_KEY")
        }
        return keys.get(self.provider, "")
    
    def _get_base_url(self) -> str:
        """Get base URL for provider"""
        urls = {
            "openai": "https://api.openai.com/v1",
            "anthropic": "https://api.anthropic.com/v1",
            "together": "https://api.together.xyz/v1"
        }
        return urls.get(self.provider, "")
    
    async def chat_completion(self, messages: list, model: str = None) -> str:
        """Chat completion with cloud LLM"""
        
        if self.provider == "openai":
            return await self._openai_completion(messages, model)
        elif self.provider == "anthropic":
            return await self._anthropic_completion(messages, model)
        elif self.provider == "together":
            return await self._together_completion(messages, model)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    async def _openai_completion(self, messages: list, model: str = None) -> str:
        """OpenAI GPT completion"""
        model = model or "gpt-3.5-turbo"
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers
            ) as response:
                result = await response.json()
                return result["choices"][0]["message"]["content"]
    
    async def _anthropic_completion(self, messages: list, model: str = None) -> str:
        """Anthropic Claude completion"""
        model = model or "claude-3-haiku-20240307"
        
        # Convert messages to Claude format
        system_msg = ""
        user_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            elif msg["role"] == "user":
                user_messages.append({"role": "user", "content": msg["content"]})
            elif msg["role"] == "assistant":
                user_messages.append({"role": "assistant", "content": msg["content"]})
        
        payload = {
            "model": model,
            "max_tokens": 1000,
            "system": system_msg,
            "messages": user_messages
        }
        
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/messages",
                json=payload,
                headers=headers
            ) as response:
                result = await response.json()
                return result["content"][0]["text"]
    
    async def _together_completion(self, messages: list, model: str = None) -> str:
        """Together AI completion (mix of open source models)"""
        model = model or "Qwen/Qwen2.5-7B-Instruct-Turbo"
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers
            ) as response:
                result = await response.json()
                return result["choices"][0]["message"]["content"]
