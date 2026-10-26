# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Implementation summary

The logic layer lives in `pawpal_system.py` and is built from four classes (plus a small `ScheduledTask` record). See `uml_diagram.md` for the class diagram.

- **Task**: one care activity with a title, duration, priority (high/medium/low), optional preferred time (`"HH:MM"`), frequency (once/daily/weekly), and completion status. It validates its own fields.
- **Pet**: a name, species, age, and a list of tasks. Adding a task tags it with the pet's name.
- **Owner**: holds the daily minutes available and a list of pets. `get_all_tasks()` returns every pet's tasks together.
- **Scheduler**: the "brain". `generate_plan()` reads tasks only through `Owner.get_all_tasks()`, so one plan covers all pets. It skips completed tasks, takes the rest by priority while they fit in the owner's available minutes, and lays them out in time order (untimed tasks start at 08:00). Each plan entry is a `ScheduledTask` with a start time and a reason, tasks that didn't fit go in `skipped`, and `explain_plan()` turns both into readable text.

Known limits: the fit is greedy by priority (a long task can crowd out shorter ones), conflicts are warnings only (the later task is pushed back, never rejected or rearranged), and an overdue task that was never completed keeps appearing in each day's plan until it is done.

Run the demo with `python main.py` and the tests with `python -m pytest`.

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Output from running `python main.py` (owner Farwa with 90 minutes available, two pets, seven tasks added out of time order, with two deliberate conflicts):

```
All tasks, sorted by time:
  07:30  Morning walk (Biscuit) [daily, todo]
  07:45  Medication (Mochi) [once, todo]
  08:00  Breakfast (Mochi) [daily, todo]
  12:30  Play session (Mochi) [once, todo]
  12:30  Brush fur (Mochi) [once, todo]
  18:00  Evening walk (Biscuit) [daily, todo]
  --:--  Grooming (Biscuit) [weekly, todo]

Only Mochi's tasks:
  08:00  Breakfast (Mochi) [daily, todo]
  07:45  Medication (Mochi) [once, todo]
  12:30  Play session (Mochi) [once, todo]
  12:30  Brush fur (Mochi) [once, todo]

==================================================
Today's Schedule
==================================================
Daily plan for Farwa (90 min available):
  07:30-08:00 Morning walk (Biscuit) [30 min, high] - high priority; fits in the time available
  08:00-08:05 Medication (Mochi) [5 min, high] - high priority; fits in the time available; moved from 07:45 because an earlier task ran over
  08:05-08:15 Breakfast (Mochi) [10 min, high] - high priority; fits in the time available; moved from 08:00 because an earlier task ran over
  12:30-12:40 Brush fur (Mochi) [10 min, medium] - medium priority; fits in the time available
  12:40-13:00 Play session (Mochi) [20 min, medium] - medium priority; fits in the time available; moved from 12:30 because an earlier task ran over
Conflicts:
  Conflict (different pets): 'Medication' (Mochi) at 07:45 overlaps 'Morning walk' (Biscuit) 07:30-08:00
  Conflict (same pet): 'Play session' (Mochi) at 12:30 overlaps 'Brush fur' (Mochi) 12:30-12:40
Not scheduled:
  Evening walk (Biscuit) [medium] - needs 30 min but only 15 min left
  Grooming (Biscuit) [low] - needs 45 min but only 15 min left

Warnings:
  Conflict (different pets): 'Medication' (Mochi) at 07:45 overlaps 'Morning walk' (Biscuit) 07:30-08:00
  Conflict (same pet): 'Play session' (Mochi) at 12:30 overlaps 'Brush fur' (Mochi) 12:30-12:40

Completed 'Morning walk'. Next one is due 2026-10-26.

Pending tasks now:
  18:00  Evening walk (Biscuit) [daily, todo]
  --:--  Grooming (Biscuit) [weekly, todo]
  07:30  Morning walk (Biscuit) [daily, todo]
  08:00  Breakfast (Mochi) [daily, todo]
  07:45  Medication (Mochi) [once, todo]
  12:30  Play session (Mochi) [once, todo]
  12:30  Brush fur (Mochi) [once, todo]
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
============================= test session starts =============================
platform win32 -- Python 3.14.5, pytest-9.1.1, pluggy-1.7.0
collected 20 items

tests\test_pawpal.py ....................                                [100%]

============================= 20 passed in 0.09s ==============================
```

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_time()` | Clock order by preferred time; untimed tasks go last, ordered by priority. |
| Filtering | `Owner.filter_tasks()` | By pet name (case-insensitive), by completion status, or both. |
| Conflict detection | `Scheduler.find_conflicts()` | Warns when timed tasks overlap, for the same pet or different pets. |
| Recurring tasks | `Pet.complete_task()`, `Task.next_occurrence()` | Completing a daily or weekly task creates the next one. |

### Sorting
`Scheduler.sort_by_time(tasks)` uses `sorted()` with a tuple key: timed tasks first, in clock order (the `"HH:MM"` time is converted to minutes with `parse_time`, so a badly formatted time can't sort wrongly as text), then untimed tasks by priority. `generate_plan()` uses the same ordering to lay out the day.

### Filtering
`Owner.filter_tasks(pet_name=None, completed=None)` returns tasks matching a pet name and/or completion status. A filter left as `None` is ignored. It works on `Owner.get_all_tasks()`, so it covers every pet. The Streamlit app uses it for its "Show pet" and "Show status" menus.

### Conflict detection
`Scheduler.find_conflicts(tasks)` sorts the timed tasks by start time, then compares each one with the latest-ending task before it, so it takes one pass after sorting (O(n log n)). It counts any overlap, not only identical start times, and it flags clashes across different pets too, since the owner can't be in two places at once. Back-to-back tasks (one ends exactly when the next starts) are not conflicts. It returns warning strings and never raises an error. `generate_plan()` stores them in `scheduler.conflicts`, and `explain_plan()` and the app both show them. The plan is still built: the later task is pushed back until it no longer overlaps.

### Recurring tasks
Every task has a `due_date` (default today) and a `frequency` of `once`, `daily`, or `weekly`. `Pet.complete_task(task)` marks the task done and, for repeating tasks, adds the next occurrence from `Task.next_occurrence()`: a copy with the same details, due today + 1 day (daily) or today + 7 days (weekly), calculated with `datetime.timedelta`. Counting from today, not from the old due date, means a task finished late doesn't get a due date in the past. `generate_plan()` only includes tasks that are due on or before the day being planned and not yet completed, so a weekly task doesn't appear every day.

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
