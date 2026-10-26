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

Known limits: `frequency` is stored but does not yet change the plan, the fit is greedy by priority (a long task can crowd out shorter ones), and overlapping preferred times are resolved by pushing the later task back rather than flagging a conflict.

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

Output from running `python main.py` (owner Farwa with 90 minutes available, two pets, five tasks):

```
==================================================
Today's Schedule
==================================================
07:30-08:00  Morning walk (Biscuit) [30 min, high]
08:00-08:10  Breakfast (Mochi) [10 min, high]
12:30-12:50  Play session (Mochi) [20 min, medium]
18:00-18:30  Evening walk (Biscuit) [30 min, medium]

Not scheduled:
  Grooming (Biscuit) - needs 45 min but only 0 min left

Daily plan for Farwa (90 min available):
  07:30-08:00 Morning walk (Biscuit) [30 min, high] - high priority; fits in the time available
  08:00-08:10 Breakfast (Mochi) [10 min, high] - high priority; fits in the time available
  12:30-12:50 Play session (Mochi) [20 min, medium] - medium priority; fits in the time available
  18:00-18:30 Evening walk (Biscuit) [30 min, medium] - medium priority; fits in the time available
Not scheduled:
  Grooming (Biscuit) [low] - needs 45 min but only 0 min left
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
# Paste your pytest output here
```

## 📐 Smarter Scheduling

> Fill in once you've implemented scheduling logic.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | | e.g., by priority, duration |
| Filtering | | e.g., skip tasks if time runs out |
| Conflict handling | | e.g., overlapping time slots |
| Recurring tasks | | e.g., daily vs. weekly |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
