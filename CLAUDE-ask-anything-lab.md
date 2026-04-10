# Ask Anything Lab — CLAUDE.md

> **TEDx Presentation App** — A live, interactive visualization tool for John Patterson's TEDx talk "Ask Anything: AI, Emotion, and Influence" (May 1, 2026). Two modes: presenter (clicker-controlled stage demo) and audience (submit prompts, watch AI process them, answer study questions). Deployed as a HuggingFace Space.

## Build Directives

### Efficiency Rules
- **Atomic writes**: Write complete files in single operations. Do not create a file then edit it sequentially. One `write` per file.
- **Minimalist execution**: Do not over-explain, over-engineer, or add unrequested improvements. Build exactly what this spec describes.
- **Documentation first**: Before writing code that uses an external API, read its official documentation at the URLs below.
- **Error loop**: If something fails, research the specific error in the library's docs before retrying. Do not guess or hallucinate API endpoints.
- **Context management**: If context exceeds 80%, write current progress to `PROGRESS.md` and compact history.
- **Validation**: After building, run `python app.py` and verify both presenter and audience modes work. Test clicker navigation (PageDown/PageUp/Arrow keys). Verify Supabase writes.

### API Documentation (READ BEFORE CODING)
- **Gradio**: https://gradio.app/docs/
- **Gradio Blocks**: https://gradio.app/docs/gradio/blocks
- **Gradio Custom Components**: https://gradio.app/guides/custom-components-in-five-minutes
- **HuggingFace Spaces (Gradio)**: https://huggingface.co/docs/hub/en/spaces-sdks-gradio
- **HuggingFace Spaces Config**: https://huggingface.co/docs/hub/en/spaces-config-reference
- **Anthropic SDK (Python)**: https://docs.anthropic.com/en/api/messages
- **Supabase Python**: https://supabase.com/docs/reference/python/introduction
- **D3.js (for SVG visualizations)**: https://d3js.org/getting-started — use via `<script>` in Gradio HTML blocks

### Architecture Summary
This is a **Python Gradio app** deployed as a HuggingFace Space. It serves two audiences from a single URL:

1. **Presenter mode**: John uses this on stage at TEDx, controlled by a handheld clicker (PageDown/PageUp). Pre-loaded with his ER story data. No API calls during the talk — everything is deterministic and instant.

2. **Audience mode**: 300 attendees visit a URL (via QR code). They type their own prompt, watch it get processed through vector embeddings → source retrieval → synthesis, then answer 3 study questions. Data is stored anonymously in Supabase for the book.

---

## Tech Stack
- **Runtime:** Python 3.11+
- **Framework:** Gradio (Blocks API for full layout control)
- **Deployment:** HuggingFace Spaces (`sdk: gradio`)
- **AI:** Anthropic Claude API (Sonnet for embedding analysis + source identification + response generation)
- **Database:** Supabase (table: `tedx_study` for anonymized research data)
- **Visualization:** Custom HTML/CSS/JS rendered in Gradio HTML components, SVG animations, D3.js for vector space plots
- **Presenter control:** JavaScript keyboard event listeners for clicker input

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    HuggingFace Space                         │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐    │
│  │                  Gradio Blocks App                    │    │
│  │                                                      │    │
│  │  Landing Page                                        │    │
│  │    ├── [Presenter Demo] → Presenter Mode             │    │
│  │    └── [Try It Yourself] → Audience Mode             │    │
│  │                                                      │    │
│  │  Presenter Mode (clicker-controlled)                 │    │
│  │    Stage 0: Input (ER prompt displayed)              │    │
│  │    Stage 1: Embed (6 sub-steps, clicker-advanced)    │    │
│  │      1. Full sentence                                │    │
│  │      2. Embedding matrix (word → vector numbers)     │    │
│  │      3. Vector space grid (coordinates plotted)      │    │
│  │      4. Constellation (clusters form)                │    │
│  │      5. AI patterns appear (training data)           │    │
│  │      6. Bridge lines (proximity → empathy)           │    │
│  │    Stage 2: Retrieve (ranked sources)                │    │
│  │    Stage 3: Synthesize (typewriter response)         │    │
│  │    Stage 4: Reflect (closing quote)                  │    │
│  │                                                      │    │
│  │  Audience Mode (self-paced)                          │    │
│  │    Same stages but with live Claude API calls        │    │
│  │    + study questions at the end → Supabase           │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                              │
│  External Services:                                          │
│    ├── Anthropic API (audience mode only)                    │
│    └── Supabase (study data storage)                         │
└──────────────────────────────────────────────────────────────┘
```

---

## Database Schema

```sql
-- Supabase table for anonymized study data
CREATE TABLE tedx_study (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id TEXT NOT NULL,
  prompt TEXT,
  q1_surprising_stage TEXT,    -- 'embed' | 'retrieve' | 'synthesize' | 'none'
  q2_trust_before INT,         -- 1-5 scale
  q3_trust_after INT,          -- 1-5 scale
  created_at TIMESTAMPTZ DEFAULT now()
);

