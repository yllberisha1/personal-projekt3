from __future__ import annotations

from datetime import date, timedelta
from math import ceil

import pandas as pd
import streamlit as st

from api_client import APIClient


def render(client: APIClient) -> None:
    if not st.session_state.authenticated:
        st.warning("Please log in first.")
        return

    st.title("Workouts")

    weekly_ok, weekly_data = client.get("/workouts/weekly-calories")
    if weekly_ok:
        st.metric("Total Weekly Calories Burned", weekly_data.get("weekly_calories_burned", 0))

    with st.expander("Add Workout", expanded=True):
        with st.form("add_workout_form"):
            workout_name = st.text_input("Workout Name")
            duration_minutes = st.number_input("Duration (minutes)", min_value=1, max_value=600, value=30)
            calories_burned = st.number_input("Calories Burned", min_value=0, max_value=5000, value=200)
            workout_date = st.date_input("Date", value=date.today())
            submitted = st.form_submit_button("Add Workout", use_container_width=True)

        if submitted:
            if not workout_name.strip():
                st.error("Workout name is required.")
            else:
                payload = {
                    "workout_name": workout_name.strip(),
                    "duration_minutes": int(duration_minutes),
                    "calories_burned": int(calories_burned),
                    "date": workout_date.isoformat(),
                }
                ok, data = client.post("/workouts", payload)
                if ok:
                    st.success("Workout added successfully.")
                    st.rerun()
                else:
                    st.error(data.get("detail", "Could not add workout."))

    st.subheader("Workout History")
    filter_col1, filter_col2, filter_col3 = st.columns(3)

    start_date = filter_col1.date_input("Start Date", value=date.today() - timedelta(days=30), key="workout_start")
    end_date = filter_col2.date_input("End Date", value=date.today(), key="workout_end")
    search_text = filter_col3.text_input("Search by Name", placeholder="e.g. Running")

    params = {"start_date": start_date.isoformat(), "end_date": end_date.isoformat()}
    ok, workouts_data = client.get("/workouts", params=params)

    if not ok:
        st.error(workouts_data.get("detail", "Could not load workouts."))
        return

    if search_text:
        workouts_data = [
            row for row in workouts_data if search_text.lower() in row["workout_name"].lower()
        ]

    if not workouts_data:
        st.info("No workouts found for the selected filters.")
        return

    workout_df = pd.DataFrame(workouts_data)
    workout_df["date"] = pd.to_datetime(workout_df["date"])

    st.subheader("Calories Burned Trend")
    calories_by_date = workout_df.groupby("date", as_index=True)["calories_burned"].sum().sort_index()
    st.line_chart(calories_by_date)

    total_rows = len(workouts_data)
    page_size_col, page_col = st.columns(2)
    page_size = page_size_col.selectbox("Rows per page", [5, 10, 20], index=1, key="workout_page_size")
    total_pages = max(1, ceil(total_rows / page_size))

    if "workout_page" not in st.session_state:
        st.session_state.workout_page = 1
    if st.session_state.workout_page > total_pages:
        st.session_state.workout_page = total_pages

    current_page = int(
        page_col.number_input(
            "Page",
            min_value=1,
            max_value=total_pages,
            value=int(st.session_state.workout_page),
            step=1,
            key="workout_page",
        )
    )

    start_idx = (current_page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_workouts = workouts_data[start_idx:end_idx]
    st.caption(
        f"Showing {start_idx + 1}-{min(end_idx, total_rows)} of {total_rows} workout records."
    )
    st.dataframe(pd.DataFrame(paginated_workouts), use_container_width=True)

    csv_data = workout_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Export Workout History (CSV)",
        data=csv_data,
        file_name="workout_history.csv",
        mime="text/csv",
    )

    st.subheader("Edit / Delete Workouts")
    for workout in paginated_workouts:
        workout_id = workout["id"]
        label = f"{workout['date']} | {workout['workout_name']} ({workout['calories_burned']} kcal)"
        with st.expander(label):
            with st.form(f"edit_workout_{workout_id}"):
                edit_name = st.text_input("Workout Name", value=workout["workout_name"], key=f"name_{workout_id}")
                edit_duration = st.number_input(
                    "Duration (minutes)",
                    min_value=1,
                    max_value=600,
                    value=int(workout["duration_minutes"]),
                    key=f"duration_{workout_id}",
                )
                edit_calories = st.number_input(
                    "Calories Burned",
                    min_value=0,
                    max_value=5000,
                    value=int(workout["calories_burned"]),
                    key=f"calories_{workout_id}",
                )
                edit_date = st.date_input(
                    "Date",
                    value=date.fromisoformat(workout["date"]),
                    key=f"date_{workout_id}",
                )
                save_submitted = st.form_submit_button("Save Changes")

            if save_submitted:
                if not edit_name.strip():
                    st.error("Workout name is required.")
                else:
                    payload = {
                        "workout_name": edit_name.strip(),
                        "duration_minutes": int(edit_duration),
                        "calories_burned": int(edit_calories),
                        "date": edit_date.isoformat(),
                    }
                    update_ok, update_data = client.put(f"/workouts/{workout_id}", payload)
                    if update_ok:
                        st.success("Workout updated.")
                        st.rerun()
                    else:
                        st.error(update_data.get("detail", "Update failed."))

            if st.button("Delete Workout", key=f"delete_workout_{workout_id}"):
                delete_ok, delete_data = client.delete(f"/workouts/{workout_id}")
                if delete_ok:
                    st.success("Workout deleted.")
                    st.rerun()
                else:
                    st.error(delete_data.get("detail", "Delete failed."))
