# RAID Log Extractor

Turn the notes from a team call into a RAID log in less than one minute.

> **Status:** Work in progress. Version 1.0 is planned for October 27, 2026.

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

Each item has an owner, a due date, a status, and a **source quote** from the notes. When the notes do not give an owner or a date, the tool writes **"Not stated"**. It does not guess.

## Quick start

```bash
git clone https://github.com/<your-user>/raid-log-extractor.git
cd raid-log-extractor
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env    # then put your Anthropic API key in .env
python -m raid extract samples/<file>.txt
```

The Excel file goes into the `output/` folder.

## Project structure

```
raid/          the tool (parse, extract, export, command line)
samples/       call notes with no real data
evals/         correct answers and the eval script
docs/          product decisions
app.py         Streamlit web page
```

## Privacy

The tool sends the text of your notes to the Anthropic API. Do not use notes that your company or client does not permit you to share with a third-party service.

## License

MIT
