import json
import math
import os
import re

import requests
import streamlit as st


GROQ_MODEL = "openai/gpt-oss-120b"
GEMINI_EMBEDDING_MODEL = "gemini-embedding-001"
GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"
GEMINI_BATCH_EMBED_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_EMBEDDING_MODEL}:batchEmbedContents"
)


def _get_secret(name):
    value = os.getenv(name)
    if not value:
        try:
            value = st.secrets.get(name)
        except FileNotFoundError:
            value = None
    if not value:
        raise RuntimeError(
            f"{name} is not configured. Set it as an environment variable "
            "or in .streamlit/secrets.toml."
        )
    return value


def groq_chat(messages, temperature=0.2):
    response = requests.post(
        GROQ_CHAT_URL,
        headers={
            "Authorization": f"Bearer {_get_secret('GROQ_API_KEY')}",
            "Content-Type": "application/json",
        },
        json={
            "model": GROQ_MODEL,
            "messages": messages,
            "temperature": temperature,
        },
        timeout=60,
    )
    if not response.ok:
        raise RuntimeError(f"Groq request failed (HTTP {response.status_code}).")
    try:
        payload = response.json()
        return payload["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError) as error:
        raise RuntimeError("Groq returned an unexpected response format.") from error


def groq_chat_json(messages, temperature=0.2):
    content = groq_chat(messages, temperature=temperature).strip()
    content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content, flags=re.IGNORECASE)
    try:
        result = json.loads(content)
    except json.JSONDecodeError:
        start = content.find("{")
        end = content.rfind("}")
        if start < 0 or end < start:
            raise RuntimeError("The AI response did not contain valid JSON.")
        try:
            result = json.loads(content[start : end + 1])
        except json.JSONDecodeError as error:
            raise RuntimeError("The AI response did not contain valid JSON.") from error
    if not isinstance(result, dict):
        raise RuntimeError("The AI response must be a JSON object.")
    return result


def gemini_embeddings(texts, task_type):
    if not texts:
        return []

    embeddings = []
    api_key = _get_secret("GEMINI_API_KEY")
    for offset in range(0, len(texts), 80):
        batch = texts[offset : offset + 80]
        response = requests.post(
            GEMINI_BATCH_EMBED_URL,
            params={"key": api_key},
            json={
                "requests": [
                    {
                        "model": f"models/{GEMINI_EMBEDDING_MODEL}",
                        "content": {"parts": [{"text": text[:12000]}]},
                        "taskType": task_type,
                        "outputDimensionality": 768,
                    }
                    for text in batch
                ]
            },
            timeout=60,
        )
        if not response.ok:
            raise RuntimeError(
                f"Gemini embedding request failed (HTTP {response.status_code}). "
                "Check that the Gemini API is enabled for your key."
            )
        try:
            payload = response.json()
            batch_embeddings = [
                item["values"] for item in payload["embeddings"]
            ]
        except (ValueError, KeyError, TypeError) as error:
            raise RuntimeError(
                "Gemini returned an unexpected embedding response format."
            ) from error
        if len(batch_embeddings) != len(batch):
            raise RuntimeError("Gemini returned an incomplete embedding batch.")
        embeddings.extend(batch_embeddings)
    return embeddings


def cosine_similarity(left, right):
    if len(left) != len(right):
        raise ValueError("Embedding vectors must have the same dimensions.")
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if not left_norm or not right_norm:
        return 0.0
    return sum(a * b for a, b in zip(left, right)) / (left_norm * right_norm)
