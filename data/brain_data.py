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
