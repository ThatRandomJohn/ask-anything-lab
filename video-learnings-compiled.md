# Compiled Learnings from Nick Saraev Videos

*All 4 videos are by Nick Saraev (370K subscribers) - an automation/AI entrepreneur who built a 7-figure content company (1SecondCopy) using Make.com and now teaches AI-powered business automation.*

---

## Video 1: "Anthropic Just Dropped The n8n Killer (Managed Agents)"
**Length:** 16:30 | **Published:** April 8, 2026

### What Are Claude Managed Agents?
- Anthropic's take on **automating the process of automating processes**
- Hosted directly on Anthropic's backend infrastructure -- they spin up a server and give you a reusable, standardized container with limited networking (for safety)
- Available at `platform.claude.com/workspaces/default`
- Part of the Anthropic API service (same playground as API integrations)

### Key Features Demonstrated
1. **Natural Language Agent Creation**: You describe what you want in plain English (even via voice transcript), and it builds the agent spec for you
2. **Built-in OAuth**: No need to manually manage API keys. For example, ClickUp integration uses OAuth flow -- click connect, authorize, done. Huge barrier-to-entry reduction for non-technical users
3. **Credential Vaults**: Secure storage for credentials shared across organizations
4. **Testing Interface**: Two panels -- "Transcript" (conversation view) and "Debug" (code/API view)
5. **Full API Event Logging**: Every raw API event visible -- model start, end, thinking sections, tool calls. Full interpretability and accountability
6. **Parallel Task Execution**: The agent created 5 ClickUp tasks simultaneously
7. **Self-Improving Flow**: After testing, the system suggests improvements (e.g., "add a default ClickUp list" or "add assignee mapping")
8. **Integration Guidance**: Built-in step-by-step guide for connecting to other platforms
9. **"Ask Claude" Button**: In sessions, you can ask Claude to help you build a frontend or write integration code

### Dashboard Walkthrough
- **Agents Tab**: List all agents, archive/manage them
- **Agent View**: High-level config including MCPs, tools, platforms, additional skills
- **Session View**: Independent conversation runs with the agent
- **Debug View**: Filter by request type (agent messages, thinking sections, etc.)
- **Visual Timeline**: Shows which parts of conversation are dedicated to which task type
- **Environments**: Scoped to organization, shows permissions, MCP access, networking limits
- **Analytics**: Token usage (in/out), rate-limited requests, caching stats, cost tracking (month-to-date)
- **Access Logs**: Deep dive into every single API request

### Architecture Notes
- Currently locked to **Sonnet 4.6** (at time of recording)
- More limited than running Claude Code locally (no fast mode, etc.)
- Environment types are "highly limited" -- can only chat internally + approved MCP connections
- Security model designed for **mid-market and enterprise** use cases
- When you archive an agent, you must separately archive/delete the environment

### Best Practice
- Create agents via Quick Start or Agents tab (not Environments tab) -- this automatically creates the environment and credential vault together
- Otherwise you end up with orphaned environments

### Nick's Prediction
- Anthropic will soon build a **visual workflow builder** to accompany the text-based system
- The main advantage of n8n/Make.com/Zapier right now is visual "node connects to node" representation
- Once Anthropic cracks that visual layer, it becomes a **full replacement for no-code automation infrastructure**
- Service providers and companies with technical ability will use managed infrastructure for all knowledge process automation

### Cost
- Nick spent $2.40 on testing, ~$24/month for client work
- Most usage was Sonnet 4.6, some Opus 4.6

---

## Video 2: "Claude Channels Just Dropped, And It Kills OpenClaw (Again)"
**Length:** ~21 min | **Published:** April 2026

### What Are Claude Channels?
- **Telegram and Discord integration** for Claude Code that lets you text your agents the same way you text humans
- Your agent runs locally on your computer; you interact with it via messaging apps from anywhere (including mobile)
- All your local Claude Code skills remain accessible

