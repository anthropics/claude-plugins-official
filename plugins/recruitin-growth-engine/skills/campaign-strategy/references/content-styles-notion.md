# LinkedIn Content Templates (from Notion Content Manager)

Reference implementation from Recruitin's existing `notion_content_manager.py` system. These 4 post styles are proven formats for recruitment industry LinkedIn content.

## Content Style Framework

The Notion Content Manager uses 4 LinkedIn post styles. Each style serves a different purpose in the authority-building cycle.

### Style 1: Contrarian

**Purpose:** Challenge conventional recruitment wisdom. High engagement through debate.
**Best for:** Weeks 4-6 (Authority phase) and Weeks 7-9 (Engagement phase)
**Typical engagement:** 3-5x average due to comment-worthy opinion

```
[BOLD STATEMENT over {topic}]

[Lege regel]

[3-5 regels met concrete data/voorbeelden uit eigen praktijk]

[Lege regel]

[Plot twist of nuance die discussie opent]

[Lege regel]

[Vraag die uitnodigt tot reactie]

#recruitment #technischepersoneel #hiring
```

**Example:**
```
"Bedrijven die alleen op Indeed posten, verbranden 60% van hun recruitment budget."

Klinkt provocatief? Hier zijn onze cijfers uit Q4:

→ Indeed-only campagnes: €680 cost-per-hire, 42% quality score
→ Multi-channel (Indeed + LinkedIn + Meta): €290 cost-per-hire, 71% quality score

Het verschil? Passieve kandidaten bereik je niet op job boards.
Ze scrollen wel door hun Instagram en LinkedIn feed.

Maar — en hier zit de nuance — voor blue collar rollen werkt Indeed nog steeds het beste.
Het hangt af van je doelgroep, niet van het platform.

Waar zetten jullie het meeste budget in? En waarom?

#recruitment #talentacquisition #recruitmentmarketing #arbeidsmarkt
```

### Style 2: Data Story

**Purpose:** Establish authority through specific numbers and analysis.
**Best for:** Weeks 1-3 (Foundation phase)
**Typical engagement:** Saves and shares due to reference value

```
[Specifiek getal] over {topic}

[Lege regel]

Dit is wat dit betekent voor recruitment in Oost-Nederland:

→ [Insight 1 met data]
→ [Insight 2 met voorbeeld]
→ [Insight 3 met actie]

[Lege regel]

[Conclusie + vraag aan lezer]

#recruitment #data #hiring
```

**Example:**
```
127 vacatures voor PLC programmeurs in Gelderland. Vorige maand: 98. Dat is +30% in 4 weken.

Dit is wat dit betekent voor recruitment in Oost-Nederland:

→ De automationssector draait overuren. ASML, VDL en Siemens zoeken allemaal tegelijk.
→ Indeed-data laat zien dat het gemiddeld salaris is gestegen van €4.600 naar €4.850. Bedrijven bieden meer om schaars talent te lokken.
→ Ghosting-risico is HOOG: Yacht en Brunel hebben 40% meer vacatures in dezelfde niche.

De bedrijven die nu niet investeren in employer branding, betalen straks €800+ per hire.
Wie het slim aanpakt met targeted content, zit op €350.

Hoe merken jullie de krapte in technisch recruitment?

#recruitment #arbeidsmarkt #engineering #automation #data
```

### Style 3: How-To

**Purpose:** Provide actionable value. Positions Recruitin as helpful expert.
**Best for:** Weeks 7-9 (Engagement phase) and Weeks 10-12 (Conversion phase)
**Typical engagement:** High saves, good for lead generation

```
[Herkenbaar probleem rond {topic}]

[Lege regel]

Hier is de fix in 4 stappen:

1. [Concrete actie 1]
2. [Concrete actie 2]
3. [Concrete actie 3]
4. [Concrete actie 4]

[Lege regel]

Resultaat: [Specifiek cijfer of uitkomst]

Save deze post voor later.

#recruitment #tips #hiring
```

