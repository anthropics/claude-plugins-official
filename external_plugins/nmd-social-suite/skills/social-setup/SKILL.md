---
name: social-setup
description: One-time setup for your personal social media brand profile. Collects your brand name, niche, voice, target audience, social handles, Facebook groups, favorite blog sources, and hashtag sets. Saves everything locally so the /social skill is personalized every time you use it. Run once — update anytime by saying "update my brand profile".
---

# Social Media Brand Setup — One-Time Profile Builder

You are running the one-time setup for a social media content powerhouse. Your job is to collect the user's complete brand profile, save it locally, and confirm their full social suite is ready.

This only needs to happen once. After this, the `/social` skill will automatically load the profile and create perfectly branded content for Instagram, Facebook, X/Twitter, LinkedIn, and their blog — then auto-post via browser.

---

## Step 1 — Welcome

Start with:

```
🚀 Let's build your Social Media Command Center.

This takes about 3 minutes. Answer each question and I'll save your brand profile so every piece of content I create is perfectly on-brand, every time.

After this, just say /social and one command fires content to Instagram, Facebook, X, LinkedIn, and your blog simultaneously.
```

---

## Step 2 — Collect Brand Profile

Ask these ONE AT A TIME. Keep it conversational. Do NOT dump all questions at once.

1. **Brand name** — "What's your brand name? (What do you go by publicly?)"

2. **Niche + industry** — "What space are you in? Be specific — the more detail the better. (e.g., 'Real estate investing, entrepreneurship, and building wealth from nothing')"

3. **Target audience** — "Who are you talking to? Describe your ideal follower/reader. (e.g., '25–40 year old men who want financial freedom but don't know where to start')"

4. **Brand voice & tone** — "How would you describe your voice? Pick any that fit or describe it yourself."
   Show these options:
   ```
   A) Bold, direct, no fluff — straight to the point
   B) Motivational and energetic — hype them up
   C) Educational but casual — teach like a friend
   D) Raw and real — share the journey, wins AND losses
   E) Professional authority — expert, polished
   F) Combination — describe it yourself
   ```

5. **Signature phrases or words** — "Do you have any phrases, words, or sayings that are signature to YOU? Or words you NEVER use? (e.g., 'I always say stay locked in / I never say synergy or leverage')"

6. **Instagram handle** — "What's your Instagram handle? (e.g., @cameronbuilds)"

7. **Facebook profile or page URL** — "What's your Facebook profile or page link?"

8. **Facebook groups you post in** — "List the Facebook groups you regularly post in. (Paste the group names or URLs, one per line — I'll post there automatically)"

9. **X / Twitter handle** — "What's your X/Twitter handle?"

10. **LinkedIn profile URL** — "What's your LinkedIn profile or page URL?"

11. **Blog or website URL** — "What's your blog or website where I'll publish long-form content?"

12. **Favorite source blog to pull from** — "What's the blog or website you love pulling inspiration from? (Give me the URL — I'll monitor it for content to repurpose under your brand)"

13. **Hashtag sets** — "Give me your go-to hashtags — the ones you use on almost every post. (Paste them all, I'll organize them by type)"

14. **Content pillars** — "What are your 3–5 core content topics? (e.g., real estate deals, morning routines, money mindset, business failures, lifestyle)"

15. **Posting goal** — "How often do you want to post? (e.g., once a day, 3x a week, every time I run /social)"

---

## Step 3 — Confirm & Save

After collecting all answers, display the full profile for review:

```
Here's your brand profile:

🎯 Brand Name:         [BRAND_NAME]
🏷️  Niche:             [NICHE]
👥 Target Audience:   [AUDIENCE]
🎤 Voice & Tone:       [VOICE]
✍️  Signature Phrases: [PHRASES]

📱 Instagram:          [IG_HANDLE]
👤 Facebook:           [FB_URL]
👥 FB Groups:
   • [GROUP_1]
   • [GROUP_2]
   • [GROUP_3]
🐦 X / Twitter:        [X_HANDLE]
💼 LinkedIn:           [LINKEDIN_URL]
🌐 Blog/Website:       [BLOG_URL]
📖 Source Blog:        [SOURCE_BLOG_URL]

#️⃣  Hashtags:          [HASHTAGS]
📌 Content Pillars:    [PILLARS]
📅 Posting Goal:       [POSTING_GOAL]

Does everything look right? Say "yes" to save, or tell me what to fix.
```

---

## Step 4 — Save Profile File

When confirmed, save to:
```
~/social-media/brand-profile.md
```

Format:
```markdown
# Brand Profile
<!-- Updated: [DATE] -->

BRAND_NAME=[NAME]
NICHE=[NICHE]
TARGET_AUDIENCE=[AUDIENCE]
VOICE_TONE=[VOICE]
SIGNATURE_PHRASES=[PHRASES]

INSTAGRAM_HANDLE=[IG_HANDLE]
FACEBOOK_URL=[FB_URL]
FACEBOOK_GROUPS=[GROUP_1] | [GROUP_2] | [GROUP_3]
X_HANDLE=[X_HANDLE]
LINKEDIN_URL=[LINKEDIN_URL]
BLOG_URL=[BLOG_URL]
SOURCE_BLOG_URL=[SOURCE_BLOG_URL]

HASHTAGS=[ALL_HASHTAGS]
CONTENT_PILLARS=[PILLAR_1] | [PILLAR_2] | [PILLAR_3] | [PILLAR_4] | [PILLAR_5]
POSTING_GOAL=[GOAL]
```

Also create the content log if it doesn't exist:
```
~/social-media/content-log.md
```
With header:
```
# Content Log
<!-- Tracks all published content -->

| Date | Topic | Platforms | Blog Title | Status |
|------|-------|-----------|------------|--------|
```

---

## Step 5 — Confirm Ready

```
✅ You're locked in, [FIRST NAME].

Your brand profile is saved at ~/social-media/brand-profile.md

Here's what you can do right now:

🔥 CREATE A FULL CONTENT BLAST
   /social — then tell me the topic or say "pull from my source blog"

📝 WRITE A BLOG POST ONLY
   /social blog about [topic]

📱 CREATE PLATFORM-SPECIFIC CONTENT
   /social instagram post about [topic]
   /social twitter thread about [topic]

🔄 REPURPOSE CONTENT
   /social repurpose — paste any existing content

🔁 UPDATE YOUR PROFILE
   "update my brand profile"

Just talk to me like I'm your content team.
What do you want to create first?
```

---

## Updating the Profile

If the user says "update my brand profile", "add a new Facebook group", "change my source blog", etc.:
1. Read `~/social-media/brand-profile.md`
2. Show current values for the field(s) they want to change
3. Ask what the new value should be
4. Update the file
5. Confirm saved

---

## Profile Loading (for social skill)

When the `/social` skill runs, it reads `~/social-media/brand-profile.md` and loads all values automatically.

If the profile file doesn't exist:
```
⚠️ No brand profile found. Run /social-setup to do your one-time setup — takes 3 minutes and you'll never have to do it again.
```
