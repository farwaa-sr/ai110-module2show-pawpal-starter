from datetime import date, timedelta

import pytest

from pawpal_system import Owner, Pet, Scheduler, Task

TODAY = date(2026, 10, 25)


def make_owner(minutes=120):
    owner = Owner("Farwa", minutes)
    biscuit, mochi = Pet("Biscuit", "dog"), Pet("Mochi", "cat")
    owner.add_pet(biscuit)
    owner.add_pet(mochi)
    return owner, biscuit, mochi


def test_mark_complete_changes_task_status():
    task = Task("Morning walk", 30, "high")
    assert task.completed is False

    task.mark_complete()

    assert task.completed is True


def test_adding_task_increases_pet_task_count():
    pet = Pet("Biscuit", "dog")
    assert len(pet.get_tasks()) == 0

    pet.add_task(Task("Feeding", 10, "high"))
    assert len(pet.get_tasks()) == 1

    pet.add_task(Task("Grooming", 45, "low"))
    assert len(pet.get_tasks()) == 2


# --- sorting ---------------------------------------------------------------

def test_sort_by_time_orders_by_clock_with_untimed_last():
    tasks = [
        Task("Evening walk", 30, time="18:00"),
        Task("Grooming", 20),
        Task("Breakfast", 10, time="07:30"),
        Task("Lunch", 10, time="12:00"),
    ]

    titles = [t.title for t in Scheduler.sort_by_time(tasks)]

    assert titles == ["Breakfast", "Lunch", "Evening walk", "Grooming"]


def test_sort_by_time_handles_empty_list():
    assert Scheduler.sort_by_time([]) == []


# --- filtering -------------------------------------------------------------

def test_filter_tasks_by_pet_and_status():
    owner, biscuit, mochi = make_owner()
    walk, feed = Task("Walk", 30), Task("Feed", 10)
    biscuit.add_task(walk)
    mochi.add_task(feed)
    walk.mark_complete()

    assert owner.filter_tasks(pet_name="biscuit") == [walk]  # case-insensitive
    assert owner.filter_tasks(completed=False) == [feed]
    assert owner.filter_tasks(pet_name="Mochi", completed=True) == []
    assert len(owner.filter_tasks()) == 2


# --- recurring tasks -------------------------------------------------------

def test_completing_daily_task_creates_next_day_task():
    pet = Pet("Biscuit", "dog")
    walk = Task("Walk", 30, frequency="daily", due_date=TODAY)
    pet.add_task(walk)

    upcoming = pet.complete_task(walk, today=TODAY)

    assert walk.completed is True
    assert upcoming is not None and upcoming.completed is False
    assert upcoming.due_date == TODAY + timedelta(days=1)
    assert upcoming in pet.tasks and upcoming.pet_name == "Biscuit"


def test_completing_weekly_task_creates_task_a_week_later():
    pet = Pet("Biscuit", "dog")
    bath = Task("Bath", 40, frequency="weekly", due_date=TODAY)
    pet.add_task(bath)

    assert pet.complete_task(bath, today=TODAY).due_date == TODAY + timedelta(days=7)


def test_next_due_date_counts_from_today_even_when_completed_late():
    pet = Pet("Biscuit", "dog")
    walk = Task("Walk", 30, frequency="daily", due_date=TODAY - timedelta(days=3))
    pet.add_task(walk)

    upcoming = pet.complete_task(walk, today=TODAY)

    assert upcoming.due_date == TODAY + timedelta(days=1)


def test_next_occurrence_keeps_the_task_details():
    walk = Task("Walk", 30, "high", time="07:30", frequency="daily", due_date=TODAY)

    upcoming = walk.next_occurrence(TODAY)

    assert (upcoming.title, upcoming.duration_minutes, upcoming.priority, upcoming.time) == (
        "Walk",
        30,
        "high",
        "07:30",
    )
    assert upcoming is not walk