**Example:**
```
Je Meta-campagne draait al 2 weken maar je krijgt alleen ongeschikte sollicitaties. Herkenbaar?

Hier is de fix in 4 stappen:

1. Check je audience: Exclude huidige werknemers van je opdrachtgever + competitors (custom audience)
2. Test je copy: Draai 3 varianten — benefit-led, pain-point-led en social proof. Kill de verliezer na 48 uur.
3. Fix je funnel: Is je landingspagina mobiel-first? 73% van onze sollicitaties komt via telefoon.
4. Voeg kwalificatievragen toe: Eén simpele vraag ("Heb je 3+ jaar ervaring?") halveert je ongeschikte sollicitaties.

Resultaat bij onze laatste 12 campagnes: quality score van 42% naar 68%. Cost-per-hire daalde met €180.

Save deze post voor later.

#recruitment #metaads #hiring #recruitmentmarketing #tips
```

### Style 4: Behind the Scenes

**Purpose:** Build trust through vulnerability and authenticity.
**Best for:** Weeks 7-9 (Engagement phase)
**Typical engagement:** High comments due to relatability

```
[Eerlijke bekentenis rond {topic}]

[Lege regel]

Dit gebeurde:
[Context in 2-3 zinnen]

[Lege regel]

Wat ik leerde:
[Concrete les met voorbeeld]

[Lege regel]

Nu doe ik dit anders:
[Nieuwe aanpak]

Herken je dit?

#recruitment #learnings #hiring
```

**Example:**
```
Vorige maand heb ik €1.200 aan Meta-budget verspild aan een campagne die niets opleverde. Nul sollicitaties.

Dit gebeurde:
Een opdrachtgever wilde "zo snel mogelijk" een Maintenance Engineer in Overijssel. Ik lanceerde dezelfde campagne-opzet die vorige keer werkte. Zelfde targeting, zelfde copy, zelfde visual.

Wat ik leerde:
De vorige campagne was in september. Nu was het januari. Compleet andere arbeidsmarkt. Q1-budgetten zijn bevroren, kandidaten zijn net begonnen aan goede voornemens bij hun huidige werkgever. Dezelfde boodschap landde niet.

Nu doe ik dit anders:
Elke campagne begint met een data-check. Wat zijn de actuele vacature-volumes? Wat is de ghosting-risk? Welke concurrenten zijn actief? Pas daarna kies ik de strategie.

Herken je dit? Wanneer heeft een "beproefde aanpak" jullie in de steek gelaten?

#recruitment #eerlijk #learnings #recruitmentmarketing
```

## Style Selection Logic for the Growth Engine

When generating content, select the style based on:

| 12-Week Phase | Primary Style | Secondary Style |
|--------------|---------------|-----------------|
| Weeks 1-3 (Foundation) | data_story | contrarian |
| Weeks 4-6 (Authority) | contrarian | data_story |
| Weeks 7-9 (Engagement) | how_to, behind_scenes | contrarian |
| Weeks 10-12 (Conversion) | how_to | data_story |

## Notion Integration

The existing system uses Notion as content management:

| Database | Notion ID | Purpose |
|----------|-----------|---------|
| Recruitment News | `2e52252c-bb15-8101-b097-cce88691c0d0` | News article aggregation |
| Content Drafts & Publishing | `2e52252c-bb15-81e9-8215-cee7c7812f6d` | Draft management |
| LinkedIn & Recruitment Intelligence Hub | `27c2252c-bb15-815b-b21b-e75a8c70d8d7` | Master content hub |

**Draft Properties:**
- Name (title)
- Style (select: contrarian / data_story / how_to / behind_scenes)
- Status (select: Draft / Ready to Send / Published / Archived)
- URL (optional source reference)
- Created (date)

**LinkedIn Character Limit:** Max 1,300 characters per post.
