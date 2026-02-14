from __future__ import annotations

import streamlit as st

from api_client import APIClient
from pages import dashboard, login, nutrition, progress, workouts


def initialize_session_state() -> None:
    defaults = {
        "authenticated": False,
        "token": "",
        "username": "",
        "user_id": None,
        "api_base_url": "http://127.0.0.1:8000",
        "dark_mode": False,
        "current_page": "Login / Register",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def clear_auth_state() -> None:
    st.session_state.authenticated = False
    st.session_state.token = ""
    st.session_state.username = ""
    st.session_state.user_id = None
    st.session_state.current_page = "Login / Register"


def apply_theme() -> None:
    if st.session_state.dark_mode:
        st.markdown(
            """
            <style>
            .stApp { background: linear-gradient(180deg, #10151c 0%, #1a222e 100%); color: #f6f7fb; }
            [data-testid="stSidebar"] { background-color: #111927; }
            </style>
            """,
            unsafe_allow_html=True,
        )


def main() -> None:
    st.set_page_config(page_title="Fitness Web App", page_icon=":weight_lifter:", layout="wide")
    initialize_session_state()

    st.sidebar.title("Fitness App")
    st.session_state.api_base_url = st.sidebar.text_input(
        "FastAPI Base URL",
        value=st.session_state.api_base_url,
        help="Example: http://127.0.0.1:8000",
    )
    st.session_state.dark_mode = st.sidebar.toggle("Dark Mode", value=st.session_state.dark_mode)
    apply_theme()

    client = APIClient(st.session_state.api_base_url, st.session_state.token)
    health_ok, _ = client.get("/")
    if health_ok:
        st.sidebar.caption("API: Connected")
    else:
        st.sidebar.caption("API: Disconnected")

    if st.session_state.authenticated:
        st.sidebar.success(f"Logged in as {st.session_state.username}")
        nav_options = ["Dashboard", "Workouts", "Nutrition", "Progress", "Login / Register"]
    else:
        nav_options = ["Login / Register"]
        st.session_state.current_page = "Login / Register"

    current_page = st.session_state.current_page
    if current_page not in nav_options:
        current_page = nav_options[0]

    selected_page = st.sidebar.radio(
        "Navigation",
        nav_options,
        index=nav_options.index(current_page),
    )
    st.session_state.current_page = selected_page

    if st.session_state.authenticated and st.sidebar.button("Logout", use_container_width=True):
        client.post("/logout")
        clear_auth_state()
        st.rerun()

    if selected_page == "Login / Register":
        login.render(client)
    elif selected_page == "Dashboard":
        dashboard.render(client)
    elif selected_page == "Workouts":
        workouts.render(client)
    elif selected_page == "Nutrition":
        nutrition.render(client)
    elif selected_page == "Progress":
        progress.render(client)


if __name__ == "__main__":
    main()
