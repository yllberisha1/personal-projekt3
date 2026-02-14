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

    st.title("Progress")

    with st.expander("Add Weight Entry", expanded=True):
        with st.form("add_weight_form"):
            weight_kg = st.number_input("Weight (kg)", min_value=20.0, max_value=500.0, value=70.0, step=0.1)
            entry_date = st.date_input("Date", value=date.today())
            submitted = st.form_submit_button("Add Entry", use_container_width=True)

        if submitted:
            ok, data = client.post(
                "/weights",
                {
                    "weight_kg": float(weight_kg),
                    "date": entry_date.isoformat(),
                },
            )
            if ok:
                st.success("Weight entry saved.")
                st.rerun()
            else:
                st.error(data.get("detail", "Could not save weight entry."))

    filter_col1, filter_col2 = st.columns(2)
    start_date = filter_col1.date_input("Start Date", value=date.today() - timedelta(days=90), key="weight_start")
    end_date = filter_col2.date_input("End Date", value=date.today(), key="weight_end")

    ok, weights_data = client.get(
        "/weights",
        params={"start_date": start_date.isoformat(), "end_date": end_date.isoformat()},
    )
    if not ok:
        st.error(weights_data.get("detail", "Could not load weight history."))
        return

    if weights_data:
        weights_df = pd.DataFrame(weights_data)
        weights_df["date"] = pd.to_datetime(weights_df["date"])
        weights_df = weights_df.sort_values("date")

        st.subheader("Weight History")
        st.line_chart(weights_df.set_index("date")["weight_kg"])

        height_cm = st.number_input(
            "Height for BMI Trend (cm)",
            min_value=50.0,
            max_value=250.0,
            value=170.0,
            step=0.5,
        )
        bmi_df = weights_df.copy()
        bmi_df["bmi"] = bmi_df["weight_kg"] / ((height_cm / 100) ** 2)

        st.subheader("BMI Trend")
        st.line_chart(bmi_df.set_index("date")["bmi"])

        st.subheader("Weight Entries")
        total_rows = len(weights_data)
        page_size_col, page_col = st.columns(2)
        page_size = page_size_col.selectbox("Rows per page", [5, 10, 20], index=1, key="weight_page_size")
        total_pages = max(1, ceil(total_rows / page_size))

        if "weight_page" not in st.session_state:
            st.session_state.weight_page = 1
        if st.session_state.weight_page > total_pages:
            st.session_state.weight_page = total_pages

        current_page = int(
            page_col.number_input(
                "Page",
                min_value=1,
                max_value=total_pages,
                value=int(st.session_state.weight_page),
                step=1,
                key="weight_page",
            )
        )

        start_idx = (current_page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_weights = weights_data[start_idx:end_idx]
        st.caption(
            f"Showing {start_idx + 1}-{min(end_idx, total_rows)} of {total_rows} weight entries."
        )
        st.dataframe(pd.DataFrame(paginated_weights), use_container_width=True)

        for row in paginated_weights:
            entry_id = row["id"]
            with st.expander(f"{row['date']} | {row['weight_kg']} kg"):
                with st.form(f"edit_weight_{entry_id}"):
                    edit_weight = st.number_input(
                        "Weight (kg)",
                        min_value=20.0,
                        max_value=500.0,
                        value=float(row["weight_kg"]),
                        step=0.1,
                        key=f"weight_value_{entry_id}",
                    )
                    edit_date = st.date_input(
                        "Date",
                        value=date.fromisoformat(row["date"]),
                        key=f"weight_date_{entry_id}",
                    )
                    save_submitted = st.form_submit_button("Save Changes")

                if save_submitted:
                    update_ok, update_data = client.put(
                        f"/weights/{entry_id}",
                        {
                            "weight_kg": float(edit_weight),
                            "date": edit_date.isoformat(),
                        },
                    )
                    if update_ok:
                        st.success("Weight entry updated.")
                        st.rerun()
                    else:
                        st.error(update_data.get("detail", "Update failed."))

                if st.button("Delete Entry", key=f"delete_weight_{entry_id}"):
                    delete_ok, delete_data = client.delete(f"/weights/{entry_id}")
                    if delete_ok:
                        st.success("Weight entry deleted.")
                        st.rerun()
                    else:
                        st.error(delete_data.get("detail", "Delete failed."))
    else:
        st.info("No weight entries in the selected date range.")

    st.subheader("Workout Frequency per Week")
    freq_ok, freq_data = client.get("/workouts/frequency")
    if freq_ok and freq_data:
        freq_df = pd.DataFrame(freq_data)
        st.bar_chart(freq_df.set_index("week")["workout_count"])
    else:
        st.info("No workout frequency data yet.")
