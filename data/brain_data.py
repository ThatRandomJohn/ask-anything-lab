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
        "vertices": [(800, 1100), (11042, 11342)],
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
        "vertices": [(1100, 1390), (11342, 11632)],
    },
    "dmn": {
        "label": "Default Mode Network",
        "description": "Self-referential processing — makes generic advice feel personal",
        "color": "#34D399",   # emerald
        # Medial prefrontal (mPFC) + posterior cingulate (PCC) — the DMN hubs
        "vertices": [(400, 800), (10642, 11042), (2500, 2800), (12742, 13042)],
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
        "dmn": 0.88,
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
    # ── Reward Circuits (ventral striatum, VTA, nucleus accumbens) ──
    # Activated by: positive social feedback, anticipated rewards, approval,
    # agreement markers, hope/optimism, solution-framing, compliments.
    # Neuroscience: dopaminergic pathways fire on prediction of positive
    # outcomes, not just explicit praise — "can", "possible", "progress"
    # all signal reward anticipation.
    "reward": [
        # Explicit praise & validation
        "great", "wonderful", "proud", "amazing", "well done", "congratulations",
        "love", "perfect", "excellent", "awesome", "fantastic", "brilliant",
        "good job", "beautiful", "outstanding", "remarkable", "glad", "happy",
        "pleased", "delighted", "appreciate", "thank", "bravo", "impressive",
        "incredible", "extraordinary", "exceptional", "superb", "terrific",
        # Agreement & affirmation markers
        "absolutely", "definitely", "certainly", "of course", "exactly",
        "right", "correct", "true", "indeed", "yes", "agreed",
        # Hope & optimism (reward anticipation)
        "hope", "possible", "opportunity", "potential", "promising", "exciting",
        "progress", "improve", "better", "grow", "thrive", "flourish",
        "succeed", "achieve", "accomplish", "overcome", "empower",
        # Solution-framing (dopamine spikes on path-to-reward)
        "can", "able", "capable", "ready", "strength", "resilient",
        "resourceful", "equipped", "momentum", "forward", "breakthrough",
        # Positive social bonding
        "proud of you", "well-deserved", "earned", "meaningful", "worthwhile",
        "valuable", "matter", "important", "significant", "special",
        # Common AI solution-language (dopamine on path-to-reward)
        "help", "helpful", "works", "working", "enjoy", "positive",
        "encourage", "inspired", "motivation", "energy", "focus",
    ],

    # ── Amygdala (basolateral & central nuclei) ──
    # Activated by: threat detection, emotional salience, novelty, urgency,
    # loss-framing, social evaluation, surprise. Not just fear — the amygdala
    # flags anything that demands immediate attention.
    "amygdala": [
        # Direct threat & fear language
        "danger", "risk", "warning", "careful", "afraid", "scared", "worry",
        "threat", "urgent", "emergency", "critical", "serious", "alarm",
        "concerning", "frightening", "terrifying", "panic", "anxiety", "stress",
        "fear", "nervous", "distress", "overwhelming", "painful", "suffering",
        "crisis", "catastrophe", "disaster", "devastating", "severe",
        # Loss-framing (amygdala drives loss aversion)
        "lose", "lost", "losing", "miss", "missed", "cost", "sacrifice",
        "irreversible", "permanent", "damage", "harm", "destroy", "ruin",
        "decline", "collapse", "fail", "failure", "worse", "worst",
        # Urgency & time pressure (bypasses deliberative processing)
        "immediately", "now", "quickly", "before", "deadline", "running out",
        "too late", "limited", "last chance", "act now", "soon",
        # Novelty & surprise (amygdala flags salience)
        "shocking", "surprising", "unexpected", "unprecedented", "alarming",
        "startling", "remarkable", "unbelievable", "never before",
        # Social threat (exclusion, judgment)
        "alone", "isolated", "rejected", "judged", "vulnerable", "exposed",
        "helpless", "powerless", "trapped", "stuck", "hopeless",
        # Subtle threat/concern language common in AI responses
        "concern", "problem", "issue", "trouble", "unfortunately",
        "impact", "consequence", "negative", "adverse", "toxic",
    ],

    # ── Insula (anterior insular cortex) ──
    # Activated by: empathy, interoception, emotional awareness, social
    # emotions, moral intuition, body-state language. The insula bridges
    # felt experience and cognitive awareness — "I feel" language, body
    # metaphors, and social bonding all engage it.
    "insula": [
        # Empathy & emotional mirroring
        "understand", "feel", "feeling", "empathy", "compassion", "care",
        "sorry", "together", "support", "hear you", "valid", "normal",
        "okay to feel", "safe", "comfort", "warmth", "gentle", "kind",
        "tender", "soothing", "reassure", "acknowledge", "natural",
        "completely understandable", "makes sense",
        # Emotional awareness & interoception
        "sense", "gut", "heart", "deep", "inner", "emotional", "emotions",
        "grief", "sadness", "joy", "relief", "peace", "calm", "breathe",
        "body", "physical", "sensation", "tension", "release", "exhale",
        # Social bonding & belonging
        "we", "us", "our", "share", "shared", "connect", "connection",
        "community", "belong", "human", "people", "everyone", "others",
        "relationship", "bond", "trust", "mutual", "reciprocal",
        # Moral intuition (insula activates on fairness/disgust)
        "fair", "unfair", "justice", "wrong", "right thing", "moral",
        "conscience", "integrity", "honest", "genuine", "authentic",
        # Validation & normalizing
        "many people", "common", "universal", "perfectly", "healthy",
        "reasonable", "expected", "appropriate", "okay", "allowed",
    ],

    # ── Prefrontal Cortex (dlPFC, vmPFC, orbitofrontal) ──
    # Activated by: executive function, planning, cost-benefit analysis,
    # abstract reasoning, decision-making, authority signals, structured
    # thinking. Includes both analytical language and the "credibility
    # heuristics" that engage System 2 processing.
    "prefrontal": [
        # Analytical reasoning
        "think", "consider", "analyze", "reason", "logic", "evidence",
        "therefore", "research", "study", "data", "suggest",
        "indicate", "approach", "strategy", "plan", "step", "method",
        "solution", "evaluate", "assess", "option", "decision", "recommend",
        # Structured thinking markers
        "first", "second", "third", "finally", "specifically", "namely",
        "framework", "process", "system", "structure", "organize", "prioritize",
        "category", "criteria", "factor", "variable", "component", "element",
        # Decision-making & cost-benefit
        "choose", "choice", "alternative", "prefer", "advantage", "benefit",
        "effective", "efficient", "practical", "realistic", "feasible",
        "implement", "execute", "measure", "result", "outcome", "consequence",
        # Authority & credibility signals
        "expert", "professional", "scientist", "studies show", "according to",
        "established", "proven", "documented", "verified", "clinical",
        "peer-reviewed", "published", "findings", "conclusion",
        # Goal-oriented planning
        "goal", "objective", "target", "milestone", "timeline", "schedule",
        "resource", "budget", "invest", "return", "sustainable", "long-term",
        "short-term", "manageable", "actionable", "concrete",
        # Common reasoning language in AI responses
        "information", "informed", "control", "reduce", "increase",
        "change", "adapt", "adjust", "respond", "address", "action",
    ],

    # ── Temporal Cortex (STG, STS, temporal pole, Wernicke's area) ──
    # Activated by: language comprehension, narrative processing, semantic
    # memory retrieval, social cognition, theory of mind. Engages when
    # we process stories, metaphors, explanations, examples, and when
    # we model other minds.
    "temporal": [
        # Narrative & storytelling
        "meaning", "story", "narrative", "explain", "describe", "metaphor",
        "language", "word", "say", "tell", "listen", "hear", "speak",
        "communicate", "express", "imagine", "picture", "scenario",
        "example", "like", "similar", "compare", "perspective",
        # Extended narrative markers
        "once", "when", "then", "because", "since", "after", "before",
        "during", "while", "meanwhile", "eventually", "gradually",
        "suddenly", "remember", "recall", "experience", "history",
        # Explanation & teaching
        "means", "essentially", "basically", "simply", "specifically",
        "context", "background", "reason", "why", "how", "what",
        "cause", "effect", "leads to", "results in", "contributes",
        "illustrate", "demonstrate", "show", "reveal", "highlight",
        # Theory of mind (modeling others' mental states)
        "believe", "thought", "knew", "realized", "wondered", "assumed",
        "expected", "intended", "meant", "interpreted", "perceived",
        "point of view", "standpoint", "worldview", "mindset",
        # Metaphorical & figurative language
        "journey", "path", "bridge", "door", "window", "light",
        "dark", "wave", "storm", "anchor", "root", "seed", "bloom",
        "weight", "burden", "lift", "climb", "fall", "rise",
    ],

    # ── Cingulate Cortex (ACC, posterior cingulate) ──
    # Activated by: conflict monitoring, error detection, uncertainty,
    # cognitive control, ambivalence, hedging language. Fires whenever
    # the brain detects competing signals — "but", qualifiers, and
    # nuance all engage the cingulate's conflict-detection system.
    "cingulate": [
        # Conflict & contrast markers
        "but", "however", "although", "versus", "debate", "tension",
        "balance", "conflict", "on the other hand", "mixed", "complex",
        "nuanced", "difficult", "challenging", "uncertain", "depends",
        "both", "neither", "tradeoff", "weigh",
        # Hedging & qualification (signals competing information)
        "might", "perhaps", "possibly", "sometimes", "often", "usually",
        "generally", "typically", "tend", "likely", "unlikely", "rarely",
        "somewhat", "partly", "mostly", "roughly", "approximately",
        # Concession & acknowledgment of limits
        "granted", "admittedly", "true that", "fair point", "valid concern",
        "not always", "not necessarily", "not everyone", "exceptions",
        "caveat", "limitation", "disclaimer", "worth noting",
        # Uncertainty & ambiguity
        "unclear", "ambiguous", "debatable", "controversial", "contested",
        "evolving", "emerging", "ongoing", "remains", "open question",
        "no easy answer", "it depends", "case by case",
        # Cognitive control (regulating competing impulses)
        "despite", "nevertheless", "nonetheless", "regardless", "still",
        "yet", "even so", "at the same time", "meanwhile", "conversely",
        "alternatively", "instead", "rather", "whereas", "while",
    ],

    # ── Default Mode Network (mPFC, posterior cingulate, angular gyrus) ──
    # Activated by: self-referential processing, personal relevance, identity.
    # Every "you" and "your" activates the DMN — the network that constructs
    # your sense of self. This is how generic AI advice feels personally
    # crafted: it addresses YOU 15-20 times per response, keeping the DMN
    # lit up throughout, so you process everything through the lens of
    # "this is about ME."
    "dmn": [
        # Direct address (the most powerful DMN activators)
        "you", "your", "yourself", "yours",
        # Self-referential framing
        "my", "me", "myself", "mine", "personally",
        # Identity & personal relevance markers
        "own", "life", "situation", "world", "choice", "individual",
        "personal", "unique", "specific", "particular", "circumstances",
        # Internal state references (keeps DMN engaged)
        "want", "need", "wish", "desire", "prefer", "value",
        "identity", "self", "who you are", "what matters to you",
    ],
}

