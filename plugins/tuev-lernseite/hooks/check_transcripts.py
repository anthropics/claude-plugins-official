#!/usr/bin/env python3
"""
TÜV Lernseite — UserPromptSubmit hook
Prüft ob im aktuellen Arbeitsverzeichnis neue .docx-Transkripte ohne
zugehörige _lernseite.html existieren und fügt ggf. Kontext ein.
"""
import json
import os
import sys
from pathlib import Path


def find_unprocessed(cwd: Path) -> list[str]:
    docx_files = list(cwd.rglob("*.docx"))
    unprocessed = []
    for docx in docx_files:
        lernseite = docx.parent / (docx.stem + "_lernseite.html")
        if not lernseite.exists():
            unprocessed.append(docx.name)
    return unprocessed


def main():
    cwd = Path(os.environ.get("CLAUDE_CWD", os.getcwd()))

    # Nur aktiv wenn das Verzeichnis überhaupt .docx-Dateien enthält
    all_docx = list(cwd.rglob("*.docx"))
    if not all_docx:
        print(json.dumps({}))
        return

    unprocessed = find_unprocessed(cwd)
    if not unprocessed:
        print(json.dumps({}))
        return

    names = ", ".join(unprocessed)
    context = (
        f"SYSTEM: {len(unprocessed)} neue Transkript-Datei(en) ohne Lernseite erkannt: "
        f"{names}. "
        "Bitte verarbeite diese automatisch mit dem tuev-lernseite Skill "
        "und erstelle für jede Datei eine HTML-Lernseite."
    )
    print(json.dumps({"additionalContext": context}))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # Hook-Fehler sollen den Prompt nie blockieren
        print(json.dumps({}), file=sys.stderr)
        sys.exit(0)
