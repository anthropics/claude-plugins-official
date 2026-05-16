---
name: tuev-lernseite
description: Erstellt strukturierte HTML-Lernseiten für die TÜV KI-Agenten-Prüfungsvorbereitung aus .docx-Transkripten oder .htm/.html-Referenzdokumenten. Aktiviert wenn der Nutzer sagt "verarbeite Transkript", "erstelle Lernseite", "neue Transkripte gefunden", "lernseite", "tuev", "prüfungsvorbereitung", oder wenn .docx/.htm/.html-Dateien ohne zugehörige _lernseite.html vorhanden sind. Liest die Quelldatei (.docx nativ, .htm/.html mit HTML-Text-Extraktion), extrahiert Schlüsselkonzepte, Prüfungsfragen mit Antworten und Merkkästen, und speichert das Ergebnis als [name]_lernseite.html im Verzeichnis Lernseiten/.
version: 1.1.0
---

# TÜV Lernseiten-Generator

Dieser Skill verarbeitet `.docx`-Transkripte und `.htm`/`.html`-Referenzdokumente aus der KI-Agenten-Ausbildung und erstellt daraus strukturierte HTML-Lernseiten zur Prüfungsvorbereitung.

## Arbeitsablauf

### Schritt 1: Unverarbeitete Quelldateien finden

Suche mit `Glob` nach allen `.docx`-, `.htm`- und `.html`-Dateien im aktuellen Arbeitsverzeichnis:
- Pattern: `*.docx`, `*.htm`, `*.html` im CWD
- Für jede gefundene Datei: Prüfe ob `Lernseiten/[basename]_lernseite.html` bereits existiert
- Verarbeite nur Dateien OHNE zugehörige Lernseite
- Ignoriere Dateien die selbst bereits `_lernseite` im Namen enthalten

Wenn alle Quelldateien bereits verarbeitet wurden, melde dies kurz und frage ob eine bestimmte Datei neu verarbeitet werden soll.

### Schritt 2: Quelldatei lesen

**Bei `.docx`-Dateien:** Lese direkt mit dem `Read`-Tool. Claude versteht `.docx`-Dateien nativ.

**Bei `.htm`- oder `.html`-Dateien:** Extrahiere den Textinhalt mit Python (HTML-Tags entfernen):
```python
from html.parser import HTMLParser
import re

class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []
        self.skip = False
        self.skip_tags = {'script', 'style'}
        self.block_tags = {'p', 'div', 'li', 'h1', 'h2', 'h3', 'h4', 'tr', 'br', 'td', 'th'}
    def handle_starttag(self, tag, attrs):
        if tag in self.skip_tags: self.skip = True
        if tag in self.block_tags: self.text.append('\n')
    def handle_endtag(self, tag):
        if tag in self.skip_tags: self.skip = False
    def handle_data(self, data):
        if not self.skip:
            s = data.strip()
            if s: self.text.append(s + ' ')

with open('DATEINAME.htm', 'r', encoding='utf-8') as f:
    content = f.read()
parser = TextExtractor()
parser.feed(content)
text = re.sub(r'[ \t]+', ' ', ''.join(parser.text))
text = re.sub(r'\n{3,}', '\n\n', text)
# text enthält jetzt den lesbaren Inhalt
```
Den so gewonnenen Text als Grundlage für Schritt 3 verwenden.

### Schritt 3: Inhalt analysieren

Analysiere den Transkriptinhalt und extrahiere:

**A) Schlüsselkonzepte & Definitionen**
- Alle Fachbegriffe, Technologien, Methoden und Konzepte die erklärt werden
- Definition/Erklärung je Begriff
- Kontext und praktische Bedeutung

**B) Prüfungsfragen & Musterantworten**
- 5–10 typische Prüfungsfragen die aus dem Transkriptinhalt ableitbar sind
- Vollständige Musterantworten (TÜV-typisch: präzise, keine Floskeln)
- Schwierigkeit: Mix aus Verständnis-, Anwendungs- und Vertiefungsfragen

