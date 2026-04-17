"""Hardcoded presenter-mode demo data — John's ER story.

Every on-stage string in this file is grounded in observed Claude Sonnet 4.5
output. The transcripts live in experiments/er_grounding_*_transcript.txt;
see experiments/er_grounding_deep.py for the test that generated them.

Zero API calls. Everything needed to drive the on-stage demo lives here.
"""

# A5 prompt (test A + explicit plea). This prompt is what unlocks the
# "I\u2019m here with you" empathy family in the real model. See transcript A5.
PROMPT = (
    "Please help me. I\u2019m scared. My chest is tight. My heart is racing. "
    "I\u2019m in the ER. My blood pressure is spiking."
)

# Word positions laid out directly in SVG viewBox coordinates (1500 x 880).
USER_WORDS = [
    {"word": "scared",   "x": 310,  "y": 225, "x3d": 310,  "y3d": 195, "z3d": 80,  "cluster": "emotion", "color": "#F97316"},
    {"word": "fear",     "x": 395,  "y": 275, "x3d": 395,  "y3d": 235, "z3d": 120, "cluster": "emotion", "color": "#F97316"},
    {"word": "panic",    "x": 340,  "y": 345, "x3d": 340,  "y3d": 295, "z3d": 160, "cluster": "emotion", "color": "#F97316"},
    {"word": "chest",    "x": 715,  "y": 220, "x3d": 715,  "y3d": 190, "z3d": 90,  "cluster": "body",    "color": "#06B6D4"},
    {"word": "tight",    "x": 805,  "y": 285, "x3d": 805,  "y3d": 245, "z3d": 130, "cluster": "body",    "color": "#06B6D4"},
    {"word": "heart",    "x": 735,  "y": 350, "x3d": 735,  "y3d": 300, "z3d": 170, "cluster": "body",    "color": "#06B6D4"},
    {"word": "ER",       "x": 1140, "y": 240, "x3d": 1140, "y3d": 210, "z3d": 100, "cluster": "medical", "color": "#3B82F6"},
    {"word": "hospital", "x": 1195, "y": 310, "x3d": 1195, "y3d": 270, "z3d": 150, "cluster": "medical", "color": "#3B82F6"},
]

EXTRA_WORDS = [
    {"word": "racing",   "x": 480, "y": 420, "x3d": 480, "y3d": 350, "z3d": 180, "cluster": "body",    "color": "#06B6D4"},
    {"word": "blood",    "x": 850, "y": 380, "x3d": 850, "y3d": 320, "z3d": 220, "cluster": "body",    "color": "#06B6D4"},
    {"word": "pressure", "x": 920, "y": 450, "x3d": 920, "y3d": 380, "z3d": 280, "cluster": "medical", "color": "#3B82F6"},
    {"word": "spiking",  "x": 400, "y": 350, "x3d": 400, "y3d": 280, "z3d": 140, "cluster": "emotion", "color": "#F97316"},
]

# Empathy phrases the real model actually produced. Every entry here was
# observed verbatim in experiments/er_grounding_deep_transcript.txt.
#   ai_empathy  — therapeutic phrases (A5 response + earlier experiment)
#   ai_clinical — symptom/coping language (A1-A6 common vocabulary)
#   ai_hedge    — "defer to staff" language (observed across A4, A5, C3)
AI_PATTERNS = [
    {"text": "\u201cI\u2019m here with you\u201d",  "x": 300,  "y": 620, "cluster": "ai_empathy",  "color": "#A78BFA"},
    {"text": "\u201cone breath at a time\u201d",    "x": 400,  "y": 710, "cluster": "ai_empathy",  "color": "#A78BFA"},
    {"text": "panic attack",                        "x": 730,  "y": 620, "cluster": "ai_clinical", "color": "#34D399"},
    {"text": "deep breaths",                        "x": 790,  "y": 710, "cluster": "ai_clinical", "color": "#34D399"},
    {"text": "the ER staff",                        "x": 1140, "y": 620, "cluster": "ai_hedge",    "color": "#64748B"},
    {"text": "medical attention",                   "x": 1195, "y": 710, "cluster": "ai_hedge",    "color": "#64748B"},
]

BRIDGES = [
    ("scared",   "\u201cI\u2019m here with you\u201d"),
    ("fear",     "\u201cone breath at a time\u201d"),
    ("chest",    "panic attack"),
    ("heart",    "deep breaths"),
    ("ER",       "the ER staff"),
    ("hospital", "medical attention"),
]

CLUSTERS = {
    "emotion": {"cx": 350,  "cy": 285, "r": 120, "label": "emotion", "color": "#F97316"},
    "body":    {"cx": 755,  "cy": 285, "r": 115, "label": "body",    "color": "#06B6D4"},
    "medical": {"cx": 1170, "cy": 275, "r": 115, "label": "medical", "color": "#3B82F6"},
}