### Demo Use Cases Shown
1. **Thumbnail Design on the Go**: Sent a URL to Telegram, asked agent to replace person in thumbnail, change text, colors, logos. Agent upscaled and sent multiple variants back to phone
2. **Lead Scraping**: Via Discord, asked to "scrape me 100 leads from Apify -- Dentist in California" -- agent ran the Apify scraping skill, compiled 98 leads with phone numbers, sent CSV back to phone
3. **General Conversation**: Agent maintains conversation history locally with descriptions of what occurred

### How It Works Under the Hood
- Plugin-based: `@claude-plugins-official` for both Telegram and Discord
- Every approved channel plugin has a **sender allow list** -- only specific IDs you've pre-added can push messages; everything else is silently dropped
- Same security level as regular Claude Code
- Local conversation history updated with reasoning/thinking layer alongside the message log

### Setup: Telegram
1. Message `@BotFather` on Telegram, create new bot (name must end with "bot")
2. Copy the bot token
3. In Claude Code terminal: `/plugin install telegram @claude-plugins-official`
4. Choose scope (user = all workspaces)
5. `/reload-plugins` to activate
6. `/telegram:configure` -- paste bot token
7. Exit Claude Code, relaunch with: `claude --channels plugin:telegram@claude-plugins-official`
8. Send a message to your bot on Telegram to verify

### Setup: Discord
1. Go to `discord.com/developer/applications`, create new app
2. Under Bot settings: enable "Message Content Intent"
3. Reset token, copy it
4. Under OAuth2: add permissions -- Bot, then: View Channels, Send Messages, Send Messages in Threads, Read Message History, Attach Files, Add Reactions
5. Use generated URL to invite bot to your Discord server
6. In Claude Code: `/plugin install discord @claude-plugins-official`
7. `/discord:configure` -- paste token
8. Launch: `claude --channels plugin:discord@claude-plugins-official`
9. DM the bot on Discord to verify

### Keeping It Running 24/7
**Mac:**
- Terminal: `caffeinate -t [seconds]` (e.g., 3600 for 1 hour)
- Settings > Lock Screen: Set "turn display off" to Never
- Settings > Battery > Options: "Prevent automatic sleeping on power adapter when display is off" = ON
- "Wake for network access" = Always

**Scaling Setup:**
- Use a **Mac Mini** or headless server dedicated to running Claude Code
- Use **Syncthing** to sync your business/workspace folder between your main computer and the server
- Two-way sync means files created via Telegram/Discord on the server appear on your main machine and vice versa
- Only downside: potential git conflicts if committing on both machines simultaneously

### OpenClaw/Claudebot Analysis
Nick argues OpenClaw (formerly Claudebot, formerly Moldbot) blew up due to:
1. **Astroturfing**: A crypto rug-pull pumped artificial interest via fake accounts/GitHub stars
2. **Creator amplification**: YouTube creators saw clicks on the topic and kept making videos
3. **VPS hosting sponsorships**: Companies paid creators $5-10K to make videos about hosting these bots

His core argument:
- OpenClaw is essentially "a Telegram wrapper with cron (heartbeat features) and memory"
- Claude Channels provides the same functionality with **better security** (sender allow lists, no prompt injection risks from random users)
- **More scalable** -- maintained by Anthropic, not random developers
- Combined with Claude Dispatch (for co-work), covers the vast majority of OpenClaw use cases

---

## Video 3: "Cold Email Copywriting & Outreach Full Course 2026"
**Length:** ~4 hours | **Published:** 2026

*Nick's comprehensive course on outbound sales copywriting. He's generated $15M+ in outbound sales over a decade, running a $4M/year profit business.*

### The 7 Psychology Principles Behind Cold Outreach
(Based on Robert Cialdini's "Influence" + Nick's behavioral neuroscience background)

#### 1. Give First
- Provide genuine value before asking for anything
- Examples: "I noticed your landing page is misconfigured -- you're losing $10-20K/month. Here's how to fix it."
- Creates obligation that lowers resistance, disarms skepticism, opens door to trust
- Same principle as Costco samples or restaurant breath mints with the bill

#### 2. Micro Commitments
- Never ask for the big thing first; build momentum through small yeses
- Sequence: Watch 1-min video > longer video > phone call > video call > close
- Research shows: the more times you get someone to say "yes" before the ask, the higher conversion
- Each small agreement makes the next slightly larger one feel natural

