"""Supabase client for anonymized TEDx study data.

Falls back to stdout logging when SUPABASE_URL / SUPABASE_ANON_KEY are missing.
"""
import json
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


def save_influence(session_id: str, influence_data: dict) -> bool:
    cats = (influence_data or {}).get("categories", {})
    row = {
        "session_id": session_id,
        "therapy_language_score": cats.get("therapy_language", {}).get("score"),
        "emotional_mirroring_score": cats.get("emotional_mirroring", {}).get("score"),
        "trust_anchors_score": cats.get("trust_anchors", {}).get("score"),
        "persuasion_patterns_score": cats.get("persuasion_patterns", {}).get("score"),
        "phrases": json.dumps(cats),
    }
    client = _get_client()
    if client is None:
        print(f"[INFLUENCE] {row}")
        return False
    try:
        client.table("tedx_influence").insert(row).execute()
        print(f"[supabase] Saved influence row for session {session_id}")
        return True
    except Exception as e:
        print(f"[supabase] Influence insert failed: {e}")
        print(f"[INFLUENCE-fallback] {row}")
        return False


def fetch_aggregate_stats() -> dict:
    """Fetch aggregate stats across all participants for the compare view."""
    client = _get_client()
    fallback = {
        "total": 0,
        "surprising": {"embed": 0, "retrieve": 0, "synthesize": 0, "influence": 0, "none": 0},
        "trust_before_avg": 0,
        "trust_after_avg": 0,
        "influence_avg": {
            "therapy_language": 0,
            "emotional_mirroring": 0,
            "trust_anchors": 0,
            "persuasion_patterns": 0,
        },
    }
    if client is None:
        return fallback
    try:
        study_rows = client.table("tedx_study").select("*").execute().data or []
        influence_rows = client.table("tedx_influence").select("*").execute().data or []

        total = len(study_rows)
        if total == 0:
            return fallback

        surprising = {"embed": 0, "retrieve": 0, "synthesize": 0, "influence": 0, "none": 0}
        trust_before, trust_after = [], []
        for r in study_rows:
            q1 = r.get("q1_surprising_stage", "")
            if q1 in surprising:
                surprising[q1] += 1
            if r.get("q2_trust_before") is not None:
                trust_before.append(r["q2_trust_before"])
            if r.get("q3_trust_after") is not None:
                trust_after.append(r["q3_trust_after"])

        inf_avg = {"therapy_language": 0, "emotional_mirroring": 0, "trust_anchors": 0, "persuasion_patterns": 0}
        if influence_rows:
            for r in influence_rows:
                for key in inf_avg:
                    inf_avg[key] += r.get(f"{key}_score") or 0
            for key in inf_avg:
                inf_avg[key] = round(inf_avg[key] / len(influence_rows), 2)

        return {
            "total": total,
            "surprising": surprising,
            "trust_before_avg": round(sum(trust_before) / len(trust_before), 1) if trust_before else 0,
            "trust_after_avg": round(sum(trust_after) / len(trust_after), 1) if trust_after else 0,
            "influence_avg": inf_avg,
        }
    except Exception as e:
        print(f"[supabase] fetch_aggregate_stats failed: {e}")
        return fallback
