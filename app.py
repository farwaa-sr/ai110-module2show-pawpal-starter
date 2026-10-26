import datetime

import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task, format_time

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

# Streamlit reruns this whole script on every interaction, so keep the Owner in
# session_state and only create it the first time (when the key is missing).
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan")
owner: Owner = st.session_state.owner

st.title("🐾 PawPal+")
st.markdown(
    "A pet care planner: add your pets and their care tasks, then generate a "
    "daily schedule that fits your available time."
)

with st.expander("Scenario", expanded=False):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.
"""
    )

st.divider()

# --- Owner -> Owner.name / Owner.set_availability() ---------------------------
st.subheader("Owner")
col1, col2 = st.columns(2)
with col1:
    owner.name = st.text_input("Owner name", value=owner.name)
with col2:
    minutes = st.number_input(
        "Minutes available per day",
        min_value=0,
        max_value=1440,
        value=owner.available_minutes_per_day,
        step=10,
    )
    owner.set_availability(int(minutes))

# --- Add a pet -> Owner.add_pet(Pet(...)) -------------------------------------
st.subheader("Pets")
with st.form("add_pet_form", clear_on_submit=True):
    c1, c2, c3 = st.columns(3)
    with c1:
        pet_name = st.text_input("Pet name", key="pet_name")
    with c2:
        species = st.selectbox("Species", ["dog", "cat", "other"], key="species")
    with c3:
        age = st.number_input("Age", min_value=0, max_value=40, value=1, key="age")
    add_pet_clicked = st.form_submit_button("Add pet")

if add_pet_clicked:
    name = pet_name.strip()
    if not name:
        st.error("Please enter a pet name.")
    elif any(p.name.lower() == name.lower() for p in owner.pets):
        st.error(f"You already have a pet named {name}.")
    else:
        owner.add_pet(Pet(name=name, species=species, age=int(age)))
        st.success(f"Added {name}!")

if owner.pets:
    st.table(
        [{"Name": p.name, "Species": p.species, "Age": p.age, "Tasks": len(p.tasks)} for p in owner.pets]
    )
else:
    st.info("No pets yet. Add one above.")

# --- Add a task -> Pet.add_task(Task(...)) ------------------------------------
st.subheader("Tasks")
if not owner.pets:
    st.caption("Add a pet first, then you can give it tasks.")
else:
    with st.form("add_task_form", clear_on_submit=True):
        target = st.selectbox("For which pet?", [p.name for p in owner.pets], key="task_pet")
        c1, c2, c3 = st.columns(3)
        with c1:
            task_title = st.text_input("Task title", key="task_title")
        with c2:
            duration = st.number_input(
                "Duration (minutes)", min_value=1, max_value=240, value=20, key="task_duration"
            )
        with c3:
            priority = st.selectbox("Priority", ["low", "medium", "high"], index=2, key="task_priority")
        c4, c5 = st.columns(2)
        with c4:
            use_time = st.checkbox("Set a preferred time", key="task_use_time")
            preferred = st.time_input("Preferred time", value=datetime.time(8, 0), key="task_time")
        with c5:
            frequency = st.selectbox("Frequency", ["once", "daily", "weekly"], key="task_frequency")
        add_task_clicked = st.form_submit_button("Add task")

    if add_task_clicked:
        if not task_title.strip():
            st.error("Please enter a task title.")
        else:
            pet = next(p for p in owner.pets if p.name == target)
            try:
                pet.add_task(
                    Task(
                        title=task_title.strip(),
                        duration_minutes=int(duration),
                        priority=priority,
                        time=preferred.strftime("%H:%M") if use_time else None,
                        frequency=frequency,
                    )
                )
                st.success(f"Added '{task_title.strip()}' for {pet.name}.")
            except ValueError as err:
                st.error(str(err))

all_tasks = owner.get_all_tasks()

# --- Mark a task done -> Pet.complete_task() (repeating tasks spawn the next one) ---
pending = owner.filter_tasks(completed=False)
if pending:
    with st.form("complete_task_form"):
        picked = st.selectbox(
            "Mark a task as done",
            range(len(pending)),
            format_func=lambda i: f"{pending[i].title} ({pending[i].pet_name}, due {pending[i].due_date})",
            key="complete_pick",
        )
        complete_clicked = st.form_submit_button("Mark done")
    if complete_clicked:
        task = pending[picked]
        pet = next(p for p in owner.pets if p.name == task.pet_name)
        upcoming = pet.complete_task(task)
        if upcoming:
            st.success(f"Done! Next '{task.title}' is due {upcoming.due_date}.")
        else:
            st.success(f"Done! '{task.title}' is complete.")

# --- View tasks -> Owner.filter_tasks() + Scheduler.sort_by_time() ------------
if all_tasks:
    f1, f2 = st.columns(2)
    with f1:
        pet_filter = st.selectbox("Show pet", ["All pets"] + [p.name for p in owner.pets], key="pet_filter")
    with f2:
        status_filter = st.selectbox("Show status", ["All", "To do", "Done"], key="status_filter")
    shown = owner.filter_tasks(
        pet_name=None if pet_filter == "All pets" else pet_filter,
        completed={"All": None, "To do": False, "Done": True}[status_filter],
    )
    if shown:
        st.table(
            [
                {
                    "Pet": t.pet_name,
                    "Task": t.title,
                    "Due": str(t.due_date),
                    "Time": t.time or "-",
                    "Minutes": t.duration_minutes,
                    "Priority": t.priority,
                    "Frequency": t.frequency,
                    "Done": "yes" if t.completed else "no",
                }
                for t in Scheduler.sort_by_time(shown)
            ]
        )
    else:
        st.info("No tasks match those filters.")
else:
    st.info("No tasks yet.")

st.divider()

# --- Generate schedule -> Scheduler(owner).generate_plan() --------------------
st.subheader("Build Schedule")
if st.button("Generate schedule"):
    if not all_tasks:
        st.warning("Add at least one task first.")
    else:
        scheduler = Scheduler(owner)
        plan = scheduler.generate_plan()
        if plan:
            st.success(f"Today's plan for {owner.name} ({owner.available_minutes_per_day} min available)")
            st.table(
                [
                    {
                        "Time": f"{format_time(i.start_minute)}-{format_time(i.end_minute)}",
                        "Pet": i.task.pet_name,
                        "Task": i.task.title,
                        "Priority": i.task.priority,
                        "Why": i.reason,
                    }
                    for i in plan
                ]
            )
        else:
            st.warning("Nothing fits in the time available.")
        for warning in scheduler.conflicts:
            st.warning(warning + ". The later task was pushed back in the plan.")
        if scheduler.skipped:
            st.markdown("**Not scheduled**")
            for task, why in scheduler.skipped:
                st.write(f"- {task.title} ({task.pet_name}): {why}")
