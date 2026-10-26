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

## Features

- **Multiple pets, one plan**: an owner can have several pets, each with its own tasks. The scheduler gathers every pet's tasks through `Owner.get_all_tasks()`, so one daily plan covers all of them.
- **Priority-based planning within your time**: `Scheduler.generate_plan()` takes tasks by priority (high, then medium, then low) until the owner's available minutes for the day run out.
- **Sorting by time**: `Scheduler.sort_by_time()` puts tasks in clock order; tasks with no preferred time go last.
- **Filtering**: `Owner.filter_tasks()` shows tasks for one pet, only finished or unfinished tasks, or both filters together.
- **Conflict warnings**: `Scheduler.find_conflicts()` flags tasks whose times overlap, whether for the same pet or different pets, and returns a warning instead of failing. The plan still gets built, with the later task moved back.
- **Daily and weekly recurrence**: completing a repeating task with `Pet.complete_task()` creates the next one, due tomorrow (daily) or in 7 days (weekly).
- **Due dates**: each task has a due date, and a plan only includes tasks that are due and not yet done.
- **A plan that explains itself**: every scheduled task has a reason, and every task that did not fit is listed with why (`Scheduler.explain_plan()`).
- **Input checks**: bad durations, priorities, frequencies, and times (such as `25:00`) are rejected with a clear message instead of breaking the plan.

## Implementation summary

The logic layer lives in `pawpal_system.py` and is built from four classes (plus a small `ScheduledTask` record). See `uml_diagram.md` for the final class diagram (Mermaid source in `diagrams/uml_final.mmd`).

- **Task**: one care activity with a title, duration, priority (high/medium/low), optional preferred time (`"HH:MM"`), frequency (once/daily/weekly), and completion status. It validates its own fields.
- **Pet**: a name, species, age, and a list of tasks. Adding a task tags it with the pet's name.
- **Owner**: holds the daily minutes available and a list of pets. `get_all_tasks()` returns every pet's tasks together.
- **Scheduler**: the "brain". `generate_plan()` reads tasks only through `Owner.get_all_tasks()`, so one plan covers all pets. It skips completed tasks, takes the rest by priority while they fit in the owner's available minutes, and lays them out in time order (untimed tasks start at 08:00). Each plan entry is a `ScheduledTask` with a start time and a reason, tasks that didn't fit go in `skipped`, and `explain_plan()` turns both into readable text.

Known limits: the fit is greedy by priority (a long task can crowd out shorter ones), conflicts are warnings only (the later task is pushed back, never rejected or rearranged), and an overdue task that was never completed keeps appearing in each day's plan until it is done.

### How the design changed from the first UML

The first diagram had the four classes with only basic attributes and methods. Building and testing the app changed it in these places (the final diagram is in `diagrams/uml_final.mmd`):

- **Task**: gained `time`, `frequency`, and `due_date` so tasks can be ordered, repeated, and planned by day. It also gained `next_occurrence()` and input validation. `pet_name` was added so a task still knows its pet after all pets' tasks are combined into one list.
- **Pet**: gained `complete_task()`, which marks a task done and adds the next occurrence of a repeating task. It lives on `Pet` because the pet owns the task list the new task has to be added to.
- **Owner**: gained `filter_tasks()` for filtering by pet and status.
- **ScheduledTask**: a new class (task, start time, reason). The plan needs start times, and keeping the reason on each entry replaced the separate `explanations` dictionary.
- **Scheduler**: gained `sort_by_time()` and `find_conflicts()` (static, so they work on any list of tasks), plus `conflicts` and `skipped` to record what it flagged and what did not fit. `generate_plan()` now takes an optional day.
- **New relationships**: the Scheduler reads tasks only through `Owner.get_all_tasks()`, and `Pet` and `Task` create new `Task` objects when a task repeats.

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

Run the full test suite from the project folder (with the virtual environment active):

```bash
python -m pytest
```

### What the tests cover

56 tests in `tests/test_pawpal.py` and `tests/test_edge_cases.py`:

