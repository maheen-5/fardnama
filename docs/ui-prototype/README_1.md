# FardNama - Frontend Prototype

AI-powered cyberbullying evidence collection and reporting platform (FYP project).
This package contains the **frontend-only prototype**: a clickable, static UI mockup
of the full evidence pipeline. It is not wired to any backend, AI model, or database —
all data shown (evidence, classifications, severity scores, etc.) is illustrative.

## How to open it
Just double-click `index.html` (or open it in any modern browser - Chrome, Edge, Firefox).
No installation, server, or internet connection required, except that the two fonts
(Source Serif 4 / Inter / Noto Nastaliq Urdu / Noto Sans Arabic) load from Google Fonts,
so an internet connection is needed for the fonts to render correctly. Without it, the
page still works, just with fallback fonts.

## What's included
- **Notice / consent screen** - PECA 2016 alignment, privacy, no-auto-submit, and
  deletion-rights disclosures, gated behind an explicit checkbox.
- **Login screen** : case-number or username login (mocked, no real auth).
- **9-step evidence pipeline**, merging the original "Severity assessment" and
  "LLM forensics council" stages into one combined **Assessment** step:
  1. Add evidence
  2. Read & organize (processing)
  3. Understand what happened (classification)
  4. Assessment (severity + legal/forensic grounding)
  5. Timeline
  6. Evidence vault
  7. Build report
  8. Get support (reporting assistant)
  9. Safety tools (SOS / panic button)
- **SOS safety feature** : a floating button, double-click to simulate sharing your
  location with trusted contacts and surfacing nearby safe places (police station,
  FIA cybercrime office, hospital, busy public space). This is a UI simulation only:
  browsers cannot hook into a device's real hardware power button or send live SMS —
  a native mobile app would be required for that.
- **Full English / Urdu bilingual support**, including right-to-left layout, toggled
  from the language switch on any screen.

## Design notes
- Color palette: warm beige + sage green + olive, chosen deliberately to feel calm
  and safe rather than the more common neon/red "cyber-threat" aesthetic - appropriate
  given the sensitive subject matter of the tool.
- Mobile responsive (sidebar collapses to a horizontal step strip under ~780px width).
- Single self-contained HTML file - all CSS and JS are inline, no build step needed.

## For the team / supervisor
This is a **visual and interaction prototype** to validate the flow and tone of the
product before backend/AI integration work begins. Happy to iterate on wording,
Urdu translations, color, or step ordering based on feedback.
