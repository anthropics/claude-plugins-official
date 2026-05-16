# TÜV Lernseiten-Generator

Erstellt strukturierte HTML-Lernseiten zur Vorbereitung auf die TÜV KI-Agenten-Zertifizierungsprüfungen (AI Trainer, AI Consultant, AI Agent Builder).

## Was dieser Plugin macht

Claude verarbeitet Quelldateien aus der KI-Agenten-Ausbildung und generiert daraus vollständige HTML-Lernseiten mit drei Abschnitten:

- **Schlüsselkonzepte & Definitionen** — Alle prüfungsrelevanten Fachbegriffe mit Erklärung und Kontext
- **Prüfungsfragen & Musterantworten** — 5–10 aufklappbare Fragen im TÜV-Stil
- **Merkkästen** — 4–6 kompakte Zusammenfassungen der wichtigsten Kernaussagen

## Unterstützte Eingabeformate

- **`.docx`** — Transkripte aus Live-Sessions und OnDemand-Einheiten (nativ lesbar)
- **`.htm` / `.html`** — Referenz- und Informationsdokumente (HTML-Textextraktion per Parser)

## Verwendung

```
"erstelle Lernseite"
"verarbeite Transkript"
"TÜV Prüfungsvorbereitung"
"neue Transkripte verarbeiten"
```

Der Hook erkennt automatisch neue `.docx`-Dateien ohne zugehörige Lernseite und schlägt die Verarbeitung vor.

Ausgabe: `Lernseiten/[Dateiname]_lernseite.html`

## Enthaltene Komponenten

- **Skill** `tuev-lernseite` — Hauptlogik zur Lernseiten-Generierung
- **Hook** `UserPromptSubmit` — Automatische Erkennung neuer Transkriptdateien

## Autor

Entwickelt für die TÜV Rheinland KI-Agenten-Zertifizierungsvorbereitung am AI Training Institute.
