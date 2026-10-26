# PawPal+ UML Class Diagram (final)

This matches the final `pawpal_system.py`. The Mermaid source is also saved as
[diagrams/uml_final.mmd](diagrams/uml_final.mmd).

```mermaid
classDiagram
    class Owner {
        +str name
        +int available_minutes_per_day
        +dict preferences
        +list~Pet~ pets
        +add_pet(pet) void
        +get_all_tasks() list~Task~
        +filter_tasks(pet_name, completed) list~Task~
        +set_availability(minutes) void
    }

    class Pet {
        +str name
        +str species
        +int age
        +list~Task~ tasks
        +add_task(task) void
        +remove_task(task) void
        +get_tasks() list~Task~
        +complete_task(task, today) Task
    }

    class Task {
        +str title
        +int duration_minutes
        +str priority
        +str category
        +str time
        +str frequency
        +bool completed
        +str pet_name
        +date due_date
        +edit(title, duration_minutes, priority, time, frequency) void
        +mark_complete() void
        +next_occurrence(today) Task
        -_validate() void
    }

    class ScheduledTask {
        +Task task
        +int start_minute
        +str reason
        +end_minute int
    }

    class Scheduler {
        +Owner owner
        +list~ScheduledTask~ plan
        +list skipped
        +list~str~ conflicts
        +sort_by_time(tasks)$ list~Task~
        +find_conflicts(tasks)$ list~str~
        +generate_plan(day) list~ScheduledTask~
        +explain_plan() str
    }

    Owner "1" --> "1..*" Pet : has
    Pet "1" --> "0..*" Task : has
    Scheduler "1" --> "1" Owner : reads all tasks via get_all_tasks()
    Scheduler "1" --> "0..*" ScheduledTask : produces plan
    ScheduledTask "1" --> "1" Task : places
    Scheduler ..> Task : sorts, checks conflicts, records skipped
    Pet ..> Task : complete_task() adds the next occurrence
    Task ..> Task : next_occurrence() makes a copy for the next due date
```

## What changed from the initial design

- **Task** gained `time`, `frequency` and `due_date`, validation, `next_occurrence()`, and a wider `edit()`.
- **Pet** gained `complete_task()`, which marks a task done and adds the next occurrence of repeating tasks.
- **Owner** gained `filter_tasks()` (by pet and/or status).
- **ScheduledTask** is new: a task placed at a start time, with the reason it was placed there.
- **Scheduler** gained `sort_by_time()` and `find_conflicts()` (static, so they work on any list of tasks), `conflicts`, and `skipped`. `generate_plan()` takes an optional day. The old `explanations` dict was replaced by `ScheduledTask.reason`.
- **Relationships:** the Scheduler reads tasks only through `Owner.get_all_tasks()`, so one plan covers every pet. `Pet` and `Task` also create new `Task` objects when a task repeats.

Not shown: the module-level helpers `parse_time()` and `format_time()` and the constants `PRIORITY_ORDER`, `FREQUENCIES`, `RECURRENCE_DAYS` and `DAY_START_MINUTE`.
