#!/usr/bin/env python3.12
"""
work_day.py — work-day helper for Bes morning briefing.

Usage:
  python3.12 work_day.py is_work_day [YYYY-MM-DD]
      → prints "true" or "false"

  python3.12 work_day.py prev_work_day [YYYY-MM-DD]
      → prints the most recent work day before the given date (YYYY-MM-DD)

  python3.12 work_day.py work_days_since YYYY-MM-DD [ref_date]
      → prints all work days from YYYY-MM-DD up to (but not including) ref_date,
        one per line, in order. ref_date defaults to today.

  python3.12 work_day.py last_work_day_before_today
      → prints yesterday's date if it was a work day, otherwise walks back
        until it finds one.

  python3.12 work_day.py logs_to_summarize [YYYY-MM-DD]
      → Given today (or passed date as "today"), returns the list of dates
        whose work logs should be summarized in the morning briefing.
        Logic: all work days from (and including) the prev_work_day before
        today, back to (and including) the work day after the last work day
        that came before that — i.e., all work days since the previous
        work day gap. In practice:
          Monday → [Friday]  (or further back if Fri was also off)
          Tuesday–Friday → [yesterday]
          After a holiday → [last_work_day, day_before_if_also_workday, ...]

Days off: ~/.hermes/days-off.txt (one YYYY-MM-DD per line, # comments ok)
US federal holidays: auto-detected via `holidays` package (all states/federal).
"""

import sys
from datetime import date, timedelta
import holidays

DAYS_OFF_FILE = "/home/justin.guest/.hermes/days-off.txt"


def load_personal_days_off():
    days = set()
    try:
        with open(DAYS_OFF_FILE) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                try:
                    days.add(date.fromisoformat(line))
                except ValueError:
                    pass
    except FileNotFoundError:
        pass
    return days


def is_work_day(d: date, personal_off: set = None, us_holidays: dict = None) -> bool:
    if personal_off is None:
        personal_off = load_personal_days_off()
    if us_holidays is None:
        us_holidays = holidays.US(years=d.year)
    if d.weekday() >= 5:  # Saturday=5, Sunday=6
        return False
    if d in personal_off:
        return False
    if d in us_holidays:
        return False
    return True


def prev_work_day(ref: date) -> date:
    personal_off = load_personal_days_off()
    us_hols = {}
    d = ref - timedelta(days=1)
    while True:
        if d.year not in us_hols:
            us_hols.update(holidays.US(years=d.year))
        if is_work_day(d, personal_off, us_hols):
            return d
        d -= timedelta(days=1)


def work_days_since(start: date, ref: date) -> list:
    """All work days in [start, ref). ref not included."""
    personal_off = load_personal_days_off()
    us_hols = {}
    result = []
    d = start
    while d < ref:
        if d.year not in us_hols:
            us_hols.update(holidays.US(years=d.year))
        if is_work_day(d, personal_off, us_hols):
            result.append(d)
        d += timedelta(days=1)
    return result


def logs_to_summarize(today: date) -> list:
    """
    Returns the list of dates whose work logs should be shown in the morning
    briefing. Always at least one date (the most recent work day before today).
    If there was a gap (weekend/holiday) before today, includes all work days
    from just after the previous-previous work day up to today.
    """
    # Most recent work day before today
    most_recent = prev_work_day(today)
    # Work day before that
    one_before = prev_work_day(most_recent)
    # If most_recent is consecutive with yesterday (no gap), just return it
    yesterday = today - timedelta(days=1)
    if most_recent == yesterday:
        # No gap — just yesterday
        return [most_recent]
    else:
        # Gap: return all work days from one_before+1 up to today
        # (i.e., from the day after the previous "regular" work day)
        return work_days_since(one_before + timedelta(days=1), today)


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)

    cmd = args[0]

    if cmd == "is_work_day":
        d = date.fromisoformat(args[1]) if len(args) > 1 else date.today()
        print("true" if is_work_day(d) else "false")

    elif cmd == "prev_work_day":
        d = date.fromisoformat(args[1]) if len(args) > 1 else date.today()
        print(prev_work_day(d).isoformat())

    elif cmd == "work_days_since":
        start = date.fromisoformat(args[1])
        ref = date.fromisoformat(args[2]) if len(args) > 2 else date.today()
        for d in work_days_since(start, ref):
            print(d.isoformat())

    elif cmd == "last_work_day_before_today":
        print(prev_work_day(date.today()).isoformat())

    elif cmd == "logs_to_summarize":
        today = date.fromisoformat(args[1]) if len(args) > 1 else date.today()
        for d in logs_to_summarize(today):
            print(d.isoformat())

    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)