#### 3. Social Proof
- Show others taking the same action you're requesting
- **Use specific numbers**: "We generated $112,482 last week for an XYZ business"
- **Match the reference group**: If selling to B2B SaaS, cite B2B SaaS case studies (not freelance dog walkers)
- The more Venn diagram overlap between your reference and your prospect, the more powerful

#### 4. Authority
- Demonstrate hyper-relevant expertise through credentials, accomplishments, confidence
- Match credibility to ICP -- "Google Partner" works better for blue-collar businesses than "behavioral neuroscience degree"
- Signal confidence in writing: "I can absolutely 100% help you" not "I believe maybe I could help"
- Many easy partnership/credential programs exist even for beginners

#### 5. Rapport
- Find shared context (ethnic, cultural, career, even pets)
- **Explicit rapport**: Mentioning shared interests/backgrounds
- **Implicit rapport**: Mirror communication style, message length, punctuation, tone
- Example: Lowercase messages for SF VCs in 2022 signaled in-group membership

#### 6. Scarcity
- Limit availability or create time pressure with deadlines
- **Make constraints real**: Your own capacity, schedule, existing client load
- "This proposal expires end of week" -- but only if genuinely true
- Admitting limitations that show fault (e.g., limited bandwidth) actually builds trust

#### 7. Shared Identity
- Establish common ground: industry, values, challenges, geography
- Mirror tone, message length, use in-group language
- Highlight shared struggles (entrepreneurship hardships, etc.)

### The 3 Components of a Successful Campaign

#### 1. Establish Clear Goals + KPIs
- Define exactly what you're optimizing: short-term revenue (close deals) vs. long-term (awareness/funnel)
- Assign specific key performance indicators to track

#### 2. Build a Frame
- The frame of interaction should NOT always be corporate/highbrow
- Adapt to niche, geography, cultural norms, language
- Many successful campaigns use casual, non-corporate framing

#### 3. Iterate Relentlessly
- **You will almost never one-shot a killer campaign**
- Start at 3.5% reply rate > iterate > 4.5% > 5% > 8% > 10%
- Run multiple variants, kill lowest performers, build new variants from the winner
- It's a data science game: write > test > measure > evolve

