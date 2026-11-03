# Kights games
from datetime import datetime, timedelta
import uuid
events = [
    # (date, time, opponent, note)
    ("2025-10-11","12:00","Titans","Titans (home) vs Knights (away)"),
    ("2025-10-17","18:00","Vikings","Vikings (home) vs Knights (away)"),
    ("2025-10-24","20:00","Titans","Knights (home) vs Titans (away)"),
    ("2025-10-25","12:00","Vikings","Knights (home) vs Vikings (away)"),
    ("2025-11-01","10:00","Titans","Knights (home) vs Titans (away)"),
    ("2025-11-08","12:00","Vikings","Knights (home) vs Vikings (away)"),
    # All-Star games (include both)
    ("2025-11-07","18:00","All-Star","All-Star Game"),
    ("2025-11-07","20:00","All-Star","All-Star Game"),
]

tzid = "America/Chicago"  # using user's likely timezone (UTC-6 from metadata)
ics_lines = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//ChatGPT//WaterPolo Knights Schedule//EN",
    f"X-WR-TIMEZONE:{tzid}"
]

for date_str, time_str, opponent, note in events:
    dtstart = datetime.strptime(date_str + " " + time_str, "%Y-%m-%d %H:%M")
    dtend = dtstart + timedelta(hours=1)
    uid = str(uuid.uuid4())
    summary = "Water Polo – Knights Game"
    if opponent == "All-Star":
        description = "Men's Water Polo All-Star Game"
    else:
        description = f"Men's Water Polo League Game — Knights vs {opponent}"
    ics_lines.extend([
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}",
        f"DTSTART;TZID={tzid}:{dtstart.strftime('%Y%m%dT%H%M%S')}",
        f"DTEND;TZID={tzid}:{dtend.strftime('%Y%m%dT%H%M%S')}",
        f"SUMMARY:{summary}",
        f"LOCATION:Pool",
        f"DESCRIPTION:{description} — {note}",
        "END:VEVENT"
    ])

ics_lines.append("END:VCALENDAR")
ics_content = "\n".join(ics_lines)

path = "waterpolo_knights_schedule.ics"
with open(path, "w") as f:
    f.write(ics_content)

path, ics_content[:400]
