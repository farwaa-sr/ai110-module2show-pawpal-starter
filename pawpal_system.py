"""PawPal+ logic layer: backend classes for owners, pets, tasks, and scheduling.

Based on uml_diagram.md. The Scheduler reads every task through
Owner.get_all_tasks(), so plans cover all of an owner's pets at once.
"""

from dataclasses import dataclass, field
from typing import Optional

# Lower number = scheduled first. Lets the Scheduler sort priorities without string checks.
PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
FREQUENCIES = ("once", "daily", "weekly")
DAY_START_MINUTE = 8 * 60  # plans begin at 08:00


def parse_time(text: str) -> int:
    """Convert "HH:MM" to minutes after midnight."""
    try:
        hours, minutes = text.split(":")
        value = int(hours) * 60 + int(minutes)
    except ValueError:
        raise ValueError(f"Time must look like 'HH:MM', got {text!r}") from None
    if not 0 <= value < 24 * 60:
        raise ValueError(f"Time out of range: {text!r}")
    return value


def format_time(minute: int) -> str:
    """Convert minutes after midnight to "HH:MM"."""
    return f"{minute // 60:02d}:{minute % 60:02d}"


@dataclass
class Task:
    """A single care activity (walk, feeding, meds, enrichment, grooming)."""

    title: str
    duration_minutes: int
    priority: str = "medium"  # "high" | "medium" | "low"
    category: str = "general"
    time: Optional[str] = None  # preferred start as "HH:MM"; None = scheduler decides
    frequency: str = "once"  # "once" | "daily" | "weekly"
    completed: bool = False
    pet_name: str = ""  # set by Pet.add_task so a flattened task list keeps its pet

    def __post_init__(self) -> None:
        """Validate the fields as soon as the task is created."""
        self._validate()

    def _validate(self) -> None:
        """Raise ValueError if duration, priority, frequency, or time is invalid."""
        if self.duration_minutes <= 0:
            raise ValueError("duration_minutes must be positive")
        if self.priority not in PRIORITY_ORDER:
            raise ValueError(f"priority must be one of {list(PRIORITY_ORDER)}")
        if self.frequency not in FREQUENCIES:
            raise ValueError(f"frequency must be one of {list(FREQUENCIES)}")
        if self.time is not None:
            parse_time(self.time)

    def edit(
        self,
        title: Optional[str] = None,
        duration_minutes: Optional[int] = None,
        priority: Optional[str] = None,
        time: Optional[str] = None,
        frequency: Optional[str] = None,
    ) -> None:
        """Update any of the given fields; fields left as None are unchanged."""
        old = (self.title, self.duration_minutes, self.priority, self.time, self.frequency)
        if title is not None:
            self.title = title
        if duration_minutes is not None:
            self.duration_minutes = duration_minutes
        if priority is not None:
            self.priority = priority
        if time is not None:
            self.time = time
        if frequency is not None:
            self.frequency = frequency
        try:
            self._validate()
        except ValueError:
            self.title, self.duration_minutes, self.priority, self.time, self.frequency = old
            raise

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.completed = True


@dataclass
class Pet:
    """An animal being cared for. Owns its list of tasks."""

    name: str
    species: str
    age: int = 0
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a care task to this pet and tag the task with the pet's name."""
        task.pet_name = self.name
        self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Remove a care task; raises ValueError if the pet doesn't have it."""
        self.tasks.remove(task)

    def get_tasks(self) -> list[Task]:
        """Return a copy of this pet's tasks."""
        return list(self.tasks)


@dataclass
class Owner:
    """The person using the app; supplies the daily time constraint."""

    name: str
    available_minutes_per_day: int = 120
    preferences: dict = field(default_factory=dict)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        self.pets.append(pet)

    def get_all_tasks(self) -> list[Task]:
        """Return every task from every one of this owner's pets, together."""
        return [task for pet in self.pets for task in pet.get_tasks()]

    def set_availability(self, minutes: int) -> None:
        """Set how many minutes per day the owner has for pet care."""
        if minutes < 0:
            raise ValueError("available minutes cannot be negative")
        self.available_minutes_per_day = minutes


