from __future__ import annotations

from typing import Sequence

from agent_framework import AgentMiddleware
from agent_framework.openai import OpenAIChatClient, OpenAIChatCompletionClient

from .config import settings


AgentClient = OpenAIChatClient | OpenAIChatCompletionClient


def get_agent_client() -> AgentClient:
    client_kwargs = {
        "base_url": settings.openai_base_url,
        "model": settings.openai_model,
        "api_key": settings.openai_api_key,
    }

    if settings.openai_api_kind in {"chat_completions", "chat-completions", "chat", "completions"}:
        return OpenAIChatCompletionClient(**client_kwargs)
    if settings.openai_api_kind in {"responses", "response"}:
        return OpenAIChatClient(**client_kwargs)
    raise ValueError("Unsupported OPENAI_API_KIND. Use 'chat_completions' or 'responses'.")


def create_agent(
    name: str,
    instructions: str,
    middleware: Sequence[AgentMiddleware] | None = None,
    client: AgentClient | None = None,
    tools: Sequence[object] | None = None,
):
    active_client = client or get_agent_client()
    return active_client.as_agent(
        name=name,
        instructions=instructions,
        tools=tools,
        middleware=list(middleware or []),
    )

