# Appointments Agent

A Python application to help manage and schedule appointments/meetings.

## Setup

1. Copy `.env.example` to `.env` and fill in your configuration values
2. Install dependencies: `pip install -r requirements.txt`
3. Run the application: `streamlit main.py`

### Google Calendar Credentials (`client_secrets.json`)

Use a Google Service Account JSON (not an OAuth `installed` file):
1. Enable Calendar API in a GCP project.
2. Create a Service Account and JSON key → save as `client_secrets.json` (root, git‑ignored).
3. Share your calendar with the `client_email` (permission: Make changes to events).
4. Optional: set `CALENDAR_ID` (defaults to `primary`).


## Features
- Collect user time needs to help find available spots in the calendar
- Automatically add user info to the desired spot

## Graph

![Appointments Agent Graph](https://github.com/Wonder2210/appointments-agent/blob/main/graph.png)

[Mermaid graph](https://www.mermaidchart.com/play?utm_source=mermaid_live_editor&utm_medium=toggle#pako:eNqVlMFuwyAMQH8FZZdEGl3Xww6k6qmfsNsyIZdAgkRJBLTVNO3fR9IqRavVZjkFx8-An5XvTHS1zFhGKa2s6KzSDassIcp0J9GCC-OKEHFwR8mI0VaCq-yY3jjoW_K-Lc8pw8O5DxHiPP9Y95tptX7pN58FY0xp58M1vYHQSse1VZ3bQ9CdzW9DxTVfgJG2BsfhCNrAThsdvnI0WtzsEm8XQARsN-RTwp9AB76X3kMj83TxNyfC_OBjvVqGeBKfo9GE8nKoJYO2zcQgMWwfsN149KD3MkejRaolNmiSMr5PSgykRiZlhNIN4qd8IIPQxZVD2jqPR-9TzjF65pEe_oNGrZX3pvbMoReawaUjVT5QPY9ID56KvC8krfpYP9LjEbrMVyo6jpjfSkVqqeBgAlHaGPakVmqp1PPwS6Gt1E0b2OtihWDjT2OEaNeDiE1lSyRtGORL6Z3avSlR2eznFyXhqdM)