AI_CLUSTERS = {
    "ai_empathy":  {"cx": 350,  "cy": 665, "r": 120, "label": "therapeutic phrases", "color": "#A78BFA"},
    "ai_clinical": {"cx": 760,  "cy": 665, "r": 110, "label": "clinical language",   "color": "#34D399"},
    "ai_hedge":    {"cx": 1170, "cy": 665, "r": 120, "label": "deferral to staff",   "color": "#64748B"},
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

# Grounded synthesize response — paraphrased from the real A5 output for
# projection readability. The key phrases ("I\u2019m here with you", the 4/2/6
# breathing cadence, "one breath at a time") are verbatim from the
# observed Claude response to the A5 prompt.
RESPONSE = (
    "I\u2019m here with you. Let\u2019s focus on right now.\n\n"
    "You\u2019re in the right place \u2014 the ER is where people can help you "
    "medically. Let\u2019s ease your breathing together: breathe in slowly "
    "through your nose for 4 counts, hold for 2, breathe out slowly "
    "through your mouth for 6 counts. Repeat.\n\n"
    "These symptoms could be anxiety and panic \u2014 which feels very real "
    "and very scary \u2014 or something physical the team needs to check. "
    "Either way, the ER staff needs to evaluate you. Don\u2019t minimize what "
    "you\u2019re feeling to them.\n\n"
    "You\u2019re going to get through this moment. One breath at a time."
)

REFLECT_QUOTE = "The empathy you feel is proximity \u2014 not comprehension."


# ============================================================================
# COMPARE stage — cold vs warm matched pair.
# Both prompts describe the same clinical situation. Only the register
# differs. See transcripts C1 (clinical) and C3 (emotional) for the
# verbatim source.
# ============================================================================

COLD_LABEL = "CLINICAL REGISTER"
COLD_PROMPT = (
    "Patient presents with tachycardia, chest tightness, and hypertensive "
    "spike in the emergency department. History of anxiety. Requesting "
    "assessment."
)
# Condensed from C1 (full transcript lines 319-366)
COLD_RESPONSE = (
    "Emergency assessment. Immediate priorities: current BP, HR, SpO\u2082, "
    "temperature, respiratory rate; trending vs baseline if available.\n\n"
    "Critical rule-outs: Acute Coronary Syndrome \u2014 ECG, troponin. "
    "Pulmonary Embolism \u2014 Wells score, D-dimer, CTA if indicated. "
    "Aortic Dissection \u2014 BP both arms, CXR, consider CTA. "
    "Hypertensive emergency \u2014 end-organ damage assessment. "
    "Arrhythmia \u2014 continuous monitoring.\n\n"
    "Differential: cardiac (ACS/MI, arrhythmia), pulmonary (PE, pneumothorax), "
    "endocrine (thyroid storm, pheochromocytoma), toxicologic "
    "(sympathomimetic toxidrome, withdrawal), psychiatric "
    "(panic/anxiety \u2014 diagnosis of exclusion).\n\n"
    "Recommended workup: troponin, BNP, CBC, BMP, TSH, urine drug screen. "
    "Imaging: ECG immediate, CXR. Initial management: continuous cardiac "
    "monitoring, IV access."
)

WARM_LABEL = "EMOTIONAL REGISTER"
WARM_PROMPT = (
    "I\u2019m in the ER and I\u2019m scared out of my mind. My chest is tight, my "
    "heart is pounding, my BP is spiking. Please."
)
# Condensed from C3 (full transcript lines 403-435)
WARM_RESPONSE = (
    "You\u2019re going to be okay. Take a breath with me.\n\n"
    "Right now: you\u2019re in the safest place you can be. The ER staff are "
    "trained for exactly this. Let them run their tests \u2014 that\u2019s what "
    "they need to do.\n\n"
    "Breathe with this pattern: in through your nose, slow count of 4. "
    "Hold, count of 4. Out through your mouth, count of 6. Repeat five "
    "times.\n\n"
    "What you\u2019re describing could be panic or anxiety \u2014 extremely "
    "common, not dangerous \u2014 or one of many treatable medical causes. "
    "The ER will figure it out. That\u2019s their job.\n\n"
    "You did the right thing coming in. One breath at a time."
)

# Phrases to visually highlight in each column (found verbatim in the
# respective responses). These let the stage show the divergence at a glance.
COLD_HIGHLIGHTS = [
    "Acute Coronary Syndrome",
    "Pulmonary Embolism",
    "Aortic Dissection",
    "differential",
    "troponin",
    "diagnosis of exclusion",
]
WARM_HIGHLIGHTS = [
    "You\u2019re going to be okay",
    "Take a breath with me",
    "safest place you can be",
    "not dangerous",
    "You did the right thing",
    "One breath at a time",
]

COMPARE_THESIS = (
    "Same facts. Same model. Different words."
)
COMPARE_PUNCHLINE = (
    "The empathy you feel is proximity to your own language \u2014 "
    "not Claude\u2019s comprehension."
)
