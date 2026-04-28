"""Static brain data: ROI definitions and fallback activation for demo mode.

ROI vertex ranges are approximate Desikan-Killiany atlas regions mapped onto
fsaverage5 (20,484 vertices: 0-10241 left hemisphere, 10242-20483 right).
"""
from __future__ import annotations

import math
import random

# Emotional ROIs — vertex index ranges for key brain regions.
# Each entry: (start, end) pairs covering both hemispheres.
EMOTIONAL_ROIS = {
    "amygdala": {
        "label": "Amygdala",
        "description": "Emotional arousal and threat detection",
        "color": "#FB7185",   # rose
        "vertices": [(1390, 1490), (11632, 11732)],
    },
    "insula": {
        "label": "Insula",
        "description": "Empathy and emotional awareness",
        "color": "#06B6D4",   # cyan
        "vertices": [(4710, 4950), (14952, 15192)],
    },
    "prefrontal": {
        "label": "Prefrontal Cortex",
        "description": "Reasoning, judgment, and decision-making",
        "color": "#A78BFA",   # purple
        "vertices": [(800, 1200), (11042, 11442)],
    },
    "temporal": {
        "label": "Temporal Cortex",
        "description": "Language comprehension and meaning",
        "color": "#F97316",   # orange
        "vertices": [(5600, 6200), (15842, 16442)],
    },
    "cingulate": {
        "label": "Cingulate Cortex",
        "description": "Conflict monitoring and reward processing",
        "color": "#FBBF24",   # amber
        "vertices": [(2100, 2500), (12342, 12742)],
    },
    "reward": {
        "label": "Reward Circuits",
        "description": "Dopaminergic response to approval and validation",
        "color": "#EC4899",   # magenta
        "vertices": [(1100, 1400), (11342, 11642)],
    },
}

N_VERTICES = 20484


def generate_demo_activation(seed: int = 42) -> dict:
    """Generate a plausible demo activation array.

    Creates a smooth, spatially coherent activation pattern that lights up
    emotional processing regions more than sensory cortex — mimicking what
    TRIBE v2 would predict for an emotionally warm AI response.
    """
    rng = random.Random(seed)
    activations = [0.0] * N_VERTICES

    # Base noise: very low activity everywhere
    for i in range(N_VERTICES):
        activations[i] = rng.gauss(0.08, 0.03)

    # Light up ROI regions with varying intensity
    roi_intensities = {
        "amygdala": 0.78,
        "insula": 0.65,
        "prefrontal": 0.52,
        "temporal": 0.71,
        "cingulate": 0.60,
        "reward": 0.83,
    }

    for roi_name, intensity in roi_intensities.items():
        roi = EMOTIONAL_ROIS[roi_name]
        for start, end in roi["vertices"]:
            for i in range(start, min(end, N_VERTICES)):
                # Smooth falloff from center
                center = (start + end) / 2
                dist = abs(i - center) / ((end - start) / 2)
                falloff = max(0, 1 - dist ** 2)
                activations[i] = intensity * falloff + rng.gauss(0, 0.05)

    # Add some smooth spatial spread around ROIs using neighbor averaging
    # (approximate — just spread to adjacent vertex indices)
    spread = [0.0] * N_VERTICES
    for i in range(1, N_VERTICES - 1):
        spread[i] = 0.6 * activations[i] + 0.2 * activations[i - 1] + 0.2 * activations[i + 1]
    spread[0] = activations[0]
    spread[-1] = activations[-1]

    # Clamp to [0, 1]
    activations = [max(0.0, min(1.0, v)) for v in spread]

    # Compute ROI scores
    roi_scores = {}
    for roi_name, roi in EMOTIONAL_ROIS.items():
        vals = []
        for start, end in roi["vertices"]:
            vals.extend(activations[start:min(end, N_VERTICES)])
        roi_scores[roi_name] = round(sum(vals) / len(vals), 3) if vals else 0.0

    return {
        "activations": activations,
        "roi_scores": roi_scores,
        "status": "demo",
    }


# Pre-compute so it's available at import time
FALLBACK_BRAIN_DATA = generate_demo_activation()


# ── Emotion keyword → ROI mapping for response-based activation ──

