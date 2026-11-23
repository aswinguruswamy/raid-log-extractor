# How to export a call transcript

RAID Log Extractor reads `.vtt` transcripts, `.docx` minutes and `.txt` notes. Speaker names matter: the tool uses them to see who said "I'll do it" and who was on the call.

## Microsoft Teams

1. Open the meeting in the Teams calendar, or open the meeting chat.
2. Go to **Recap** (or **Recordings & Transcripts**).
3. Select the transcript, then **Download** → **Download as .vtt**.
4. Upload the `.vtt` file. Speaker names come from the voice tags in the file.

Transcription must be on during the meeting. Only the organiser and people allowed by your organisation can download it.

## Zoom

1. Sign in to the Zoom web portal and open **Recordings** → **Cloud recordings**.
2. Open the meeting and find the **Audio transcript** file.
3. Download it (it is a `.vtt` file) and upload it.

Cloud recording with **Create audio transcript** must be on for the meeting.

## Your own notes

Write one line for each turn, with the speaker first: `Aiko Sato: I'll send the notes by Friday.` Add a line `Present: Aiko Sato, Ben Ortiz` when you write minutes.

## Before you upload

Your notes go to the Anthropic API. Do not upload notes you may not share. Enter the meeting date, so that "by Friday" becomes a date.