def test_completing_one_off_task_creates_nothing():
    pet = Pet("Biscuit", "dog")
    vet = Task("Vet visit", 60, frequency="once")
    pet.add_task(vet)

    assert pet.complete_task(vet) is None
    assert len(pet.tasks) == 1


def test_complete_task_rejects_task_from_another_pet():
    pet = Pet("Biscuit", "dog")
    with pytest.raises(ValueError):
        pet.complete_task(Task("Walk", 30))


def test_plan_only_includes_tasks_due_by_that_day():
    owner, biscuit, _ = make_owner()
    biscuit.add_task(Task("Today", 10, due_date=TODAY))
    biscuit.add_task(Task("Tomorrow", 10, due_date=TODAY + timedelta(days=1)))
    biscuit.add_task(Task("Overdue", 10, due_date=TODAY - timedelta(days=2)))

    plan = Scheduler(owner).generate_plan(TODAY)

    assert sorted(i.task.title for i in plan) == ["Overdue", "Today"]


# --- conflict detection ----------------------------------------------------

def test_overlapping_tasks_are_reported_as_conflicts():
    owner, biscuit, mochi = make_owner()
    biscuit.add_task(Task("Walk", 30, "high", time="08:00", due_date=TODAY))
    mochi.add_task(Task("Feed", 10, "high", time="08:15", due_date=TODAY))
    scheduler = Scheduler(owner)

    scheduler.generate_plan(TODAY)

    assert len(scheduler.conflicts) == 1
    assert "different pets" in scheduler.conflicts[0]
    assert "Feed" in scheduler.conflicts[0] and "Walk" in scheduler.conflicts[0]


def test_same_pet_conflict_is_labelled():
    owner, biscuit, _ = make_owner()
    biscuit.add_task(Task("Walk", 30, time="08:00", due_date=TODAY))
    biscuit.add_task(Task("Brush", 10, time="08:10", due_date=TODAY))

    warnings = Scheduler.find_conflicts(owner.get_all_tasks())

    assert len(warnings) == 1 and "same pet" in warnings[0]


def test_back_to_back_tasks_do_not_conflict():
    tasks = [Task("A", 30, time="08:00"), Task("B", 30, time="08:30")]

    assert Scheduler.find_conflicts(tasks) == []


def test_long_task_conflicts_with_every_task_inside_it():
    tasks = [
        Task("Long", 120, time="08:00"),
        Task("Inside 1", 10, time="08:30"),
        Task("Inside 2", 10, time="09:00"),  # would be missed by only checking the previous task
    ]

    assert len(Scheduler.find_conflicts(tasks)) == 2


def test_untimed_tasks_never_conflict():
    assert Scheduler.find_conflicts([Task("A", 30), Task("B", 30)]) == []


def test_conflicting_tasks_are_still_scheduled_without_overlap():
    owner, biscuit, mochi = make_owner()
    biscuit.add_task(Task("Walk", 30, "high", time="08:00", due_date=TODAY))
    mochi.add_task(Task("Feed", 10, "high", time="08:00", due_date=TODAY))

    plan = Scheduler(owner).generate_plan(TODAY)

    assert len(plan) == 2
    assert plan[0].end_minute <= plan[1].start_minute


# --- scheduler basics ------------------------------------------------------

def test_plan_reads_tasks_from_all_pets_and_respects_time_budget():
    owner, biscuit, mochi = make_owner(minutes=40)
    biscuit.add_task(Task("Walk", 30, "high", due_date=TODAY))
    mochi.add_task(Task("Feed", 10, "medium", due_date=TODAY))
    mochi.add_task(Task("Play", 20, "low", due_date=TODAY))
    scheduler = Scheduler(owner)

    plan = scheduler.generate_plan(TODAY)

    assert [i.task.title for i in plan] == ["Walk", "Feed"]
    assert [t.title for t, _ in scheduler.skipped] == ["Play"]


def test_plan_with_no_tasks_is_empty():
    owner, _, _ = make_owner()

    assert Scheduler(owner).generate_plan(TODAY) == []
