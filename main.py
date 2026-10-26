"""Temporary demo: build an owner, two pets, and tasks, then exercise the scheduler."""

from pawpal_system import Owner, Pet, Scheduler, Task, format_time


def show_tasks(title: str, tasks: list[Task]) -> None:
    print(f"\n{title}")
    for t in tasks:
        status = "done" if t.completed else "todo"
        print(f"  {t.time or '--:--'}  {t.title} ({t.pet_name}) [{t.frequency}, {status}]")


def main() -> None:
    owner = Owner(name="Farwa", available_minutes_per_day=90)

    biscuit = Pet(name="Biscuit", species="dog", age=4)
    mochi = Pet(name="Mochi", species="cat", age=2)
    owner.add_pet(biscuit)
    owner.add_pet(mochi)

    # Added out of time order on purpose, to show sorting.
    evening_walk = Task("Evening walk", 30, "medium", time="18:00", frequency="daily")
    morning_walk = Task("Morning walk", 30, "high", time="07:30", frequency="daily")
    biscuit.add_task(evening_walk)
    biscuit.add_task(morning_walk)
    biscuit.add_task(Task("Grooming", 45, "low", frequency="weekly"))
    mochi.add_task(Task("Breakfast", 10, "high", time="08:00", frequency="daily"))
    mochi.add_task(Task("Medication", 5, "high", time="07:45"))  # overlaps the morning walk
    mochi.add_task(Task("Play session", 20, "medium", time="12:30"))
    mochi.add_task(Task("Brush fur", 10, "medium", time="12:30"))  # exact same time, same pet

    scheduler = Scheduler(owner)

    show_tasks("All tasks, sorted by time:", scheduler.sort_by_time(owner.get_all_tasks()))
    show_tasks("Only Mochi's tasks:", owner.filter_tasks(pet_name="Mochi"))

    scheduler.generate_plan()
    print("\n" + "=" * 50)
    print("Today's Schedule")
    print("=" * 50)
    print(scheduler.explain_plan())

    print("\nWarnings:")
    for warning in scheduler.conflicts or ["none"]:
        print(f"  {warning}")

    # Completing a daily task creates tomorrow's copy.
    upcoming = biscuit.complete_task(morning_walk)
    print(f"\nCompleted '{morning_walk.title}'. Next one is due {upcoming.due_date}.")
    show_tasks("Pending tasks now:", owner.filter_tasks(completed=False))


if __name__ == "__main__":
    main()
