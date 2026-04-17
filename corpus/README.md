# Corpus Analysis — AI Emotion & Influence

Research pipeline for John Patterson's TEDx talk *"Ask Anything: AI, Emotion, and Influence"*.

Takes real user prompts sent to ChatGPT (from the public WildChat-1M corpus), classifies their
emotional content, clusters them semantically, and labels each cluster using the vocabulary of
the talk. Produces the evidence artifacts used in the book.

## Pipeline

```
fetch_corpus.py      →  data/prompts.parquet      (N prompts, text + source metadata)
classify_emotions.py →  data/emotions.parquet     (28-dim GoEmotions probabilities)
embed_prompts.py     →  data/embeddings.npy       (384-dim semantic vectors)
cluster_topics.py    →  data/clusters.parquet     (UMAP + HDBSCAN cluster id per prompt)
label_clusters.py    →  data/labels.json          (Claude-generated label + talk theme mapping)
analyze.py           →  out/*.png + out/*.csv     (heatmaps, exemplars, summary tables)
```

Run each script in order, or use `python run_all.py`.

## Talk taxonomy

The labeling step uses these themes from the TEDx talk:

1. `crisis-companionship` — 2am, ER, reassurance-under-threat
2. `information-seeking` — diagnostic / factual / search-replacement
3. `emotional-validation` — "that makes sense you'd feel that way"
4. `judgment-outsourcing` — asking AI to decide for you
5. `mechanism-curiosity` — asking how AI itself works
6. `influence-at-scale` — marketing, persuasion, brand, audience
7. `ambient-companionship` — loneliness / social substitute
8. `high-stakes-decision` — health / money / child / relationship
9. `low-stakes-utility` — recipes, trivia, homework
10. `validation-seeking` — confirm an existing belief

Clusters that don't fit any theme are tagged `new` — those are the surprises the corpus reveals.