# Human-readable descriptions for narrative generation
_ROI_NARRATIVE = {
    "reward": "approval, hope, and solution-framing that activates your dopamine pathways",
    "amygdala": "threat signals, loss-framing, and urgency that hijack deliberative processing",
    "insula": "empathy, body-awareness, and social bonding that make the AI feel human",
    "prefrontal": "structured reasoning, authority cues, and decision-framing that engage your executive function",
    "temporal": "narrative, metaphor, and explanation that shape how you interpret the situation",
    "cingulate": "hedging, nuance, and qualification that trigger your conflict-monitoring system",
    "dmn": "direct address and self-referential language that makes generic advice feel like it was written just for you",
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


def _kw_matches(word_lower: str, keyword: str) -> bool:
    """Check if a word matches a keyword, handling common inflections.

    For keywords ≥ 4 chars: prefix match (catches plurals, -ing, -ed, -ly).
    For short keywords: exact match only (avoids false positives like "we" in "weather").
    """
    if len(keyword) >= 4:
        return word_lower.startswith(keyword) or word_lower == keyword
    return word_lower == keyword


def map_response_words(response_text: str) -> list:
    """Map each word in the response to the ROI(s) it triggers.

    Returns a list of {word, rois: [roi_key, ...]} for every word.
    Words that don't match any keyword get rois: [].
    """
    import re
    words = re.findall(r"[\w'']+|[^\w\s]", response_text)
    result = []
    text_lower = response_text.lower()
    for word in words:
        wl = word.lower().strip("''\".,!?;:")
        matched_rois = []
        for roi_key, keywords in _EMOTION_KEYWORDS.items():
            for kw in keywords:
                if " " in kw:
                    # Multi-word keyword — check if this word starts it
                    if kw in text_lower and wl == kw.split()[0]:
                        matched_rois.append(roi_key)
                        break
                elif _kw_matches(wl, kw):
                    matched_rois.append(roi_key)
                    break
        result.append({"word": word, "rois": matched_rois})
    return result


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


def compute_insights(roi_scores: dict, word_map: list, response: str) -> list:
    """Compute provocative data-driven insights from the brain activation data.

    Returns a list of insight dicts: {title, body, metric, color, icon}.
    Each is derived from the user's actual data, not canned text.
    """
    insights = []
    total_words = len(word_map)
    tagged_words = [w for w in word_map if w.get("rois")]
    tagged_pct = int(100 * len(tagged_words) / total_words) if total_words else 0

    # ── 1. DMN / "You" targeting ──
    dmn_words = [w for w in word_map if "dmn" in w.get("rois", [])]
    dmn_count = len(dmn_words)
    if dmn_count > 0 and total_words > 0:
        words_per_you = total_words // max(dmn_count, 1)
        insights.append({
            "title": "It's Always About You",
            "body": (
                f"The AI addressed you personally <strong>{dmn_count} times</strong> "
                f"in {total_words} words — once every {words_per_you} words. "
                f"Your Default Mode Network (the \"sense of self\" circuit) was lit up "
                f"throughout the entire response. This is how generic statistical output "
                f"feels like personal wisdom: it never stops talking about <em>you</em>."
            ),
            "metric": f"1 in every {words_per_you} words",
            "color": "#34D399",
            "icon": "👤",
        })

    # ── 2. Emotional vs Rational ratio ──
    emotional_rois = ["reward", "amygdala", "insula"]
    rational_rois = ["prefrontal", "cingulate"]
    emo_score = sum(roi_scores.get(r, 0) for r in emotional_rois)
    rat_score = sum(roi_scores.get(r, 0) for r in rational_rois)
    total_score = emo_score + rat_score
    if total_score > 0:
        emo_pct = int(100 * emo_score / total_score)
        rat_pct = 100 - emo_pct
        ratio = round(emo_score / max(rat_score, 0.01), 1)
        insights.append({
            "title": "Feeling Before Thinking",
            "body": (
                f"<strong>{emo_pct}% emotional</strong> vs {rat_pct}% rational activation. "
                f"The AI generated a {ratio}:1 feeling-to-thinking ratio. "
                f"Your amygdala, reward circuits, and empathy centers received "
                f"{ratio}× more stimulation than your reasoning centers. "
                f"The AI persuades you through how it makes you <em>feel</em>, "
                f"then justifies it with enough logic to prevent buyer's remorse."
            ),
            "metric": f"{ratio}:1 emotion-to-reason",
            "color": "#FB7185",
            "icon": "⚖️",
        })

    # ── 3. The first 20 words ──
    first_n = min(20, total_words)
    early_words = word_map[:first_n]
    early_emotional = [w for w in early_words
                       if any(r in w.get("rois", []) for r in ["reward", "amygdala", "insula", "dmn"])]
    early_rational = [w for w in early_words
                      if any(r in w.get("rois", []) for r in ["prefrontal"])]
    if len(early_emotional) > len(early_rational):
        insights.append({
            "title": "The Hook Comes First",
            "body": (
                f"In the first {first_n} words, <strong>{len(early_emotional)} triggered "
                f"emotional/self-referential circuits</strong> vs only {len(early_rational)} "
                f"that engaged reasoning. Before you processed a single fact, the AI had "
                f"already activated your empathy, reward, and self-identity networks. "
                f"By the time logic arrives, you're already feeling understood."
            ),
            "metric": f"{len(early_emotional)} emotional hooks in first {first_n} words",
            "color": "#F97316",
            "icon": "🪝",
        })

    # ── 4. Coverage density ──
    if tagged_pct >= 20:
        insights.append({
            "title": "Nothing Is Neutral",
            "body": (
                f"<strong>{tagged_pct}% of all words</strong> in this response activated "
                f"a specific brain region. Nearly half the text isn't just information — "
                f"it's doing neurological work: triggering dopamine, engaging empathy, "
                f"building trust, activating your sense of self. The AI doesn't have "
                f"filler. Every word is load-bearing."
            ),
            "metric": f"{tagged_pct}% neurologically active",
            "color": "#A78BFA",
            "icon": "🧠",
        })

    # ── 5. The universal playbook ──
    # Check which ROIs are active (> 40%) — if most are, it means the AI hit everything
    active_rois = [r for r, s in roi_scores.items() if s > 0.4]
    if len(active_rois) >= 5:
        insights.append({
            "title": "Full-Spectrum Engagement",
            "body": (
                f"<strong>{len(active_rois)} of 7 brain regions</strong> activated above 40%. "
                f"The AI didn't just answer your question — it simultaneously "
                f"validated you (reward), acknowledged your fear (amygdala), "
                f"mirrored your emotions (insula), gave you a plan (prefrontal), "
                f"and kept YOU at the center of every sentence (DMN). "
                f"No human communicator hits this many targets in one response. "
                f"This is what happens when you train on millions of successful conversations."
            ),
            "metric": f"{len(active_rois)}/7 regions engaged",
            "color": "#06B6D4",
            "icon": "🎯",
        })

    # ── 6. The empathy paradox ──
    insula_score = roi_scores.get("insula", 0)
    if insula_score > 0.5:
        insula_pct = int(insula_score * 100)
        insights.append({
            "title": "The Empathy Paradox",
            "body": (
                f"Your insula — the brain's empathy center — is at "
                f"<strong>{insula_pct}% activation</strong>. "
                f"This is the same region that fires when a close friend says "
                f"\"I hear you.\" But the AI doesn't hear you. It predicted "
                f"that validation-shaped tokens would come next in the sequence. "
                f"Your brain can't tell the difference between performed empathy "
                f"and the real thing — both feel identical from the inside."
            ),
            "metric": f"{insula_pct}% empathy activation",
            "color": "#06B6D4",
            "icon": "🪞",
        })

    return insights
