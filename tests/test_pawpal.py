from pawpal_system import Pet, Task


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
