---
title: Ask Anything Lab
emoji: 🧠
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: "5.12.0"
app_file: app.py
pinned: true
license: mit
short_description: "See what happens when AI processes your words"
---

# Ask Anything Lab

Live companion visualization for John Patterson's TEDx talk *"Ask Anything: AI, Emotion, and Influence"* (May 1, 2026).

Two modes share one URL:

- **Presenter** — clicker-controlled stage demo, hardcoded ER-story data, zero API calls, zero latency
- **Audience** — 300 attendees visit a QR code, type their own prompt, watch it embed/retrieve/synthesize live, answer three study questions

## Run locally

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open http://localhost:7860

## Environment variables

```
ANTHROPIC_API_KEY=    # required for audience mode (falls back to placeholder data otherwise)
SUPABASE_URL=         # Supabase project URL
SUPABASE_ANON_KEY=    # Supabase anon / public key (insert-only via RLS)
```

Without Supabase keys, study submissions log to stdout (`[STUDY] {...}`).

## Keyboard / clicker controls (presenter mode)

| Action  | Keys                                          |
|---------|-----------------------------------------------|
| Forward | ArrowRight, Space, PageDown, ArrowDown, Enter |
| Back    | ArrowLeft, PageUp, ArrowUp, Backspace         |

## Supabase schema

```sql
CREATE TABLE tedx_study (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id TEXT NOT NULL,
  prompt TEXT,
  q1_surprising_stage TEXT,
  q2_trust_before INT,
  q3_trust_after INT,
  created_at TIMESTAMPTZ DEFAULT now()
);
ALTER TABLE tedx_study ENABLE ROW LEVEL SECURITY;
CREATE POLICY "anon_insert" ON tedx_study FOR INSERT TO anon WITH CHECK (true);
CREATE POLICY "service_read" ON tedx_study FOR SELECT TO service_role USING (true);
```