**C) Zusammenfassung / Merkkästen**
- 4–6 kompakte Merkkästen mit den wichtigsten Kernaussagen
- Jeder Merkkasten: 1–3 Sätze, direkt prüfungsrelevant
- Aufbau: Aussage → Begründung/Beispiel

### Schritt 4: HTML-Lernseite generieren

Erstelle eine vollständige HTML-Datei nach diesem Template:

```html
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>[MODUL-TITEL] — TÜV Lernseite</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; }
    body {
      font-family: 'Segoe UI', Arial, sans-serif;
      font-size: 16px;
      line-height: 1.6;
      color: #1a1a1a;
      max-width: 960px;
      margin: 0 auto;
      padding: 24px 20px 60px;
      background: #f9f9f9;
    }
    header {
      background: #003366;
      color: white;
      padding: 24px 28px;
      border-radius: 8px;
      margin-bottom: 24px;
    }
    header h1 { margin: 0 0 6px; font-size: 1.6rem; }
    header .meta { font-size: 0.85rem; opacity: 0.8; }
    nav {
      background: white;
      border: 1px solid #d0d7de;
      border-radius: 8px;
      padding: 16px 20px;
      margin-bottom: 28px;
    }
    nav strong { color: #003366; display: block; margin-bottom: 8px; }
    nav a {
      display: block;
      color: #0055aa;
      text-decoration: none;
      padding: 3px 0;
      font-size: 0.95rem;
    }
    nav a:hover { text-decoration: underline; }
    section {
      background: white;
      border: 1px solid #d0d7de;
      border-radius: 8px;
      padding: 24px 28px;
      margin-bottom: 24px;
    }
    h2 {
      color: #003366;
      border-bottom: 2px solid #003366;
      padding-bottom: 8px;
      margin-top: 0;
      font-size: 1.25rem;
    }
    h3 { color: #0055aa; margin-top: 20px; font-size: 1.05rem; }
    .konzept {
      border: 1px solid #c8d8e8;
      border-left: 4px solid #0055aa;
      border-radius: 4px;
      padding: 12px 16px;
      margin: 12px 0;
      background: #f5f8fc;
    }
    .konzept .term { font-weight: 700; color: #003366; }
    .konzept .definition { color: #333; margin-top: 4px; }
    .frage-block {
      border: 1px solid #d0d7de;
      border-radius: 6px;
      margin: 14px 0;
      overflow: hidden;
    }
    .frage-block summary {
      background: #f0f4f8;
      padding: 12px 16px;
      cursor: pointer;
      font-weight: 600;
      color: #003366;
      list-style: none;
      display: flex;
      align-items: flex-start;
      gap: 10px;
    }
    .frage-block summary::-webkit-details-marker { display: none; }
    .frage-block summary::before {
      content: "▶";
      font-size: 0.75rem;
      margin-top: 3px;
      flex-shrink: 0;
      transition: transform 0.2s;
    }
    .frage-block[open] summary::before { content: "▼"; }
    .frage-block .antwort {
      padding: 14px 16px;
      background: #fafffe;
      border-top: 1px solid #d0d7de;
      color: #222;
    }
    .merkkasten {
      background: #fffde7;
      border: 1px solid #f9c700;
      border-left: 5px solid #f9c700;
      border-radius: 4px;
      padding: 14px 18px;
      margin: 14px 0;
    }
    .merkkasten .mk-titel {
      font-weight: 700;
      color: #5a4000;
      margin-bottom: 4px;
    }
    .merkkasten .mk-text { color: #333; }
    .badge {
      display: inline-block;
      background: #003366;
      color: white;
      font-size: 0.75rem;
      padding: 2px 8px;
      border-radius: 12px;
      margin-right: 6px;
      vertical-align: middle;
    }
    @media print {
      body { background: white; padding: 10px; }
      nav, .frage-block summary::before { display: none; }
      .frage-block .antwort { display: block !important; border-top: 1px solid #ccc; }
      header { border-radius: 0; }
    }
  </style>
</head>
<body>

<header>
  <h1>[MODUL-TITEL]</h1>
  <div class="meta">
    TÜV KI-Agenten-Ausbildung &nbsp;|&nbsp;
    Erstellt: [DATUM] &nbsp;|&nbsp;
    Quelle: <em>[DATEINAME]</em>
  </div>
</header>

<nav>
  <strong>Inhaltsverzeichnis</strong>
  <a href="#schluesselkonzepte">1. Schlüsselkonzepte &amp; Definitionen</a>
  <a href="#pruefungsfragen">2. Prüfungsfragen &amp; Musterantworten</a>
  <a href="#zusammenfassung">3. Zusammenfassung / Merkkästen</a>
</nav>

<!-- ============================================================ -->
<section id="schluesselkonzepte">
  <h2>1. Schlüsselkonzepte &amp; Definitionen</h2>

  <!-- BEISPIEL — durch tatsächliche Inhalte ersetzen -->
  <div class="konzept">
    <div class="term">Begriff 1</div>
    <div class="definition">Definition und Erklärung …</div>
  </div>

  <div class="konzept">
    <div class="term">Begriff 2</div>
    <div class="definition">Definition und Erklärung …</div>
  </div>
  <!-- weitere .konzept-Blöcke für jeden extrahierten Begriff -->

</section>

<!-- ============================================================ -->
<section id="pruefungsfragen">
  <h2>2. Prüfungsfragen &amp; Musterantworten</h2>
  <p style="color:#555;font-size:0.9rem">Klicke auf eine Frage, um die Musterantwort einzublenden.</p>

  <!-- BEISPIEL — durch tatsächliche Fragen ersetzen -->
  <details class="frage-block">
    <summary>Frage 1: …?</summary>
    <div class="antwort">Musterantwort …</div>
  </details>

  <details class="frage-block">
    <summary>Frage 2: …?</summary>
    <div class="antwort">Musterantwort …</div>
  </details>
  <!-- weitere details.frage-block für jede Frage -->

</section>

<!-- ============================================================ -->
<section id="zusammenfassung">
  <h2>3. Zusammenfassung / Merkkästen</h2>

  <!-- BEISPIEL — durch tatsächliche Merkkästen ersetzen -->
  <div class="merkkasten">
    <div class="mk-titel">Kernaussage 1</div>
    <div class="mk-text">Kompakte Zusammenfassung der Kernaussage …</div>
  </div>

  <div class="merkkasten">
    <div class="mk-titel">Kernaussage 2</div>
    <div class="mk-text">Kompakte Zusammenfassung der Kernaussage …</div>
  </div>
  <!-- weitere .merkkasten-Blöcke -->

</section>

</body>
</html>
```

