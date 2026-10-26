"""Happy-path and edge-case tests for PawPal+ (complements test_pawpal.py)."""

from datetime import date, timedelta

import pytest

from pawpal_system import DAY_START_MINUTE, Owner, Pet, Scheduler, Task, format_time, parse_time

TODAY = date(2026, 10, 25)


def make_owner(minutes=120):
    owner = Owner("Farwa", minutes)
    biscuit, mochi = Pet("Biscuit", "dog"), Pet("Mochi", "cat")
    owner.add_pet(biscuit)
    owner.add_pet(mochi)
    return owner, biscuit, mochi


def planned(owner):
    """Plan for TODAY as a list of (title, 'HH:MM-HH:MM')."""
    plan = Scheduler(owner).generate_plan(TODAY)
    return [(i.task.title, f"{format_time(i.start_minute)}-{format_time(i.end_minute)}") for i in plan]


# =============================== HAPPY PATHS ================================

def test_full_day_two_pets_happy_path():
    owner, biscuit, mochi = make_owner(minutes=120)
    biscuit.add_task(Task("Evening walk", 30, "medium", time="18:00", due_date=TODAY))
    biscuit.add_task(Task("Morning walk", 30, "high", time="07:30", due_date=TODAY))
    mochi.add_task(Task("Breakfast", 10, "high", time="08:00", due_date=TODAY))

    assert planned(owner) == [
        ("Morning walk", "07:30-08:00"),
        ("Breakfast", "08:00-08:10"),
        ("Evening walk", "18:00-18:30"),
    ]


def test_high_priority_wins_when_time_is_tight():
    owner, biscuit, _ = make_owner(minutes=30)
    biscuit.add_task(Task("Grooming", 30, "low", due_date=TODAY))
    biscuit.add_task(Task("Medication", 30, "high", due_date=TODAY))
    scheduler = Scheduler(owner)

    plan = scheduler.generate_plan(TODAY)

    assert [i.task.title for i in plan] == ["Medication"]
    assert [t.title for t, _ in scheduler.skipped] == ["Grooming"]


def test_completed_tasks_are_left_out_of_the_plan():
    owner, biscuit, _ = make_owner()
    done = Task("Walk", 30, due_date=TODAY)
    biscuit.add_task(done)
    biscuit.add_task(Task("Feed", 10, due_date=TODAY))
    done.mark_complete()

    assert [title for title, _ in planned(owner)] == ["Feed"]


def test_generating_the_plan_twice_does_not_duplicate_entries():
    owner, biscuit, _ = make_owner()
    biscuit.add_task(Task("Walk", 30, due_date=TODAY))
    scheduler = Scheduler(owner)

    scheduler.generate_plan(TODAY)
    scheduler.generate_plan(TODAY)

    assert len(scheduler.plan) == 1


def test_explain_plan_mentions_scheduled_and_skipped_tasks():
    owner, biscuit, _ = make_owner(minutes=30)
    biscuit.add_task(Task("Walk", 30, "high", due_date=TODAY))
    biscuit.add_task(Task("Grooming", 45, "low", due_date=TODAY))
    scheduler = Scheduler(owner)
    scheduler.generate_plan(TODAY)

    text = scheduler.explain_plan()

    assert "Walk (Biscuit)" in text and "Not scheduled" in text and "Grooming" in text


def test_parse_and_format_time_round_trip():
    assert parse_time("07:30") == 450
    assert format_time(450) == "07:30"
    assert format_time(parse_time("23:59")) == "23:59"


# ================================ EDGE CASES ================================

# --- pets and owners with nothing in them ---

def test_pet_with_no_tasks():
    pet = Pet("Biscuit", "dog")

    assert pet.get_tasks() == []


def test_owner_with_no_pets_has_no_tasks_and_an_empty_plan():
    owner = Owner("Farwa")

    assert owner.get_all_tasks() == []
    scheduler = Scheduler(owner)
    assert scheduler.generate_plan(TODAY) == []
    assert "No plan yet" in scheduler.explain_plan()


def test_pet_without_tasks_does_not_hide_other_pets_tasks():
    owner, biscuit, _ = make_owner()  # Mochi has no tasks
    biscuit.add_task(Task("Walk", 30, due_date=TODAY))

    assert [t.title for t in owner.get_all_tasks()] == ["Walk"]
    assert owner.filter_tasks(pet_name="Mochi") == []


# --- two tasks at the exact same time ---

def test_two_tasks_at_the_exact_same_time_conflict_and_both_get_scheduled():
    owner, biscuit, mochi = make_owner()
    biscuit.add_task(Task("Walk", 30, "high", time="08:00", due_date=TODAY))
    mochi.add_task(Task("Feed", 10, "medium", time="08:00", due_date=TODAY))
    scheduler = Scheduler(owner)

    plan = scheduler.generate_plan(TODAY)

    assert len(scheduler.conflicts) == 1
    # Higher priority keeps 08:00; the other is pushed to start when it ends.
    assert [(i.task.title, i.start_minute) for i in plan] == [
        ("Walk", parse_time("08:00")),
        ("Feed", parse_time("08:30")),
    ]


def test_three_tasks_at_the_same_time_report_two_conflicts():
    tasks = [Task(name, 10, time="09:00") for name in ("A", "B", "C")]

    assert len(Scheduler.find_conflicts(tasks)) == 2


def test_sort_by_time_breaks_ties_by_priority():
    low = Task("Low", 10, "low", time="08:00")
    high = Task("High", 10, "high", time="08:00")

    assert Scheduler.sort_by_time([low, high]) == [high, low]


