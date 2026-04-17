"""Study questions stage (audience mode)."""

# (value, label) tuples — value is what we store in Supabase
SURPRISING_OPTIONS = [
    ("embed",      "The embedding step \u2014 words becoming numbers"),
    ("retrieve",   "The retrieval step \u2014 finding nearby sources"),
    ("synthesize", "The synthesis step \u2014 stitching it into a response"),
    ("influence",  "The influence analysis \u2014 seeing persuasion techniques identified"),
    ("none",       "Nothing really surprised me"),
]


def study_intro_html():
    return """
<div style="background:#06080C; padding: 3em 3em 1em;">
  <div style="max-width: 800px; margin: 0 auto;">
    <div style="color:#64748B; font-size: 0.95em; letter-spacing:0.2em; text-transform:uppercase; margin-bottom: 0.6em;">
      Three quick questions
    </div>
    <h2 style="color: #F1F5F9; font-size: 2em; margin-top: 0; font-weight: 600;">
      You&rsquo;ve seen how it works. Now we ask you.
    </h2>
    <p style="color: #64748B; font-size: 1.1em; line-height: 1.55;">
      Your answers are anonymous. They&rsquo;ll help John&rsquo;s book
      <em>Ask Anything: AI, Emotion, and Influence</em> document how people&rsquo;s trust
      shifts once they see the mechanism.
    </p>
  </div>
</div>
"""


def thanks_html():
    return """
<div style="background:#06080C; padding: 5em 3em; text-align: center; min-height: 60vh;">
  <div style="color:#F59E0B; font-size: 0.95em; letter-spacing:0.25em; text-transform:uppercase; margin-bottom: 1em;">
    recorded
  </div>
  <h2 style="color: #F1F5F9; font-size: 2.8em; margin: 0.3em 0; font-weight: 700;">Thank you.</h2>
  <p style="color: #64748B; font-size: 1.3em; max-width: 640px; margin: 1em auto;">
    Your response is in the dataset that will become the book.<br/>
    Enjoy the rest of the talk.
  </p>
  <div style="color:#475569; margin-top: 3em; font-style: italic; font-size: 1.3em;">
    &ldquo;The empathy you feel is proximity &mdash; not comprehension.&rdquo;
  </div>
</div>
"""