- **Sorting:** tasks come back in clock order with untimed tasks last, ties at the same time are broken by priority, and the original list is not modified.
- **Filtering:** by pet (case-insensitive), by completion status, and both together; an unknown pet returns nothing.
- **Recurring tasks:** completing a daily or weekly task creates the next one due today + 1 or + 7 days, including across month and year boundaries and when completed late; one-off tasks create nothing; completing a task twice does not create a duplicate.
- **Conflict detection:** overlaps and exact same-time starts are flagged for the same pet and for different pets; back-to-back tasks are not conflicts; one long task containing several others is caught.
- **Plan building:** priority order under a tight time budget, an exact fit, zero minutes available, a task longer than the whole budget, completed and not-yet-due tasks left out, no duplicates when the plan is generated twice, and correct start times for timed and untimed tasks.
- **Edge cases and validation:** a pet with no tasks, an owner with no pets, and invalid durations, priorities, frequencies and times (such as `"8:60"` and `"25:00"`) are rejected, and a failed `edit()` leaves the task unchanged.

The edge-case tests found two real bugs, both fixed: `"8:60"` was accepted as a valid time, and completing an already-completed recurring task created a duplicate.

### Test output

```
============================= test session starts =============================
platform win32 -- Python 3.14.5, pytest-9.1.1, pluggy-1.7.0
rootdir: C:\Users\farwa\.vscode\.venv\Projects\ai110-module2show-pawpal-starter
plugins: anyio-4.15.1
collected 56 items

tests\test_edge_cases.py ...................................             [ 62%]
tests\test_pawpal.py .....................                               [100%]

============================= 56 passed in 0.15s ==============================
```

### Confidence level: ⭐⭐⭐⭐ (4 out of 5)

I'm confident in the scheduling logic (sorting, filtering, recurrence, conflict detection, and plan building), because each has both happy-path and edge-case tests and the tests already caught two real bugs. I stopped at four stars because:

- the Streamlit UI (`app.py`) is not covered by the test suite; I only checked it by hand with Streamlit's test runner;
- a task that runs past midnight is not handled or tested;
- the scheduler is greedy by priority, so it is not guaranteed to fit the most care into the available time.

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

Start the app with `streamlit run app.py` (with the virtual environment active).

### What you can do in the app

- **Owner**: set your name and how many minutes per day you have for pet care.
- **Pets**: add a pet (name, species, age). Empty and duplicate names are rejected.
- **Tasks**: add a task for a pet with a title, duration, priority, frequency (once, daily, weekly), and an optional preferred time.
- **Mark done**: finish a task. A daily or weekly task automatically gets its next occurrence.
- **Task list**: filter by pet and by status (all, to do, done). The list is always sorted by time, with untimed tasks last.
- **Conflict warning**: if two tasks overlap, a warning appears right away, naming both tasks and suggesting a fix.
- **Generate schedule**: builds today's plan, with a summary of tasks scheduled and minutes used, a table with the reason for each entry, and a list of tasks that did not fit.

### Example workflow

1. Set the owner name and available minutes (say 90).
2. Add two pets, for example Biscuit (dog) and Mochi (cat).
3. Add tasks: a high-priority "Morning walk" for Biscuit at 07:30, a high-priority "Breakfast" for Mochi at 08:00, and a medium-priority "Medication" for Mochi at 07:45.
4. Medication overlaps the walk, so a conflict warning appears under the task list.
5. Click **Generate schedule**. The plan shows the tasks in time order, and the later overlapping tasks moved back. With only these three short tasks everything fits in 90 minutes; add a long low-priority task, such as a 60-minute grooming, to see the time budget leave it out with a reason.
6. Mark "Morning walk" done. Tomorrow's walk now appears in the task list, due the next day.

### Scheduler behaviors shown

- **Sorting**: tasks added out of order come back in clock order.
- **Filtering**: the task list narrows to one pet or one status.
- **Conflict warnings**: overlapping and same-time tasks are flagged for the same pet and for different pets, and the plan still gets built.
- **Time budget**: lower-priority tasks are skipped, with a reason, when the available minutes run out.
- **Recurrence**: completing a daily task creates a new one due the next day.

### Sample command-line output

`python main.py` runs the same logic without the UI. This is an excerpt of its output (the full output is in Sample Output above):

```
All tasks, sorted by time:
  07:30  Morning walk (Biscuit) [daily, todo]
  07:45  Medication (Mochi) [once, todo]
  08:00  Breakfast (Mochi) [daily, todo]
  12:30  Play session (Mochi) [once, todo]
  12:30  Brush fur (Mochi) [once, todo]
  18:00  Evening walk (Biscuit) [daily, todo]
  --:--  Grooming (Biscuit) [weekly, todo]

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

Completed 'Morning walk'. Next one is due 2026-10-26.
```

*No screenshot is included.*
