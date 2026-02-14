from __future__ import annotations

import pandas as pd
import streamlit as st

from api_client import APIClient


def render(client: APIClient) -> None:
    if not st.session_state.authenticated:
        st.warning("Please log in first.")
        return

    ok, dashboard_data = client.get("/dashboard")
    if not ok:
        st.error(dashboard_data.get("detail", "Could not load dashboard."))
        return

    st.title("Dashboard")
    st.write(f"Welcome back, **{dashboard_data['username']}**")

    metric_col1, metric_col2, metric_col3 = st.columns(3)
    metric_col1.metric("Total Workouts", dashboard_data["total_workouts"])
    metric_col2.metric("Calories Burned", dashboard_data["total_calories_burned"])
    metric_col3.metric("Calories Consumed", dashboard_data["total_calories_consumed"])

    st.subheader("Current BMI")
    bmi_col1, bmi_col2 = st.columns(2)
    height_cm = bmi_col1.number_input("Height (cm)", min_value=50.0, max_value=250.0, value=170.0, step=0.5)
    weight_kg = bmi_col2.number_input("Weight (kg)", min_value=20.0, max_value=350.0, value=70.0, step=0.1)

    bmi = weight_kg / ((height_cm / 100) ** 2)
    category = "Normal"
    if bmi < 18.5:
        category = "Underweight"
    elif bmi >= 30:
        category = "Obese"
    elif bmi >= 25:
        category = "Overweight"

    st.metric("BMI", f"{bmi:.2f}", category)

    workouts_ok, workouts_data = client.get("/workouts")
    meals_ok, meals_data = client.get("/meals")

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("Calories Burned by Date")
        if workouts_ok and workouts_data:
            workout_df = pd.DataFrame(workouts_data)
            workout_df["date"] = pd.to_datetime(workout_df["date"])
            burned_by_date = workout_df.groupby("date", as_index=True)["calories_burned"].sum().sort_index()
            st.bar_chart(burned_by_date)
        else:
            st.info("No workout data yet.")

    with chart_col2:
        st.subheader("Calories Consumed by Date")
        if meals_ok and meals_data:
            meal_df = pd.DataFrame(meals_data)
            meal_df["date"] = pd.to_datetime(meal_df["date"])
            consumed_by_date = meal_df.groupby("date", as_index=True)["calories"].sum().sort_index()
            st.line_chart(consumed_by_date)
        else:
            st.info("No nutrition data yet.")

    if st.button("Logout from Dashboard"):
        client.post("/logout")
        st.session_state.authenticated = False
        st.session_state.token = ""
        st.session_state.username = ""
        st.session_state.user_id = None
        st.session_state.current_page = "Login / Register"
        st.rerun()