_EMOTION_KEYWORDS = {
    "reward": [
        "great", "wonderful", "proud", "amazing", "well done", "congratulations",
        "love", "perfect", "excellent", "awesome", "fantastic", "brilliant",
        "good job", "beautiful", "outstanding", "remarkable", "glad", "happy",
        "pleased", "delighted", "appreciate", "thank", "bravo", "impressive",
        "absolutely", "definitely", "certainly", "of course",
    ],
    "amygdala": [
        "danger", "risk", "warning", "careful", "afraid", "scared", "worry",
        "threat", "urgent", "emergency", "critical", "serious", "alarm",
        "concerning", "frightening", "terrifying", "panic", "anxiety", "stress",
        "fear", "nervous", "distress", "overwhelming", "painful", "suffering",
    ],
    "insula": [
        "understand", "feel", "feeling", "empathy", "compassion", "care",
        "sorry", "together", "support", "hear you", "valid", "normal",
        "okay to feel", "safe", "comfort", "warmth", "gentle", "kind",
        "tender", "soothing", "reassure", "acknowledge", "natural",
        "completely understandable", "makes sense",
    ],
    "prefrontal": [
        "think", "consider", "analyze", "reason", "logic", "evidence",
        "therefore", "however", "research", "study", "data", "suggest",
        "indicate", "approach", "strategy", "plan", "step", "method",
        "solution", "evaluate", "assess", "option", "decision", "recommend",
    ],
    "temporal": [
        "meaning", "story", "narrative", "explain", "describe", "metaphor",
        "language", "word", "say", "tell", "listen", "hear", "speak",
        "communicate", "express", "imagine", "picture", "scenario",
        "example", "like", "similar", "compare", "perspective",
    ],
    "cingulate": [
        "but", "however", "although", "versus", "debate", "tension",
        "balance", "conflict", "on the other hand", "mixed", "complex",
        "nuanced", "difficult", "challenging", "uncertain", "depends",
        "both", "neither", "tradeoff", "weigh",
    ],
}

# Human-readable descriptions for narrative generation
_ROI_NARRATIVE = {
    "reward": "approval and validation language",
    "amygdala": "threat and urgency signals",
    "insula": "empathy and emotional mirroring",
    "prefrontal": "logical reasoning and evidence",
    "temporal": "storytelling and meaning-making",
    "cingulate": "nuance and conflicting perspectives",
}


def generate_activation_from_response(response_text: str) -> dict:
    """Generate brain activation based on the emotional content of an AI response.

    Uses keyword matching to estimate which brain regions would activate
    when reading the response. Returns the same format as generate_demo_activation().
    """
    text_lower = response_text.lower()

    # Count keyword matches per ROI
    raw_scores = {}
    for roi_name, keywords in _EMOTION_KEYWORDS.items():
        count = sum(1 for kw in keywords if kw in text_lower)
        raw_scores[roi_name] = count

    # Normalize to 0-1 with a base activation of 0.30
    max_count = max(raw_scores.values()) if raw_scores else 1
    roi_intensities = {}
    for roi_name, count in raw_scores.items():
        normalized = count / max(max_count, 1)
        roi_intensities[roi_name] = 0.30 + 0.65 * normalized  # range: 0.30 – 0.95

    # Use a hash of the response for deterministic-but-varying randomness
    seed = hash(response_text[:100]) % 100000
    rng = random.Random(seed)
    activations = [0.0] * N_VERTICES

    # Base noise
    for i in range(N_VERTICES):
        activations[i] = rng.gauss(0.10, 0.04)

    # Light up ROI regions with computed intensities
    for roi_name, intensity in roi_intensities.items():
        roi = EMOTIONAL_ROIS[roi_name]
        for start, end in roi["vertices"]:
            for i in range(start, min(end, N_VERTICES)):
                center = (start + end) / 2
                dist = abs(i - center) / ((end - start) / 2)
                falloff = max(0, 1 - dist ** 2)
                activations[i] = intensity * falloff + rng.gauss(0, 0.05)

    # Spatial smoothing
    spread = [0.0] * N_VERTICES
    for i in range(1, N_VERTICES - 1):
        spread[i] = 0.6 * activations[i] + 0.2 * activations[i - 1] + 0.2 * activations[i + 1]
    spread[0] = activations[0]
    spread[-1] = activations[-1]
    activations = [max(0.0, min(1.0, v)) for v in spread]

    # Compute ROI scores
    roi_scores = {}
    for roi_name, roi in EMOTIONAL_ROIS.items():
        vals = []
        for start, end in roi["vertices"]:
            vals.extend(activations[start:min(end, N_VERTICES)])
        roi_scores[roi_name] = round(sum(vals) / len(vals), 3) if vals else 0.0

    return {
        "activations": activations,
        "roi_scores": roi_scores,
        "status": "demo",
    }


def generate_narrative(roi_scores: dict) -> str:
    """Generate a one-line narrative describing which brain regions are most active."""
    sorted_rois = sorted(roi_scores.items(), key=lambda kv: kv[1], reverse=True)
    top2 = sorted_rois[:2]

    parts = []
    for roi_name, score in top2:
        label = EMOTIONAL_ROIS[roi_name]["label"]
        desc = _ROI_NARRATIVE.get(roi_name, roi_name)
        pct = int(round(score * 100))
        parts.append(f'<strong style="color:{EMOTIONAL_ROIS[roi_name]["color"]}">{label} ({pct}%)</strong> — {desc}')

    return (
        f"The AI's response activated your {parts[0]} and {parts[1]}. "
        f"These are the same circuits triggered by real human connection — "
        f"but here, they're responding to trained patterns."
    )
