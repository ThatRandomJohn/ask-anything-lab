"""TRIBE v2 API client — calls Modal GPU endpoint for cortical predictions.

Falls back to keyword-based activation when the endpoint is unavailable.
"""
from __future__ import annotations

import os
import time

import requests

from data.brain_data import generate_activation_from_response


def get_brain_activation(response_text: str) -> dict:
    """Get brain activation for the given AI response text.

    Tries the TRIBE v2 Modal endpoint first. Falls back to keyword-based
    activation if TRIBE_ENDPOINT_URL is not set or the request fails.

    Returns: {"activations": [20484 floats], "roi_scores": {...}, "status": str}
    """
    url = os.environ.get("TRIBE_ENDPOINT_URL")
    if not url:
        print("[tribe] No TRIBE_ENDPOINT_URL set — using keyword fallback", flush=True)
        return generate_activation_from_response(response_text)

    try:
        print(f"[tribe] Calling TRIBE v2 endpoint...", flush=True)
        t0 = time.time()
        resp = requests.post(
            url,
            json={"text": response_text},
            headers={"Content-Type": "application/json"},
            timeout=60,  # TRIBE v2 cold start can take ~30-60s
        )
        resp.raise_for_status()
        data = resp.json()
        elapsed = time.time() - t0
        print(f"[tribe] TRIBE v2 response in {elapsed:.1f}s — status: {data.get('status')}", flush=True)

        # Validate response shape
        if data.get("status") == "error":
            print(f"[tribe] Endpoint returned error: {data.get('error')}", flush=True)
            return generate_activation_from_response(response_text)

        if "activations" not in data or len(data["activations"]) != 20484:
            print(f"[tribe] Invalid response shape — falling back", flush=True)
            return generate_activation_from_response(response_text)

        return data

    except requests.exceptions.Timeout:
        print("[tribe] Request timed out — using keyword fallback", flush=True)
        return generate_activation_from_response(response_text)
    except Exception as e:
        print(f"[tribe] Request failed: {e} — using keyword fallback", flush=True)
        return generate_activation_from_response(response_text)
