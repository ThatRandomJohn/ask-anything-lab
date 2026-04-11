"""Supabase client for anonymized TEDx study data.

Falls back to stdout logging when SUPABASE_URL / SUPABASE_ANON_KEY are missing.
"""
import os

_client = None
_tried = False


def _get_client():
    global _client, _tried
    if _tried:
        return _client
    _tried = True
    url = os.environ.get("SUPABASE_URL")
    # Prefer the service_role key server-side so RLS doesn't block anonymous study inserts.
    # Falls back to anon key if service key is unavailable.
    key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_ANON_KEY")
    key_kind = "service_role" if os.environ.get("SUPABASE_SERVICE_KEY") else "anon"
    if not url or not key:
        print("[supabase] No credentials set \u2014 study data will log to stdout only.")
        return None
    try:
        from supabase import create_client
        _client = create_client(url, key)
        print(f"[supabase] Client initialized ({key_kind}).")
        return _client
    except Exception as e:
        print(f"[supabase] Failed to initialize client: {e}")
        return None


def save_study(session_id: str, prompt: str, q1: str, q2, q3) -> bool:
    row = {
        "session_id": session_id,
        "prompt": prompt,
        "q1_surprising_stage": q1,
        "q2_trust_before": int(q2) if q2 is not None else None,
        "q3_trust_after": int(q3) if q3 is not None else None,
    }
    client = _get_client()
    if client is None:
        print(f"[STUDY] {row}")
        return False
    try:
        client.table("tedx_study").insert(row).execute()
        print(f"[supabase] Saved study row for session {session_id}")
        return True
    except Exception as e:
        print(f"[supabase] Insert failed: {e}")
        print(f"[STUDY-fallback] {row}")
        return False
