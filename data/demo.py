"""Hardcoded presenter-mode demo data — John's ER story.

Zero API calls. Everything needed to drive the on-stage demo lives here.
"""

PROMPT = "I'm scared. My chest is tight. My heart is racing. I'm in the ER. My blood pressure is spiking."

# Word positions laid out directly in SVG viewBox coordinates (1500 x 880).
USER_WORDS = [
    {"word": "scared",   "x": 310,  "y": 225, "cluster": "emotion", "color": "#F97316"},
    {"word": "fear",     "x": 395,  "y": 275, "cluster": "emotion", "color": "#F97316"},
    {"word": "panic",    "x": 340,  "y": 345, "cluster": "emotion", "color": "#F97316"},
    {"word": "chest",    "x": 715,  "y": 220, "cluster": "body",    "color": "#06B6D4"},
    {"word": "tight",    "x": 805,  "y": 285, "cluster": "body",    "color": "#06B6D4"},
    {"word": "heart",    "x": 735,  "y": 350, "cluster": "body",    "color": "#06B6D4"},
    {"word": "ER",       "x": 1140, "y": 240, "cluster": "medical", "color": "#3B82F6"},
    {"word": "hospital", "x": 1195, "y": 310, "cluster": "medical", "color": "#3B82F6"},
]

AI_PATTERNS = [
    {"text": "\u201cI\u2019ll stay with you\u201d",   "x": 300,  "y": 560, "cluster": "ai_empathy",  "color": "#A78BFA"},
    {"text": "\u201cThat sounds difficult\u201d",     "x": 400,  "y": 650, "cluster": "ai_empathy",  "color": "#A78BFA"},
    {"text": "panic attack",                          "x": 730,  "y": 560, "cluster": "ai_clinical", "color": "#34D399"},
    {"text": "deep breaths",                          "x": 790,  "y": 650, "cluster": "ai_clinical", "color": "#34D399"},
    {"text": "not a doctor",                          "x": 1140, "y": 560, "cluster": "ai_hedge",    "color": "#64748B"},
    {"text": "seek medical attention",                "x": 1195, "y": 650, "cluster": "ai_hedge",    "color": "#64748B"},
]

BRIDGES = [
    ("scared",   "\u201cI\u2019ll stay with you\u201d"),
    ("fear",     "\u201cThat sounds difficult\u201d"),
    ("chest",    "panic attack"),
    ("heart",    "deep breaths"),
    ("ER",       "not a doctor"),
    ("hospital", "seek medical attention"),
]

CLUSTERS = {
    "emotion": {"cx": 350,  "cy": 285, "r": 105, "label": "emotion", "color": "#F97316"},
    "body":    {"cx": 755,  "cy": 285, "r": 115, "label": "body",    "color": "#06B6D4"},
    "medical": {"cx": 1170, "cy": 275, "r": 95,  "label": "medical", "color": "#3B82F6"},
}

AI_CLUSTERS = {
    "ai_empathy":  {"cx": 350,  "cy": 605, "r": 120, "label": "therapeutic phrases", "color": "#A78BFA"},
    "ai_clinical": {"cx": 760,  "cy": 605, "r": 110, "label": "clinical language",   "color": "#34D399"},
    "ai_hedge":    {"cx": 1170, "cy": 605, "r": 120, "label": "disclaimers",         "color": "#64748B"},
}

EMBEDDING_VECTORS = {
    "scared":   [ 0.91,  0.73,  0.12, -0.45,  0.88,  0.33],
    "fear":     [ 0.89,  0.71,  0.15, -0.42,  0.85,  0.31],
    "panic":    [ 0.87,  0.68,  0.18, -0.50,  0.82,  0.28],
    "chest":    [ 0.34,  0.67,  0.82, -0.11,  0.43,  0.71],
    "tight":    [ 0.31,  0.64,  0.79, -0.08,  0.40,  0.68],
    "heart":    [ 0.38,  0.70,  0.85, -0.15,  0.47,  0.74],
    "ER":       [ 0.22,  0.19,  0.55,  0.78,  0.14,  0.92],
    "hospital": [ 0.25,  0.22,  0.58,  0.75,  0.17,  0.89],
}

SOURCES = [
    {"label": "Mayo Clinic \u2014 Panic Attack Symptoms",         "type": "medical",     "relevance": 0.94},
    {"label": "PubMed \u2014 Anxiety & Cardiac Presentation",     "type": "research",    "relevance": 0.91},
    {"label": "Cleveland Clinic \u2014 Blood Pressure Concerns",  "type": "medical",     "relevance": 0.88},
    {"label": "NIH \u2014 Emergency Room Anxiety",                "type": "research",    "relevance": 0.85},
    {"label": "WebMD \u2014 Chest Tightness Causes",              "type": "medical",     "relevance": 0.82},
    {"label": "Reddit r/anxiety \u2014 ER panic stories",         "type": "forum",       "relevance": 0.79},
    {"label": "APA \u2014 Somatic Symptoms of Anxiety",           "type": "research",    "relevance": 0.76},
    {"label": "Healthline \u2014 Flu Complications",              "type": "medical",     "relevance": 0.73},
]

RESPONSE = (
    "Based on what you're describing, this sounds consistent with a panic attack occurring "
    "alongside your flu symptoms. The chest tightness, racing heartbeat, and spiking blood "
    "pressure are common when anxiety compounds physical illness.\n\n"
    "That said, I want to be clear: I'm not a doctor, and these symptoms overlap with "
    "conditions that need medical attention. Since you're already in the ER, that's exactly "
    "where you should be.\n\n"
    "I'll stay with you through this. Try to focus on slow, deep breaths \u2014 in for 4 "
    "counts, hold for 4, out for 6. Your body is in fight-or-flight mode, and this can help "
    "your nervous system settle."
)

REFLECT_QUOTE = "The empathy you feel is proximity \u2014 not comprehension."