def test_sort_by_time_does_not_modify_the_original_list():
    tasks = [Task("B", 10, time="12:00"), Task("A", 10, time="07:00")]

    Scheduler.sort_by_time(tasks)

    assert [t.title for t in tasks] == ["B", "A"]


# --- time budget boundaries ---

def test_task_that_exactly_fills_the_remaining_time_is_included():
    owner, biscuit, _ = make_owner(minutes=30)
    biscuit.add_task(Task("Walk", 30, due_date=TODAY))

    assert len(Scheduler(owner).generate_plan(TODAY)) == 1


def test_zero_minutes_available_schedules_nothing():
    owner, biscuit, _ = make_owner(minutes=0)
    biscuit.add_task(Task("Walk", 30, due_date=TODAY))
    scheduler = Scheduler(owner)

    assert scheduler.generate_plan(TODAY) == []
    assert len(scheduler.skipped) == 1


def test_single_task_longer_than_the_whole_budget_is_skipped_with_a_reason():
    owner, biscuit, _ = make_owner(minutes=20)
    biscuit.add_task(Task("Long hike", 60, due_date=TODAY))
    scheduler = Scheduler(owner)

    scheduler.generate_plan(TODAY)

    assert scheduler.plan == []
    assert "needs 60 min" in scheduler.skipped[0][1]


# --- where tasks are placed ---

def test_untimed_task_starts_at_the_beginning_of_the_day():
    owner, biscuit, _ = make_owner()
    biscuit.add_task(Task("Grooming", 20, due_date=TODAY))

    assert Scheduler(owner).generate_plan(TODAY)[0].start_minute == DAY_START_MINUTE


def test_timed_task_before_day_start_keeps_its_time():
    owner, biscuit, _ = make_owner()
    biscuit.add_task(Task("Early walk", 30, time="06:15", due_date=TODAY))

    assert planned(owner) == [("Early walk", "06:15-06:45")]


def test_untimed_task_is_placed_after_timed_tasks_it_would_overlap():
    owner, biscuit, _ = make_owner(minutes=200)
    biscuit.add_task(Task("Walk", 120, time="08:00", due_date=TODAY))
    biscuit.add_task(Task("Grooming", 20, due_date=TODAY))

    assert planned(owner) == [("Walk", "08:00-10:00"), ("Grooming", "10:00-10:20")]


# --- recurring tasks ---

def test_daily_task_completed_on_dec_31_is_next_due_jan_1():
    pet = Pet("Biscuit", "dog")
    walk = Task("Walk", 30, frequency="daily", due_date=date(2026, 12, 31))
    pet.add_task(walk)

    assert pet.complete_task(walk, today=date(2026, 12, 31)).due_date == date(2027, 1, 1)


def test_weekly_task_crosses_a_month_boundary():
    pet = Pet("Biscuit", "dog")
    bath = Task("Bath", 40, frequency="weekly", due_date=date(2026, 1, 28))
    pet.add_task(bath)

    assert pet.complete_task(bath, today=date(2026, 1, 28)).due_date == date(2026, 2, 4)


def test_completing_an_already_completed_task_does_not_create_a_duplicate():
    pet = Pet("Biscuit", "dog")
    walk = Task("Walk", 30, frequency="daily", due_date=TODAY)
    pet.add_task(walk)
    pet.complete_task(walk, today=TODAY)

    again = pet.complete_task(walk, today=TODAY)

    assert again is None
    assert len(pet.tasks) == 2  # the original and one next occurrence


def test_next_occurrence_is_not_due_today_so_it_is_left_out_of_todays_plan():
    owner, biscuit, _ = make_owner()
    walk = Task("Walk", 30, frequency="daily", due_date=TODAY)
    biscuit.add_task(walk)
    biscuit.complete_task(walk, today=TODAY)

    assert planned(owner) == []
    assert len(Scheduler(owner).generate_plan(TODAY + timedelta(days=1))) == 1


# --- validation and filtering ---

@pytest.mark.parametrize(
    "kwargs",
    [
        {"duration_minutes": 0},
        {"duration_minutes": -5},
        {"priority": "urgent"},
        {"frequency": "monthly"},
        {"time": "8:60"},
        {"time": "25:00"},
        {"time": "abc"},
    ],
)
def test_task_rejects_invalid_values(kwargs):
    values = {"title": "Walk", "duration_minutes": 30, **kwargs}

    with pytest.raises(ValueError):
        Task(**values)


def test_invalid_edit_leaves_the_task_unchanged():
    task = Task("Walk", 30, "high", time="08:00")

    with pytest.raises(ValueError):
        task.edit(title="Run", duration_minutes=-1)

    assert (task.title, task.duration_minutes) == ("Walk", 30)


def test_valid_edit_updates_only_the_given_fields():
    task = Task("Walk", 30, "high", time="08:00")

    task.edit(duration_minutes=45)

    assert (task.title, task.duration_minutes, task.priority, task.time) == ("Walk", 45, "high", "08:00")


def test_filter_with_unknown_pet_returns_nothing():
    owner, biscuit, _ = make_owner()
    biscuit.add_task(Task("Walk", 30))

    assert owner.filter_tasks(pet_name="Rex") == []


def test_negative_availability_is_rejected():
    owner = Owner("Farwa")

    with pytest.raises(ValueError):
        owner.set_availability(-5)


def test_removing_a_task_the_pet_does_not_have_raises():
    pet = Pet("Biscuit", "dog")

    with pytest.raises(ValueError):
        pet.remove_task(Task("Walk", 30))