### Nick's Copywriting Framework (Generated $15M+)
A cold email/DM has these components:
1. **Personalized icebreaker** (1-2 lines connecting to them specifically)
2. **Social proof** (who am I, why should you care)
3. **The offer** (what you're proposing)
4. **CTA** (specific, low-friction next step)

#### Offer Construction
- Must sound good but NOT too good to be true
- Include **risk mitigation**: "If I don't generate 20 meetings in 60 days, you don't pay a cent"
- Make it **easy to start**: "How does 3:30 PM today sound? I can give you a ring or send a one-click Google Meet invite"
- Specify **time commitment**: "I'll just need 15 minutes of your time over a brief call"

### Platform-Specific Optimization

#### Email
- Subject lines are critical -- keep short, curiosity-driven
- Follow-up sequences (3-5 emails spaced over days)
- Test variants across data set, iterate based on results

#### LinkedIn
- Connection request limits: 100-200/week (higher on premium)
- Must connect before sending full DMs
- Match tone to professional context but keep casual

#### iMessage
- Blue bubble (iPhone-to-iPhone) signals trust
- People more likely to respond to messages that look like personal texts
- Keep messages very short and conversational

### AI in Copywriting -- Nick's Controversial Take
**"I rarely if at all use AI in my copywriting these days."**

Key points:
- AI can write copy at ~2 weeks of human experience level, but struggles with the 75th-95th percentile quality that actually converts
- The skill floor in today's market is ABOVE what AI can produce -- if you're not better than AI, nobody opens your emails
- Across 10,000+ Maker School members, **people who use AI intensely for copy tend to perform worse**

#### When/How to Use AI (The Right Way)
1. **Small templated variables only** -- NOT full email rewrites
2. **Casualization layer**: Convert "Leftclick Incorporated" to "Leftclick" or "The Pacific Creative Group LLC" to "PCG"
   - People in companies use abbreviations/casual names; formal names scream "scraped"
3. **Neighborhood/geography casualization**: Convert "Vancouver, British Columbia" to "East Van"
   - Signals insider knowledge, dramatically increases open rates
4. **Lead scraping and enrichment**: Use AI to gather/enrich prospect data
5. **Personalization snippets**: "Love your [channel/LinkedIn posts]" -- have AI determine their most prominent web property

### Advanced Gray Hat Techniques (Use at Your Own Risk)
1. **Buying pre-warmed accounts**: LinkedIn, Instagram, email mailboxes from vendors; accounts with organic history get higher limits and lower ban rates
2. **Power dialers**: Parallelize outbound calls to eliminate dial/connect time; 2.5x efficiency improvement. Watch for regulations on automatic voicemail drops
3. **Cold SMS/WhatsApp/iMessage emulation**: Platforms that emulate iPhone-to-iPhone sending (blue bubbles); extremely regulated

---

## Video 4: "Claude Computer Use Just Dropped, Here's How to Hack It"
**Length:** ~15 min | **Published:** March 24, 2026 | **Views:** 59,959

### What Is Claude Computer Use?
- Claude's ability to control your computer screen, mouse, and keyboard
- Nick demonstrates "real ways to utilize Claude Computer Use for making money"
- Some approaches bypass the browser feature (acknowledged as "black hat-y")

### Use Cases Covered (from Chapter Timestamps)

#### 1. Automating Social Media Connection Requests (1:41)
- Using a controlled browser to automate LinkedIn connection requests
- Bypass normal manual limits on outreach

#### 2. LinkedIn Outreach with Min Browser (3:13)
- Using Min (a minimal browser) for LinkedIn automation
- Keeps activity looking more natural than headless browsers

#### 3. Data Scraping from LinkedIn (4:42)
- Using Claude's computer control to scrape prospect data from LinkedIn profiles
- More resilient than traditional scraping tools because it mimics human interaction

#### 4. Automating Form Submission (6:06)
- Computer control for filling out forms at scale
- Useful for applications, lead capture, data entry

#### 5. Automating Ad Management (7:37)
- Can significantly increase revenue for businesses by automating ad campaign management
- Handles routine optimization tasks

#### 6. YouTube & Invoice Management (9:06)
- Automating YouTube channel management tasks
- Invoice processing and management automation

#### 7. Desktop App QA Testing (10:33-11:58)
- Using Claude's computer features for automated QA testing of desktop applications
- Can test app features systematically

### How to Enable
- Enable Claude's computer features through settings for productivity and income generation
- Runs through the Claude desktop app

---

## Cross-Video Themes & Key Takeaways

### 1. Anthropic Is Building a Full-Stack Automation Platform
- **Managed Agents** = hosted backend (replaces n8n/Make.com)
- **Channels** = messaging interface (replaces OpenClaw/Claudebot)
- **Computer Use** = desktop/browser automation
- **Claude Code** = the coding/development layer
- Together, these cover the entire automation stack from infrastructure to interface

### 2. Security Is a First-Class Citizen
- Managed Agents: limited networking, scoped environments, credential vaults
- Channels: sender allow lists, silent message dropping
- Nick repeatedly emphasizes choosing Anthropic's maintained solutions over community tools for security

### 3. The "n8n/Make.com Killer" Thesis
- Current limitation: no visual workflow builder (text-only)
- Once Anthropic adds visual node-based views, traditional no-code platforms face existential threat
- Managed Agents already handle credentials, hosting, testing, and integration -- all without writing a line of code

### 4. Practical Money-Making With AI
- Don't use AI to replace human skills wholesale -- use it to augment specific steps
- The "casualization layer" concept: AI makes data feel human (company names, neighborhoods, etc.)
- Computer Use opens entirely new categories of automation (desktop apps, visual workflows, form filling)
- The real value is in combining multiple tools into workflows that run 24/7

### 5. Build Once, Access Anywhere
- Run agents on a dedicated machine (Mac Mini)
- Access via Telegram/Discord from your phone
- Use Syncthing for file sync between machines
- All Claude Code skills available remotely through messaging
