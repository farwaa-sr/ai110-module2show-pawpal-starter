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

The full Mermaid class diagram is in [uml_diagram.md](uml_diagram.md).

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

After writing the class skeleton in `pawpal_system.py`, I asked my AI coding assistant to review it for missing relationships and logic bottlenecks. I made these changes based on its feedback:

1. **Added `Task.pet_name`.** `Owner.get_all_tasks()` flattens every pet's tasks into one list, so a task would no longer know which pet it was for. The plan needs that to say things like "Walk for Biscuit".
2. **Added a `ScheduledTask` class** (task, start time, reason) and changed `Scheduler.plan` to hold these instead of bare `Task`s. A plain list of tasks has no times, but the daily plan needs them. Putting the reason on each entry also replaced the separate `explanations` dict, which would have had to be kept in sync with the plan.
3. **Added `Scheduler.skipped`** (tasks that didn't fit, with the reason). `explain_plan()` has to explain what was left out, and nothing in the original design recorded that.
4. **Added `PRIORITY_ORDER`.** Priority is a string, and sorting `"high"`/`"medium"`/`"low"` alphabetically gives the wrong order. A mapping gives the scheduler a reliable sort key.

Issues I noted but did not change yet:
- `generate_plan()` must rebuild the plan from scratch each time and skip completed tasks, or the stored plan goes stale when tasks change.
- A greedy "highest priority first" fit can let one long task block several short ones. That is a tradeoff to decide when implementing the scheduler.
- There is no recurrence (daily or weekly tasks) yet, which the README's "Smarter Scheduling" section mentions.
- `Owner.available_minutes_per_day` and `set_availability()` overlap, and nothing validates the value (for example, negative minutes).

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

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

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
