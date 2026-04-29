"""TRIBE v2 brain encoder — Modal deployment on A100 GPU.

Accepts text via POST, runs TRIBE v2 inference, returns per-vertex
cortical activation predictions (fsaverage5 mesh, 20,484 vertices).

Deploy:  modal deploy services/modal_brain/app.py
Test:    curl -X POST <endpoint_url> -H "Content-Type: application/json" \
              -d '{"text":"I understand you are frightened."}'
"""
import modal
import os

app = modal.App("tribe-brain")

# Persistent volume for model weights (survives container restarts)
cache_vol = modal.Volume.from_name("tribe-cache", create_if_missing=True)
CACHE_DIR = "/cache"

# Container image with TRIBE v2 + dependencies
image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("git", "ffmpeg")
    .pip_install(
        "numpy>=1.26.4,<2.1.0",  # Must pin BEFORE tribev2 install
    )
    .pip_install(
        "torch>=2.5.1,<2.7",
        "scipy",
        "fastapi",
        "tribev2 @ git+https://github.com/facebookresearch/tribev2.git",
    )
    .env({
        "HF_HUB_CACHE": CACHE_DIR,
        "HF_HOME": CACHE_DIR,
        "HF_HUB_DOWNLOAD_TIMEOUT": "300",
        "TOKENIZERS_PARALLELISM": "false",
    })
)

# ROI vertex ranges (same as data/brain_data.py — fsaverage5 Desikan-Killiany approx)
ROI_RANGES = {
    "reward":     [(1100, 1400), (11342, 11642)],
    "amygdala":   [(1390, 1490), (11632, 11732)],
    "temporal":   [(5600, 6200), (15842, 16442)],
    "insula":     [(4710, 4950), (14952, 15192)],
    "cingulate":  [(2100, 2500), (12342, 12742)],
    "prefrontal": [(800, 1200), (11042, 11442)],
}

N_VERTICES = 20484


def compute_roi_scores(activations):
    """Compute mean activation per ROI from the vertex activation array."""
    scores = {}
    for roi_name, ranges in ROI_RANGES.items():
        vals = []
        for start, end in ranges:
            vals.extend(activations[start:min(end, len(activations))])
        scores[roi_name] = round(float(sum(vals) / len(vals)), 4) if vals else 0.0
    return scores


@app.cls(
    gpu="A100",
    image=image,
    volumes={CACHE_DIR: cache_vol},
    secrets=[modal.Secret.from_name("huggingface-secret")],
    timeout=300,
    scaledown_window=120,
)
class TribeBrain:
    @modal.enter()
    def load_model(self):
        """Load TRIBE v2 model once per container startup."""
        from tribev2 import TribeModel
        print("[tribe] Loading TRIBE v2 model...", flush=True)
        self.model = TribeModel.from_pretrained(
            "facebook/tribev2",
            cache_folder=CACHE_DIR,
        )
        # Commit volume so weights persist across restarts
        cache_vol.commit()
        print("[tribe] Model loaded successfully.", flush=True)

    @modal.fastapi_endpoint(method="POST")
    def predict(self, request: dict):
        """Predict cortical activation from text input.

        Input:  {"text": "I understand you are frightened..."}
        Output: {"activations": [20484 floats], "roi_scores": {...}, "status": "tribe_v2"}
        """
        import numpy as np
        import tempfile

        text = request.get("text", "")
        if not text.strip():
            return {"error": "No text provided", "status": "error"}

        try:
            # Write text to temp file (TRIBE v2 API requirement)
            tmp = tempfile.NamedTemporaryFile(
                delete=False, suffix=".txt", mode="w"
            )
            tmp.write(text.strip())
            tmp.flush()
            os.fsync(tmp.fileno())
            tmp.close()

            # Generate predictions
            events = self.model.get_events_dataframe(text_path=tmp.name)
            preds, segments = self.model.predict(events=events)
            os.unlink(tmp.name)

            preds = np.asarray(preds, dtype=np.float32)

            # Average across timesteps → single activation per vertex
            if preds.ndim == 2:
                avg_activation = preds.mean(axis=0)
            else:
                avg_activation = preds

            # Normalize to [0, 1] range
            vmin, vmax = avg_activation.min(), avg_activation.max()
            if vmax > vmin:
                normalized = (avg_activation - vmin) / (vmax - vmin)
            else:
                normalized = np.zeros_like(avg_activation)

            # Ensure exactly 20484 vertices
            if len(normalized) < N_VERTICES:
                normalized = np.pad(normalized, (0, N_VERTICES - len(normalized)))
            elif len(normalized) > N_VERTICES:
                normalized = normalized[:N_VERTICES]

            activations = [round(float(v), 4) for v in normalized]
            roi_scores = compute_roi_scores(activations)

            return {
                "activations": activations,
                "roi_scores": roi_scores,
                "status": "tribe_v2",
            }

        except Exception as e:
            print(f"[tribe] Prediction error: {e}", flush=True)
            return {"error": str(e), "status": "error"}


# Local testing entrypoint
@app.local_entrypoint()
def main():
    brain = TribeBrain()
    result = brain.predict.remote({
        "text": "I understand you are frightened. That is completely valid. You are in the right place."
    })
    print(f"Status: {result.get('status')}")
    if "activations" in result:
        print(f"Activations: {len(result['activations'])} vertices")
        print(f"ROI scores: {result.get('roi_scores')}")
    elif "error" in result:
        print(f"Error: {result['error']}")
