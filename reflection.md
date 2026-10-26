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

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

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
