"""
Audit Logger.

Every call into the Mandate Engine gets logged here — this is what makes
the system "explainable" rather than just a claim in a README. In the demo,
this is the panel you show updating live next to the chat.
"""

import json
import datetime


class AuditLog:
    def __init__(self):
        self.entries = []

    def log(self, event_type: str, detail: dict):
        entry = {
            "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
            "event": event_type,
            "detail": detail,
        }
        self.entries.append(entry)
        return entry

    def print_trail(self):
        for e in self.entries:
            print(f"{e['timestamp']}  {e['event']}")
            for k, v in e["detail"].items():
                print(f"           {k}: {v}")

    def as_json(self):
        return json.dumps(self.entries, indent=2, ensure_ascii=False)