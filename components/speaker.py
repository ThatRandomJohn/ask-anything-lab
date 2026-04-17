"""Speaker / Book John page with contact form."""

SPEAKER_HTML = """
<div class="aal-speaker">
  <div class="aal-speaker-aurora">
    <div class="aal-aurora-blob aal-blob-orange"></div>
    <div class="aal-aurora-blob aal-blob-cyan"></div>
    <div class="aal-aurora-blob aal-blob-purple"></div>
  </div>
  <div class="aal-grid-overlay"></div>

  <div class="aal-speaker-content">
    <div class="aal-speaker-eyebrow">
      <span class="aal-eyebrow-dot"></span>
      Speaker
    </div>

    <div class="aal-speaker-hero">
      <div class="aal-speaker-info">
        <h1 class="aal-speaker-name">John Patterson</h1>
        <p class="aal-speaker-role">Founder, That Random Agency</p>
        <p class="aal-speaker-bio">
          John helps organizations understand the invisible mechanics of AI &mdash;
          how language models embed, retrieve, and synthesize meaning &mdash; and what
          that means for trust, influence, and the questions we choose to ask.
        </p>
        <p class="aal-speaker-bio">
          His TEDx talk, <em>&ldquo;Ask Anything: AI, Emotion, and Influence,&rdquo;</em>
          walks audiences through a live AI pipeline to reveal the surprising relationship
          between how we phrase a question and the empathy of the answer we receive.
        </p>
        <div class="aal-speaker-topics">
          <span class="aal-topic-tag">AI Literacy</span>
          <span class="aal-topic-tag">Prompt Engineering</span>
          <span class="aal-topic-tag">Trust &amp; Influence</span>
          <span class="aal-topic-tag">Live AI Demos</span>
        </div>
      </div>
    </div>

    <div class="aal-speaker-form-section">
      <h2 class="aal-form-title">Book John for your event</h2>
      <p class="aal-form-subtitle">
        Keynotes, workshops, and panels &mdash; tailored to your audience.
      </p>
      <form class="aal-contact-form" id="aal-contact-form">
        <div class="aal-form-row">
          <div class="aal-form-field">
            <label for="aal-name">Your name</label>
            <input type="text" id="aal-name" name="name" required placeholder="Jane Smith" />
          </div>
          <div class="aal-form-field">
            <label for="aal-email">Email</label>
            <input type="email" id="aal-email" name="email" required placeholder="jane@company.com" />
          </div>
        </div>
        <div class="aal-form-field">
          <label for="aal-org">Organization</label>
          <input type="text" id="aal-org" name="organization" placeholder="Acme Corp" />
        </div>
        <div class="aal-form-field">
          <label for="aal-event">Tell me about your event</label>
          <textarea id="aal-event" name="event" rows="4" required
            placeholder="Date, audience size, format (keynote / workshop / panel), and anything else that would help me prepare."></textarea>
        </div>
        <button type="submit" class="aal-form-submit">Send inquiry &rarr;</button>
        <div class="aal-form-status" id="aal-form-status"></div>
      </form>
    </div>
  </div>
</div>

<script>
(function() {
  if (window._aalFormSetup) return;
  window._aalFormSetup = true;

  function setupForm() {
    var form = document.getElementById('aal-contact-form');
    if (!form) { setTimeout(setupForm, 200); return; }
    if (form._bound) return;
    form._bound = true;

    form.addEventListener('submit', function(e) {
      e.preventDefault();
      var status = document.getElementById('aal-form-status');
      var btn = form.querySelector('.aal-form-submit');
      var name = form.querySelector('#aal-name').value.trim();
      var email = form.querySelector('#aal-email').value.trim();
      var org = form.querySelector('#aal-org').value.trim();
      var event = form.querySelector('#aal-event').value.trim();

      if (!name || !email || !event) {
        status.textContent = 'Please fill in all required fields.';
        status.className = 'aal-form-status aal-status-error';
        return;
      }

      btn.disabled = true;
      btn.textContent = 'Sending...';
      status.textContent = '';

      var subject = encodeURIComponent('Speaking inquiry from ' + name + (org ? ' (' + org + ')' : ''));
      var body = encodeURIComponent(
        'Name: ' + name + '\\n' +
        'Email: ' + email + '\\n' +
        'Organization: ' + (org || '—') + '\\n\\n' +
        'Event details:\\n' + event
      );

      window.open('mailto:john@thatrandomagency.com?subject=' + subject + '&body=' + body, '_blank');

      status.textContent = 'Your email client should open shortly. You can also email john@thatrandomagency.com directly.';
      status.className = 'aal-form-status aal-status-ok';
      btn.disabled = false;
      btn.textContent = 'Send inquiry \\u2192';
    });
  }

  setupForm();
  var obs = new MutationObserver(function() { setupForm(); });
  obs.observe(document.body, { childList: true, subtree: true });
})();
</script>
"""