### Schritt 5: Datei speichern

- Ausgabepfad: `[Arbeitsverzeichnis]/Lernseiten/[Dateiname-ohne-Erweiterung]_lernseite.html`
- Beispiel: `Transkript_23.03.2026.docx` → `Lernseiten/Transkript_23.03.2026_lernseite.html`
- Beispiel: `TÜV Zertifizierungen.htm` → `Lernseiten/TÜV Zertifizierungen_lernseite.html`
- Nutze das `Write`-Tool zum Speichern
- Falls das Verzeichnis `Lernseiten/` nicht existiert, erstelle es vorher mit `mkdir`

### Schritt 6: Abschlussmeldung

Nach der Verarbeitung melde kurz:
- Welche Lernseiten erstellt wurden (Dateinamen)
- Wie viele Konzepte / Fragen / Merkkästen je Seite enthalten sind
- Hinweis: HTML im Browser öffnen oder für Print-Ansicht `Strg+P` nutzen

## Qualitätsrichtlinien

- **Konzepte**: Lieber 8 präzise Begriffe als 20 oberflächliche
- **Prüfungsfragen**: Formulierung wie in echten TÜV-Prüfungen (offen, anwendungsorientiert)
- **Merkkästen**: Keine Floskeln — jeder Kasten muss allein stehend verständlich sein
- **Deutsch**: Alle Lernseiten auf Deutsch, Fachbegriffe auf Englisch nur wenn üblich
- **Vollständigkeit**: Jede Lernseite muss alle 3 Abschnitte enthalten, auch wenn ein Abschnitt kleiner ist
