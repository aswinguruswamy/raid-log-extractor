# RAID Log Extractor

Turn the notes from a team call into a RAID log in less than one minute.

> **Status:** Work in progress. Version 1.0 is planned for October 27, 2026. The live demo link and a demo GIF come with the final README.

## What it does

The tool reads the notes from a team call (.txt, .docx, or a Teams/Zoom .vtt transcript). It finds six item types:

| Type | Example |
|---|---|
| Risk | "The vendor may not deliver the API in time." |
| Assumption | "We assume that the test data is ready by Friday." |
| Issue | "The staging server is down." |
| Dependency | "The release needs sign-off from the security team." |
| Action | "Priya will send the migration plan by Monday." |
| Decision | "We will use PostgreSQL for the new service." |

Each item has an owner, a due date, a status, and a **source quote** from the notes. The code checks each quote word for word against the notes. When the notes do not give an owner or a date, the tool writes **"Not stated"**. It does not guess.

## Eval result

10 sample calls, 68 expected items, model `claude-sonnet-5-5`: **100% recall and 100% precision**, 0 invented owners or dates, about $0.01 for each call. The prompt was tuned on these samples, so new notes may score lower. See [`evals/FINDINGS.md`](evals/FINDINGS.md) and [`evals/report.md`](evals/report.md).

## Quick start

You need Python 3.9 or later and an [Anthropic API key](https://console.anthropic.com).

```bash
git clone https://github.com/aswinguruswamy/raid-log-extractor.git
cd raid-log-extractor
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
python3 -m pip install -r requirements.txt
cp .env.example .env    # then put your Anthropic API key in .env
```

**Web page:**

```bash
python3 -m streamlit run app.py
```

The demo mode needs no API key. The "Your own notes" mode uses the key in `.env`.

**Command line:**

```bash
python3 -m raid extract samples/s02_crm_migration.txt
```

The Excel file goes into the `output/` folder.

**Tests:**

```bash
python3 -m pytest          # offline tests, no API key
python3 -m pytest -m live  # live tests with your key (a few cents)
```

## Project structure

```
app.py              Streamlit web page (demo mode and your own notes)
raid/               the tool: parse, extract, export, cost, command line, eval scoring
samples/            10 sample calls with invented names (no real data)
evals/              correct answers, eval script, run outputs, report, findings
demo/               saved results that the demo mode shows
docs/               product decisions
tests/              offline tests and live tests
.streamlit/         web page settings (upload limit, colours)
```

## Privacy

The tool sends the text of your notes to the Anthropic API. It does not store the notes or your key. Do not use notes that your company or client does not permit you to share with a third-party service.

## License

MIT
