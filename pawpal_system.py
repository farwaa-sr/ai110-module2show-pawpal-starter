"""PawPal+ logic layer: backend classes for owners, pets, tasks, and scheduling.

Class stubs based on uml_diagram.md. Method bodies are not implemented yet.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Task:
    """A single care activity (walk, feeding, meds, enrichment, grooming)."""

    title: str
    duration_minutes: int
    priority: str = "medium"  # "high" | "medium" | "low"
    category: str = "general"
    completed: bool = False

    def edit(
        self,
        title: Optional[str] = None,
        duration_minutes: Optional[int] = None,
        priority: Optional[str] = None,
    ) -> None:
        """Update this task's title, duration, and/or priority."""
        pass

    def mark_complete(self) -> None:
        """Mark this task as done."""
        pass


@dataclass
class Pet:
    """An animal being cared for. Owns its list of tasks."""

    name: str
    species: str
    age: int = 0
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a care task to this pet."""
        pass

    def remove_task(self, task: Task) -> None:
        """Remove a care task from this pet."""
        pass

    def get_tasks(self) -> list[Task]:
        """Return this pet's tasks."""
        pass


@dataclass
class Owner:
    """The person using the app; supplies the daily time constraint."""

    name: str
    available_minutes_per_day: int = 120
    preferences: dict = field(default_factory=dict)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        pass

    def get_all_tasks(self) -> list[Task]:
        """Return the tasks of all of this owner's pets."""
        pass

    def set_availability(self, minutes: int) -> None:
        """Set how many minutes per day the owner has for pet care."""
        pass


class Scheduler:
    """Turns an owner's tasks and time limit into a daily plan with explanations."""

    def __init__(self, owner: Owner) -> None:
        self.owner = owner
        self.plan: list[Task] = []
        self.explanations: dict = {}

    def generate_plan(self) -> list[Task]:
        """Build the daily plan: order tasks by priority and fit them in the available time."""
        pass

    def explain_plan(self) -> str:
        """Explain why each task was included or left out of the plan."""
        pass