@dataclass
class ScheduledTask:
    """One entry in the daily plan: a task placed at a start time, with the reason why."""

    task: Task
    start_minute: int  # minutes after midnight, e.g. 480 = 08:00
    reason: str = ""

    @property
    def end_minute(self) -> int:
        """Minute of the day when this task finishes."""
        return self.start_minute + self.task.duration_minutes


class Scheduler:
    """Turns an owner's tasks and time limit into a daily plan with explanations."""

    def __init__(self, owner: Owner) -> None:
        """Create a scheduler for one owner, with an empty plan."""
        self.owner = owner
        self.plan: list[ScheduledTask] = []
        self.skipped: list[tuple[Task, str]] = []  # (task, why it did not fit)

    def generate_plan(self) -> list[ScheduledTask]:
        """Rebuild the plan from scratch.

        Pulls tasks from Owner.get_all_tasks() (all pets), skips completed ones,
        and takes the rest by priority (then earlier preferred time, then shorter
        duration) while they fit in the owner's available minutes. Chosen tasks
        are laid out in time order, starting at 08:00 or their preferred time.
        """
        self.plan = []
        self.skipped = []
        budget = self.owner.available_minutes_per_day

        pending = [t for t in self.owner.get_all_tasks() if not t.completed]
        pending.sort(key=self._priority_key)

        chosen: list[tuple[Task, str]] = []
        used = 0
        for task in pending:
            if used + task.duration_minutes <= budget:
                used += task.duration_minutes
                chosen.append((task, f"{task.priority} priority; fits in the time available"))
            else:
                left = budget - used
                self.skipped.append(
                    (task, f"needs {task.duration_minutes} min but only {left} min left")
                )

        # Lay out chosen tasks in time order; tasks with a preferred time come at that time.
        chosen.sort(key=lambda item: self._time_key(item[0]))
        cursor = 0  # end of the previous task; untimed tasks never start before DAY_START_MINUTE
        for task, reason in chosen:
            if task.time is not None:
                preferred = parse_time(task.time)
                start = max(cursor, preferred)
                if start != preferred:
                    reason += f"; moved from {task.time} because an earlier task ran over"
            else:
                start = max(cursor, DAY_START_MINUTE)
            self.plan.append(ScheduledTask(task, start, reason))
            cursor = start + task.duration_minutes
        return self.plan

    def explain_plan(self) -> str:
        """Explain why each task was included or left out of the plan."""
        if not self.plan and not self.skipped:
            return "No plan yet: there are no pending tasks."
        lines = [f"Daily plan for {self.owner.name} "
                 f"({self.owner.available_minutes_per_day} min available):"]
        for item in self.plan:
            task = item.task
            who = f" ({task.pet_name})" if task.pet_name else ""
            lines.append(
                f"  {format_time(item.start_minute)}-{format_time(item.end_minute)} "
                f"{task.title}{who} [{task.duration_minutes} min, {task.priority}] "
                f"- {item.reason}"
            )
        if self.skipped:
            lines.append("Not scheduled:")
            for task, why in self.skipped:
                who = f" ({task.pet_name})" if task.pet_name else ""
                lines.append(f"  {task.title}{who} [{task.priority}] - {why}")
        return "\n".join(lines)

    @staticmethod
    def _priority_key(task: Task) -> tuple:
        """Sort key for choosing tasks: priority, then earlier preferred time, then shorter."""
        preferred = parse_time(task.time) if task.time else 24 * 60
        return (PRIORITY_ORDER[task.priority], preferred, task.duration_minutes)

    @staticmethod
    def _time_key(task: Task) -> tuple:
        """Sort key for laying out the plan: timed tasks in clock order, then untimed by priority."""
        if task.time is not None:
            return (0, parse_time(task.time), PRIORITY_ORDER[task.priority])
        return (1, 0, PRIORITY_ORDER[task.priority])
