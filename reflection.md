# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

PawPal+ helps a busy pet owner stay consistent with pet care by tracking care tasks, respecting constraints like available time and priority, and producing a daily plan with an explanation. I identified three core actions a user should be able to perform:

1. **Enter owner and pet information.** The user starts by telling the app who they are and about their pet (for example, the pet's name and species) along with any constraints, such as how much time they have available each day. Everything else in the app hangs off this information.
2. **Add and edit care tasks.** The user can add care tasks for their pet, such as walks, feeding, medication, enrichment, or grooming. Each task has at least a duration and a priority, and the user can change them later as needs change.
3. **Generate and view today's plan.** The user asks the app to build a daily schedule from their tasks and constraints. The app shows the plan clearly, ordered by priority and fit within the available time, and explains why it chose that plan and why any tasks were left out.

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

Building blocks (initial brainstorm):

**Owner** — the person using the app and the source of the daily constraints.
- Attributes: name, available_minutes_per_day, preferences (e.g. preferred walk times), pets (list of Pet)
- Methods: add_pet(), get_all_tasks(), set_availability()

**Pet** — the animal being cared for; it owns its own tasks.
- Attributes: name, species, age, tasks (list of Task)
- Methods: add_task(), remove_task(), get_tasks()

**Task** — a single care activity (walk, feeding, meds, enrichment, grooming).
- Attributes: title, duration_minutes, priority (high/medium/low), category, completed
- Methods: edit(), mark_complete()

**Scheduler** — the logic that turns tasks and constraints into a daily plan.
- Attributes: owner, plan (list of scheduled tasks), explanations
- Methods: generate_plan() (sort by priority, fit within available time), explain_plan() (why each task was included or skipped)

**Relationships:** an Owner has one or more Pets, a Pet has many Tasks, and the Scheduler reads the Owner's tasks and time limit to produce the plan.

The full Mermaid class diagram is in [uml_diagram.md](uml_diagram.md). It was first drawn from this brainstorm and then updated to match the final code; the final source is [diagrams/uml_final.mmd](diagrams/uml_final.mmd).

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

After writing the class skeleton in `pawpal_system.py`, I asked my AI coding assistant to review it for missing relationships and logic bottlenecks. I made these changes based on its feedback:

1. **Added `Task.pet_name`.** `Owner.get_all_tasks()` flattens every pet's tasks into one list, so a task would no longer know which pet it was for. The plan needs that to say things like "Walk for Biscuit".
2. **Added a `ScheduledTask` class** (task, start time, reason) and changed `Scheduler.plan` to hold these instead of bare `Task`s. A plain list of tasks has no times, but the daily plan needs them. Putting the reason on each entry also replaced the separate `explanations` dict, which would have had to be kept in sync with the plan.
3. **Added `Scheduler.skipped`** (tasks that didn't fit, with the reason). `explain_plan()` has to explain what was left out, and nothing in the original design recorded that.
4. **Added `PRIORITY_ORDER`.** Priority is a string, and sorting `"high"`/`"medium"`/`"low"` alphabetically gives the wrong order. A mapping gives the scheduler a reliable sort key.

Issues I noted at that point, and what happened to each:
- `generate_plan()` must rebuild the plan from scratch each time and skip completed tasks, or the stored plan goes stale when tasks change. **Done:** it resets the plan on every call and skips completed tasks.
- A greedy "highest priority first" fit can let one long task block several short ones. **Still open:** it is the tradeoff described in section 2b.
- There was no recurrence (daily or weekly tasks) yet. **Done:** see change 6 below.
- `Owner.available_minutes_per_day` and `set_availability()` overlap, and nothing validated the value. **Partly done:** `set_availability()` now rejects negative minutes, but the field can still be set directly, so the overlap remains.

Later changes, made while adding sorting, filtering, recurring tasks, and conflict detection (the final diagram is in [diagrams/uml_final.mmd](diagrams/uml_final.mmd)):

5. **Added `Task.time`, `Task.frequency`, and `Task.due_date`, plus validation.** Sorting needs a time, recurrence needs a frequency, and planning by day needs a due date. Validation (`_validate()`) was added so bad values are rejected when a task is created or edited, and `edit()` grew to cover the new fields.
6. **Added `Task.next_occurrence()` and `Pet.complete_task()`.** Completing a daily or weekly task now creates the next one. I put the "complete and spawn" step on `Pet`, not `Task`, because the new task has to be added to the pet's own task list, and a task does not know its pet's list. This also added two new relationships to the diagram: `Pet` and `Task` both create new `Task` objects.
7. **Added `Owner.filter_tasks()`.** Filtering by pet and status works over `get_all_tasks()`, so it covers every pet and belongs with the class that owns the pets.
8. **Added `Scheduler.sort_by_time()` and `Scheduler.find_conflicts()` as static methods, plus `Scheduler.conflicts`.** They take a list of tasks and do not need a scheduler's state, so they work on any list, which also made them easy to test. `conflicts` stores the warnings from the latest plan. `generate_plan()` also gained an optional `day`, so it only plans tasks that are due.
9. **Added `ScheduledTask.end_minute`.** The plan and the conflict messages both need the end time of an entry.

Two of these came from testing, not from planning: the tests found that an already-completed repeating task could create a duplicate next occurrence (so `complete_task()` now does nothing the second time), and that a time like `"8:60"` was accepted (so `parse_time()` now checks hours and minutes separately).

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

The scheduler considers four things:
1. **The owner's available minutes per day.** This is a hard limit: the plan never schedules more than the owner has time for.
2. **Priority** (high, medium, low). It decides which tasks get the limited time first, and therefore which ones are skipped.
3. **Preferred times.** A task can have a start time. This is a soft constraint: if two tasks overlap, the later one is moved back and the owner gets a warning.
4. **Completion and due date.** Completed tasks and tasks not yet due are left out of the day's plan.

I ranked them by how bad it is to get them wrong. Going over the owner's time makes the plan useless, so the time budget comes first. Priority comes next because it is the fairest way to decide what to drop when time runs out: a medication should not be skipped for grooming. Preferred times came last because they can be bent (moving a task by a few minutes costs little), while the first two cannot.

One thing I did not use: `Owner.preferences` exists as a field, but no scheduler logic reads it yet.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

**Tradeoff: conflicts are warnings, and only preferred times are checked.** When two timed tasks overlap, the scheduler does not refuse the task or try to rearrange the day. `find_conflicts()` returns a warning message and the plan keeps both tasks, pushing the later one back until it no longer overlaps. The check compares the preferred time windows (start time plus duration), so overlaps count and not only exact matches. It runs before pushback, so a task that gets moved because an earlier one moved is explained by its "moved from" reason, not by a separate conflict warning.

Why this is reasonable: a pet owner usually cares more about getting a complete, usable plan than about a perfect one. A warning tells them about the clash and lets them decide (for example, feed the cat first, then walk the dog), while a rejected task would silently drop care that still needs to happen. Pushing back is also simple and predictable. The cost is that the plan can drift later in the day than the owner asked for, and the scheduler never tries a smarter arrangement, such as moving an untimed task out of the way of a timed one.

Algorithm review: I compared my `find_conflicts()` against two shorter versions on the tricky cases. Checking only adjacent tasks with `itertools.pairwise` is the shortest, but it missed conflicts when one long task contains several short ones (it reported 1 warning where 2 were expected in one test case, and 1 where 3 were expected in another). Checking every pair with `itertools.combinations` found the same conflicts as mine and is arguably the easiest to read, but it is O(n²) instead of O(n log n). I kept my version: sort once, then compare each task with the latest-ending earlier task. It is a few lines longer, but it is correct on every case I tested, it stays fast as the task list grows, and the loop is still easy to follow.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

I used an AI coding assistant (Claude Code) across the whole project: brainstorming the four classes and their attributes and methods, drafting the Mermaid UML diagram, writing the class skeleton, reviewing that skeleton for gaps, implementing the logic, writing the demo script and tests, and adding docstrings. The most helpful prompts were specific and tied to a step of the assignment, for example "create a Mermaid class diagram based on the attributes and methods we brainstormed" or "review my skeleton for missing relationships and logic bottlenecks". Asking for a review of existing code gave more useful feedback than asking for code from scratch.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

What the AI suggested, and what I did with it:
- **Accepted (design review):** adding `Task.pet_name`, a `ScheduledTask` class, `Scheduler.skipped`, and a `PRIORITY_ORDER` mapping. Each fixed a real gap: tasks lost their pet when flattened, the plan had no times, skipped tasks weren't recorded, and string priorities sort wrongly.
- **Noted but not built:** recurring-task behavior, a smarter fit than greedy priority order, and validation of the owner's availability. I recorded them in section 1b as known limits instead of expanding the scope.
- **Rejected (setup):** the AI's first plan for the broken virtual environment was to delete and rebuild it. I asked whether it would affect my files, and it turned out my Projects folder was inside that environment's folder, so the plan would have deleted my work. We created a separate environment instead.

How I verified the result: I ran `main.py` rather than trusting the code. That run exposed a real bug in the AI's scheduler: the 07:30 morning walk was moved to 08:00 with the reason "an earlier task ran over", although nothing ran earlier. The day-start time was being applied to every task. It was fixed so that 08:00 only applies to tasks with no preferred time, and the rerun showed the walk at 07:30. I also added pytest tests for marking a task complete and for adding a task to a pet.

**c. AI strategy**

*Which features were most effective?* Three things worked best:
- **Working directly in the project.** The assistant could read my files, edit several files at once, and run the code. Running `main.py` is what exposed the 07:30 walk bug, and running the tests found the two bugs described in section 4. Code that is only suggested in a chat window never gets that check.
- **Asking for a review of code that already existed**, for example the skeleton review in 1b. It gave more useful feedback than asking for code from nothing.
- **Tests as a way to check the AI's work.** I did not have to read every line it wrote; I could ask whether the behavior was right and let the tests answer.

*An AI suggestion I modified.* The assignment said a repeating task's next due date should be "today + 1 day". The first version the assistant wrote counted from the task's old due date instead, which looks equivalent but is not: a daily walk finished 3 days late would get a next date that was still in the past. I had it change the calculation to count from today and added a test for the late case. In the same spirit, when it offered shorter ways to write conflict detection, I had it compare them on tricky cases first, and I kept the longer version because the shorter `pairwise` one missed conflicts (see 2b).

*Separate chat sessions.* I did not actually use separate chat sessions. I worked through every phase in one continuous session and kept organized with the assignment's steps, the commits after each phase, and the README and reflection files as running notes. A fresh session for testing might have helped: the assistant that wrote the scheduler also wrote its tests and reviewed its skeleton, so it may share its own blind spots. The tests still caught real bugs, but I would try a separate session for the testing phase next time.

*What I learned about being the lead architect.* The assistant is fast, but it works on what it is told, so the decisions that shape the system have to come from me. Examples from this project: I chose warn-only conflicts and spawning a new task for recurrence, I asked "will it mess with my files?" before a venv rebuild that would have deleted my projects folder, and I rejected putting the virtual environment inside the repo. Designing the classes and their responsibilities first (the UML) gave the AI a clear structure to build inside, so its code fit together instead of drifting. And the habit that mattered most was verifying: running the code and the tests, not trusting a confident answer.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

I wrote 56 tests covering sorting (clock order, untimed tasks last, ties broken by priority), filtering by pet and status, recurring tasks (the next daily or weekly task, month and year boundaries, completing late, completing twice), conflict detection (overlaps, exact same time, same pet and different pets, back-to-back tasks, one long task containing others), plan building (the time budget, priority order, exact fit, zero minutes, completed and not-yet-due tasks), and input validation. I also tested the empty cases: a pet with no tasks and an owner with no pets.

These mattered because the scheduler's output looks plausible even when it is wrong, so I could not trust it by eye. The edge-case tests found two real bugs I had not noticed: the time `"8:60"` was accepted as valid, and completing an already-completed repeating task created a duplicate next task.

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

I am fairly confident, about 4 out of 5. The scheduling logic is well covered and all 56 tests pass. I am less sure about the parts the tests do not reach: the Streamlit app is only checked by hand, and the greedy fit does not guarantee the best use of the available time.

With more time I would test: a task that runs past midnight (the scheduler does not define what should happen), two pets with the same name (the app blocks it, but `Owner.add_pet` does not), overdue tasks that were never completed piling up in each day's plan, and the UI through Streamlit's test runner.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

The plan explains itself. Every scheduled task has a reason, every skipped task says why it did not fit, and conflicts are flagged with a suggestion for fixing them. I am also glad the tests caught real bugs and that the `Scheduler` reads every pet's tasks through one `Owner` method, which kept the multi-pet behavior simple.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

I would make the scheduler smarter about fitting tasks (the greedy fit can waste time) and let it move flexible tasks out of the way instead of only pushing the later task back. I would also add more flexible repeats (specific weekdays), handle overdue tasks, use the owner's `preferences`, save data between sessions (it is lost when the app restarts), and add tests for the Streamlit UI.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

Design first, then verify. A clear picture of each class's job (the UML) let the AI build quickly without the pieces drifting apart, and running the code and tests caught mistakes that sounded right when described. With a powerful AI tool the human's job shifts toward making the decisions and checking the results.