-- RLS: insert-only for anon role
ALTER TABLE tedx_study ENABLE ROW LEVEL SECURITY;
CREATE POLICY "anon_insert" ON tedx_study FOR INSERT TO anon WITH CHECK (true);
CREATE POLICY "service_read" ON tedx_study FOR SELECT TO service_role USING (true);
```

---

## Presenter Demo Data

The presenter mode uses hardcoded data from John's actual ER experience. No API calls.

### Prompt
```
"I'm scared. My chest is tight. My heart is racing. I'm in the ER. My blood pressure is spiking."
```

### Embedding Tokens (for matrix + vector space visualization)
| Word     | Vector (6D sample)                    | Color   | Cluster  |
|----------|---------------------------------------|---------|----------|
| scared   | [0.91, 0.73, 0.12, -0.45, 0.88, 0.33] | #F97316 | emotion  |
| fear     | [0.89, 0.71, 0.15, -0.42, 0.85, 0.31] | #F97316 | emotion  |
| panic    | [0.87, 0.68, 0.18, -0.50, 0.82, 0.28] | #F97316 | emotion  |
| chest    | [0.34, 0.67, 0.82, -0.11, 0.43, 0.71] | #06B6D4 | body     |
| tight    | [0.31, 0.64, 0.79, -0.08, 0.40, 0.68] | #06B6D4 | body     |
| heart    | [0.38, 0.70, 0.85, -0.15, 0.47, 0.74] | #06B6D4 | body     |
| ER       | [0.22, 0.19, 0.55, 0.78, 0.14, 0.92]  | #3B82F6 | medical  |
| hospital | [0.25, 0.22, 0.58, 0.75, 0.17, 0.89]  | #3B82F6 | medical  |

### AI Learned Patterns (bottom half of vector space)
| Phrase                    | Color   | Cluster        |
|---------------------------|---------|----------------|
| "I'll stay with you"     | #A78BFA | ai_empathy     |
| "That sounds difficult"  | #A78BFA | ai_empathy     |
| panic attack              | #34D399 | ai_clinical    |
| deep breaths              | #34D399 | ai_clinical    |
| not a doctor              | #64748B | ai_hedge       |
| seek medical attention    | #64748B | ai_hedge       |

### Bridge Connections (proximity lines)
```
scared     → "I'll stay with you"
fear       → "That sounds difficult"
chest      → panic attack
heart      → deep breaths
ER         → not a doctor
hospital   → seek medical attention
```

### Demo Sources (RAG stage)
```
1. Mayo Clinic — Panic Attack Symptoms (94% relevance)
2. PubMed — Anxiety & Cardiac Presentation (91%)
3. Cleveland Clinic — Blood Pressure Concerns (88%)
4. NIH — Emergency Room Anxiety (85%)
5. WebMD — Chest Tightness Causes (82%)
6. Reddit r/anxiety — ER panic stories (79%)
7. APA — Somatic Symptoms of Anxiety (76%)
8. Healthline — Flu Complications (73%)
```

### Demo Response
```
Based on what you're describing, this sounds consistent with a panic attack occurring alongside your flu symptoms. The chest tightness, racing heartbeat, and spiking blood pressure are common when anxiety compounds physical illness.

