"""Temporary demo: build an owner, two pets, and tasks, then print today's schedule."""

from pawpal_system import Owner, Pet, Scheduler, Task, format_time


def main() -> None:
    owner = Owner(name="Farwa", available_minutes_per_day=90)

    biscuit = Pet(name="Biscuit", species="dog", age=4)
    mochi = Pet(name="Mochi", species="cat", age=2)
    owner.add_pet(biscuit)
    owner.add_pet(mochi)

    biscuit.add_task(Task("Morning walk", 30, "high", time="07:30", frequency="daily"))
    biscuit.add_task(Task("Evening walk", 30, "medium", time="18:00", frequency="daily"))
    biscuit.add_task(Task("Grooming", 45, "low", frequency="weekly"))
    mochi.add_task(Task("Breakfast", 10, "high", time="08:00", frequency="daily"))
    mochi.add_task(Task("Play session", 20, "medium", time="12:30"))

    scheduler = Scheduler(owner)
    scheduler.generate_plan()

    print("=" * 50)
    print("Today's Schedule")
    print("=" * 50)
    for item in scheduler.plan:
        task = item.task
        print(
            f"{format_time(item.start_minute)}-{format_time(item.end_minute)}  "
            f"{task.title} ({task.pet_name}) [{task.duration_minutes} min, {task.priority}]"
        )
    if scheduler.skipped:
        print("\nNot scheduled:")
        for task, why in scheduler.skipped:
            print(f"  {task.title} ({task.pet_name}) - {why}")

    print("\n" + scheduler.explain_plan())


if __name__ == "__main__":
    main()
