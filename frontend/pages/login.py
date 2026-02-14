from __future__ import annotations

import streamlit as st

from api_client import APIClient


def render(client: APIClient) -> None:
    st.title("Login / Register")

    if st.session_state.authenticated:
        st.success(f"You are logged in as {st.session_state.username}.")
        st.info("Use the sidebar to navigate to Dashboard, Workouts, Nutrition, and Progress.")
        if st.button("Go to Dashboard", use_container_width=True):
            st.session_state.current_page = "Dashboard"
            st.rerun()
        return

    login_tab, register_tab = st.tabs(["Login", "Register"])

    with register_tab:
        with st.form("register_form"):
            username = st.text_input("Username")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            register_submitted = st.form_submit_button("Create Account", use_container_width=True)

        if register_submitted:
            if password != confirm_password:
                st.error("Passwords do not match.")
            elif not username.strip() or not email.strip():
                st.error("Username and email are required.")
            else:
                ok, data = client.post(
                    "/register",
                    {
                        "username": username.strip(),
                        "email": email.strip(),
                        "password": password,
                    },
                )
                if ok:
                    st.success("Registration successful. You can now log in.")
                else:
                    st.error(data.get("detail", "Registration failed."))

    with login_tab:
        with st.form("login_form"):
            username_or_email = st.text_input("Username or Email")
            password = st.text_input("Password", type="password")
            login_submitted = st.form_submit_button("Login", use_container_width=True)

        if login_submitted:
            ok, data = client.post(
                "/login",
                {
                    "username_or_email": username_or_email.strip(),
                    "password": password,
                },
            )
            if ok:
                st.session_state.authenticated = True
                st.session_state.token = data["token"]
                st.session_state.username = data["username"]
                st.session_state.user_id = data["user_id"]
                st.session_state.current_page = "Dashboard"
                st.success("Login successful.")
                st.rerun()
            else:
                st.error(data.get("detail", "Login failed."))
