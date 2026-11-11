import http.client
import json
import os

import streamlit as st


def _get_api_key():
    api_key = os.getenv("JOOBLE_API_KEY")
    if not api_key:
        try:
            api_key = st.secrets.get("JOOBLE_API_KEY")
        except FileNotFoundError:
            api_key = None

    if not api_key:
        raise RuntimeError(
            "Jooble API key is not configured. Set JOOBLE_API_KEY in "
            "the environment or in .streamlit/secrets.toml."
        )
    return api_key


def fetch_jobs(keywords="developer", location="India", page=1):
    api_key = _get_api_key()
    connection = http.client.HTTPSConnection("jooble.org", timeout=20)
    body = json.dumps({
        "keywords": keywords,
        "location": location,
        "page": page
    })

    try:
        connection.request(
            "POST",
            f"/api/{api_key}",
            body,
            {"Content-Type": "application/json"},
        )
        response = connection.getresponse()
        data = response.read().decode("utf-8")

        if response.status < 200 or response.status >= 300:
            raise RuntimeError(
                f"Jooble API returned HTTP {response.status} "
                f"({response.reason}). Check that your API key is valid."
            )

        try:
            parsed = json.loads(data)
        except json.JSONDecodeError as error:
            raise RuntimeError(
                f"Jooble returned an invalid response (HTTP {response.status}). "
                "Check your API key and try again."
            ) from error

        if not isinstance(parsed, dict) or not isinstance(parsed.get("jobs", []), list):
            raise RuntimeError("Jooble returned an unexpected response format.")

        return parsed.get("jobs", [])
    finally:
        connection.close()