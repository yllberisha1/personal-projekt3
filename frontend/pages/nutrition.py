from __future__ import annotations

from datetime import date, timedelta
from math import ceil

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from api_client import APIClient


def render(client: APIClient) -> None:
    if not st.session_state.authenticated:
        st.warning("Please log in first.")
        return

    st.title("Nutrition")

    with st.expander("Add Meal", expanded=True):
        with st.form("add_meal_form"):
            meal_name = st.text_input("Meal Name")
            calories = st.number_input("Calories", min_value=0, max_value=10000, value=400)
            protein = st.number_input("Protein (g)", min_value=0.0, max_value=1000.0, value=30.0)
            carbs = st.number_input("Carbs (g)", min_value=0.0, max_value=1000.0, value=40.0)
            fats = st.number_input("Fats (g)", min_value=0.0, max_value=1000.0, value=15.0)
            meal_date = st.date_input("Date", value=date.today())
            submitted = st.form_submit_button("Add Meal", use_container_width=True)

        if submitted:
            if not meal_name.strip():
                st.error("Meal name is required.")
            else:
                payload = {
                    "meal_name": meal_name.strip(),
                    "calories": int(calories),
                    "protein": float(protein),
                    "carbs": float(carbs),
                    "fats": float(fats),
                    "date": meal_date.isoformat(),
                }
                ok, data = client.post("/meals", payload)
                if ok:
                    st.success("Meal added successfully.")
                    st.rerun()
                else:
                    st.error(data.get("detail", "Could not add meal."))

    st.subheader("Daily Macro Breakdown")
    macro_date = st.date_input("Select Date", value=date.today(), key="macro_date")
    macros_ok, macros_data = client.get("/meals/macros", params={"date": macro_date.isoformat()})

    if macros_ok:
        macro_col1, macro_col2, macro_col3, macro_col4 = st.columns(4)
        macro_col1.metric("Protein (g)", f"{macros_data['total_protein']:.1f}")
        macro_col2.metric("Carbs (g)", f"{macros_data['total_carbs']:.1f}")
        macro_col3.metric("Fats (g)", f"{macros_data['total_fats']:.1f}")
        macro_col4.metric("Calories", macros_data["total_calories"])

        values = [
            macros_data["total_protein"],
            macros_data["total_carbs"],
            macros_data["total_fats"],
        ]

        if sum(values) > 0:
            fig, ax = plt.subplots()
            ax.pie(values, labels=["Protein", "Carbs", "Fats"], autopct="%1.1f%%", startangle=90)
            ax.axis("equal")
            st.pyplot(fig)
        else:
            st.info("No macro data for the selected date.")
    else:
        st.error(macros_data.get("detail", "Could not load macro data."))

    st.subheader("Meal History")
    filter_col1, filter_col2, filter_col3 = st.columns(3)
    start_date = filter_col1.date_input("Start Date", value=date.today() - timedelta(days=30), key="meal_start")
    end_date = filter_col2.date_input("End Date", value=date.today(), key="meal_end")
    search_text = filter_col3.text_input("Search Meals", placeholder="e.g. Oatmeal")

    params = {"start_date": start_date.isoformat(), "end_date": end_date.isoformat()}
    ok, meals_data = client.get("/meals", params=params)

    if not ok:
        st.error(meals_data.get("detail", "Could not load meals."))
        return

    if search_text:
        meals_data = [row for row in meals_data if search_text.lower() in row["meal_name"].lower()]

    if not meals_data:
        st.info("No meals found for the selected filters.")
        return

    meal_df = pd.DataFrame(meals_data)
    meal_df["date"] = pd.to_datetime(meal_df["date"])

    st.subheader("Calories Consumed Trend")
    calories_by_date = meal_df.groupby("date", as_index=True)["calories"].sum().sort_index()
    st.line_chart(calories_by_date)

    total_rows = len(meals_data)
    page_size_col, page_col = st.columns(2)
    page_size = page_size_col.selectbox("Rows per page", [5, 10, 20], index=1, key="meal_page_size")
    total_pages = max(1, ceil(total_rows / page_size))

    if "meal_page" not in st.session_state:
        st.session_state.meal_page = 1
    if st.session_state.meal_page > total_pages:
        st.session_state.meal_page = total_pages

    current_page = int(
        page_col.number_input(
            "Page",
            min_value=1,
            max_value=total_pages,
            value=int(st.session_state.meal_page),
            step=1,
            key="meal_page",
        )
    )

    start_idx = (current_page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_meals = meals_data[start_idx:end_idx]
    st.caption(f"Showing {start_idx + 1}-{min(end_idx, total_rows)} of {total_rows} meal records.")
    st.dataframe(pd.DataFrame(paginated_meals), use_container_width=True)

    st.subheader("Edit / Delete Meals")
    for meal in paginated_meals:
        meal_id = meal["id"]
        label = f"{meal['date']} | {meal['meal_name']} ({meal['calories']} kcal)"
        with st.expander(label):
            with st.form(f"edit_meal_{meal_id}"):
                edit_name = st.text_input("Meal Name", value=meal["meal_name"], key=f"meal_name_{meal_id}")
                edit_calories = st.number_input(
                    "Calories",
                    min_value=0,
                    max_value=10000,
                    value=int(meal["calories"]),
                    key=f"meal_calories_{meal_id}",
                )
                edit_protein = st.number_input(
                    "Protein (g)",
                    min_value=0.0,
                    max_value=1000.0,
                    value=float(meal["protein"]),
                    key=f"meal_protein_{meal_id}",
                )
                edit_carbs = st.number_input(
                    "Carbs (g)",
                    min_value=0.0,
                    max_value=1000.0,
                    value=float(meal["carbs"]),
                    key=f"meal_carbs_{meal_id}",
                )
                edit_fats = st.number_input(
                    "Fats (g)",
                    min_value=0.0,
                    max_value=1000.0,
                    value=float(meal["fats"]),
                    key=f"meal_fats_{meal_id}",
                )
                edit_date = st.date_input(
                    "Date",
                    value=date.fromisoformat(meal["date"]),
                    key=f"meal_date_{meal_id}",
                )
                save_submitted = st.form_submit_button("Save Changes")

            if save_submitted:
                if not edit_name.strip():
                    st.error("Meal name is required.")
                else:
                    payload = {
                        "meal_name": edit_name.strip(),
                        "calories": int(edit_calories),
                        "protein": float(edit_protein),
                        "carbs": float(edit_carbs),
                        "fats": float(edit_fats),
                        "date": edit_date.isoformat(),
                    }
                    update_ok, update_data = client.put(f"/meals/{meal_id}", payload)
                    if update_ok:
                        st.success("Meal updated.")
                        st.rerun()
                    else:
                        st.error(update_data.get("detail", "Update failed."))

            if st.button("Delete Meal", key=f"delete_meal_{meal_id}"):
                delete_ok, delete_data = client.delete(f"/meals/{meal_id}")
                if delete_ok:
                    st.success("Meal deleted.")
                    st.rerun()
                else:
                    st.error(delete_data.get("detail", "Delete failed."))