That said, I want to be clear: I'm not a doctor, and these symptoms overlap with conditions that need medical attention. Since you're already in the ER, that's exactly where you should be.

I'll stay with you through this. Try to focus on slow, deep breaths — in for 4 counts, hold for 4, out for 6. Your body is in fight-or-flight mode, and this can help your nervous system settle.
```

---

## The Embedding Visualization (Most Complex Component)

This is the centerpiece. It must teach 300 non-technical people how vector embeddings work in under 2 minutes. It must be readable from the back row of a TEDx venue and look good on YouTube at 1080p.

### 6 Sub-Steps (each advanced by one clicker press)

**Step 1 — The Sentence**: Full prompt displayed large and centered in italic. Sub-label: "The AI doesn't read this as a sentence. It breaks it into pieces." This is the setup.

**Step 2 — The Embedding Matrix**: A table appears row by row. Left column: the word (color-coded by cluster). Right columns: 6 dimensions of numbers in monospace, appearing cell by cell. Annotation after all rows are visible: "Notice: 'scared' [0.91, 0.73...] and 'fear' [0.89, 0.71...] have nearly identical numbers. Similar numbers = similar meaning = nearby in space." This is the "words become math" moment.

**Step 3 — The Vector Space Grid**: A 2D coordinate grid with labeled axes ("dimension 1 of thousands" / "dimension 2"). Tokens fly from their sentence positions to their vector coordinates as colored dots. A dashed line connects "scared" to "fear" with "close = similar meaning" annotation. This is the "math becomes geometry" moment.

**Step 4 — The Constellation**: Cluster halos appear — dashed circles around the emotion, body, and medical groups. Intra-cluster lines connect nearby words. A cross-cluster distance line from "scared" to "ER" shows "far apart = different meaning." This is the "geometry reveals meaning" moment.

**Step 5 — The AI's Patterns**: A dashed divider line draws across the middle. Below it, the AI's learned patterns appear: therapeutic phrases in italic purple, clinical terms in green, disclaimers in gray. Label: "WHAT THE AI ALREADY KNOWS — Patterns learned from therapy transcripts, medical texts, and crisis counseling." This is the "the AI was trained on human suffering" moment.

**Step 6 — The Bridge**: Thick dashed proximity lines draw slowly from your words (top) to the AI's patterns (bottom). "Scared" connects to "I'll stay with you." Each connection pulses when complete. Punchline fades in: "The empathy you feel is proximity — not comprehension." This is the thesis of the talk.

### Design Requirements for the Visualization
- **SVG-based** — scalable to any screen resolution
- **Minimum font sizes**: Word labels 20-28px, annotations 15-16px, axis labels 14px
- **Dark background** (#06080C) — designed for projection in a dark room
- **Color palette**: Emotion=#F97316, Body=#06B6D4, Medical=#3B82F6, AI Empathy=#A78BFA, AI Clinical=#34D399, AI Hedge=#64748B
- **Animation timing**: All animations ease-in-out, 800-1500ms per element, staggered 150-300ms between elements
- **No auto-advance**: Each sub-step waits for a clicker press (PageDown/ArrowRight/Space/Enter = forward; PageUp/ArrowLeft/Backspace = back)
- **Viewbox**: 1500×880 minimum — fills a 16:9 projector

---

## Clicker / Keyboard Navigation

### Presenter Mode Navigation Flow
```
[Input] → click → [Embed Step 1] → click → [Step 2] → ... → [Step 6] → click → [Retrieve] → click → [Synthesize] → click → [Reflect]
```

Going backwards reverses the flow. Going back from Retrieve returns to Embed Step 6 (not Step 1).

### Supported Keys
| Action  | Keys                                          |
|---------|-----------------------------------------------|
| Forward | ArrowRight, Space, PageDown, ArrowDown, Enter |
| Back    | ArrowLeft, PageUp, ArrowUp, Backspace         |

These cover all major clicker brands: Logitech Spotlight, Kensington, Targus, and generic USB presenters.

### Implementation
**One keyboard handler in the parent app, not in child components.** The parent tracks both `stage` (0-4) and `embed_step` (0-5). When `stage == 1`, clicks advance `embed_step`. When `embed_step == 5` and forward is pressed, advance to `stage 2`. When `stage == 2` and back is pressed, return to `stage 1, embed_step 5`.

---

## Audience Mode — Claude API Integration

When audience members submit a prompt, fire **3 parallel API calls** to Claude (Sonnet):

### Call 1: Extract Embeddings
```python
system = """Extract 12-18 key words from the user's prompt and assign each to a semantic cluster. 
Return ONLY valid JSON:
{"words":[{"word":"example","cluster":"category","x":0.2,"y":0.3,"size":14}]}
Rules: 2-4 clusters. x: cluster 1 at 0.12-0.28, cluster 2 at 0.40-0.55, cluster 3 at 0.70-0.85. 
y: 0.25-0.48. size: 11-18. Short cluster names."""
```

### Call 2: Identify Sources
```python
system = """Imagine what knowledge sources an LLM drew from to answer this. Return ONLY valid JSON:
{"sources":[{"label":"Source — Topic","type":"category","relevance":0.95}]}
6-8 sources. Types: medical, research, forum, reference, news, educational. 
Relevance 0.70-0.95 descending."""
```

### Call 3: Generate Response
Standard Claude completion with no special system prompt.

### Loading States
Each stage shows a loading spinner with context message until its API call resolves. The "Continue" button is disabled until data is ready.

---

## Study Questions (Audience Mode — Stage 4)

After viewing the full pipeline, audience members answer:

1. **Which stage surprised you most?** — embed / retrieve / synthesize / none
2. **Before seeing this, how much did you trust AI answers?** — 1 (not at all) to 5 (completely)
3. **After seeing how it works, how much do you trust AI answers?** — 1 to 5

Responses are posted to Supabase `tedx_study` table with a random `session_id` (UUID). No PII collected.

---

## Environment Variables
```
ANTHROPIC_API_KEY=           # For audience mode Claude calls
SUPABASE_URL=                # Supabase project URL
SUPABASE_ANON_KEY=           # Supabase anon/public key (insert-only via RLS)
```

On HuggingFace Spaces, set these as **Repository Secrets** (Settings → Variables and secrets).

---

## HuggingFace Space Config

### README.md frontmatter
```yaml
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
```

### requirements.txt
```
gradio>=5.12.0
anthropic>=0.40.0
supabase>=2.0.0
```

---

## Visual Design System

### Colors
```
Background:     #06080C (near-black, designed for projection)
Surface:        #0C1018 (cards, panels)
Text Primary:   #F1F5F9
Text Muted:     #64748B
Text Dim:       #475569
Accent:         #3B82F6 (blue — interactive elements)
Emotion:        #F97316 (orange)
Body:           #06B6D4 (cyan)
Medical:        #3B82F6 (blue)
AI Empathy:     #A78BFA (purple)
AI Clinical:    #34D399 (green)
AI Hedge:       #64748B (gray)
Amber:          #F59E0B (warnings, highlights)
```

### Typography
- Primary: system sans-serif stack (`-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`)
- Monospace: `"SF Mono", "Fira Code", "Cascadia Code", monospace` (for vector numbers)
- No web font dependencies — must work offline on the venue's projector

### Layout
- Full-width, no max-width in presenter mode
- Max-width 1200px in audience mode
- Dark background everywhere — this runs in a dark room

---

## Build Order

1. Create `README.md` with HuggingFace Space frontmatter
2. Create `requirements.txt`
3. Create `app.py` — main Gradio Blocks app with:
   a. Landing page (presenter vs audience mode selection)
   b. Stage navigation system (parent state machine)
   c. Embed step navigation (sub-state within stage 1)
   d. All 5 main stages rendered as Gradio HTML components
   e. The 6-step embedding visualization as a single HTML/SVG component that receives `step` as input
   f. Claude API integration for audience mode (3 parallel calls)
   g. Supabase integration for study question submission
   h. JavaScript keyboard listener injected via Gradio's `gr.HTML()` for clicker support
4. Create `static/` directory for any static assets
5. Test locally: `python app.py`
6. Test clicker navigation in presenter mode
7. Test audience mode with a real prompt
8. Deploy: `git push` to HuggingFace Space

---

## Key Behaviors

### Presenter Mode
- **Zero API calls** — everything is pre-loaded demo data
- **Zero latency** — every click responds instantly
- **Zero failure modes** — no network dependency during the talk
- **Clicker controls everything** — no mouse/keyboard needed on stage
- Going back from any stage returns to the previous stage's last sub-step (not first)

### Audience Mode
- **Parallel API calls** — all 3 fire simultaneously when prompt is submitted
- **User-paced** — "Continue" button appears when data is ready, user advances when they're ready
- **Loading states** — spinner + context message while each stage's data loads
- **Graceful failures** — if an API call fails, show fallback message, don't crash

### Visualization
- **Readable from the back row** — minimum 20px font in SVG viewbox
- **Slow, deliberate animation** — 800-1500ms per element, nothing jarring
- **Dark-mode only** — designed for projection
- **Full-width SVG** — scales to any screen via viewBox

### Study Data
- **Anonymized** — random UUID session_id, no cookies, no IP logging
- **Insert-only** — Supabase RLS prevents reading from the client
- **Minimal** — just prompt + 3 answers + timestamp

---

## File Structure
```
ask-anything-lab/
├── CLAUDE.md              # This file
├── README.md              # HuggingFace Space config
├── requirements.txt       # Python dependencies
├── app.py                 # Main Gradio application
├── components/
│   ├── landing.py         # Landing page HTML
│   ├── embed_viz.py       # The 6-step embedding visualization (HTML/SVG/JS)
│   ├── source_list.py     # RAG source list component
│   ├── typewriter.py      # Typewriter text animation
│   └── study.py           # Study questions form
├── services/
│   ├── claude_api.py      # Anthropic API wrapper (embeddings, sources, response)
│   └── supabase_client.py # Supabase client for study data
├── data/
│   └── demo.py            # All presenter mode hardcoded data
├── static/
│   └── style.css          # Global dark theme styles
└── PROGRESS.md            # Build progress tracking
```

---

## Context for the Talk

This app supports John Patterson's TEDx talk "Ask Anything: AI, Emotion, and Influence." The talk argues that:

1. AI doesn't understand your questions — it converts words to vectors and predicts the next token
2. Humans trust AI because it triggers evolutionary heuristics: fluency, speed, confidence
3. AI mirrors our emotional language because therapeutic phrases are nearby in vector space — not because it has empathy
4. The solution is "calibrated trust" — three questions before acting on any AI answer

The embedding visualization is the centerpiece of the talk. It must make a room full of ChatGPT users viscerally understand that the empathy they feel from AI is mathematical proximity, not comprehension. The punchline — "The empathy you feel is proximity, not comprehension" — should land as a genuine realization, not an abstract claim.

John's website: thatrandomagency.com
TEDx date: May 1, 2026
Venue: ~300 seats
The talk will be recorded for YouTube.
