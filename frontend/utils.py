import uuid
from datetime import datetime

import requests
import streamlit as st
from streamlit_cookies_manager import EncryptedCookieManager

API_BASE = "http://127.0.0.1:8000"
COOKIE_PASSWORD = "mindful_secret_key"
READ_THRESHOLD_SECONDS = 45
MAX_MEMORY = 10  # max conversation turns kept — prevents token explosion


def get_cookies():
    cookies = EncryptedCookieManager(prefix="mindful_", password=COOKIE_PASSWORD)
    return cookies


def setup_user(cookies):
    user_id = cookies.get("user_id")
    if not user_id:
        user_id = str(uuid.uuid4())
        cookies["user_id"] = user_id
        cookies.save()

    if "session_id" not in st.session_state:
        st.session_state["session_id"] = str(uuid.uuid4())

    try:
        requests.post(f"{API_BASE}/mindful/users", json={"user_id": user_id}, timeout=5)
    except Exception as e:
        st.warning(f"Could not register user: {e}")

    return user_id, st.session_state["session_id"]


def fire_event(user_id, session_id, article_id, event_type, source):
    try:
        requests.post(f"{API_BASE}/mindful/events", json={
            "user_id": user_id,
            "article_id": article_id,
            "event_type": event_type,
            "session_id": session_id,
            "source": source
        }, timeout=5)
    except Exception as e:
        print(f"Event fire failed: {e}")


def fetch_feed(user_id):
    try:
        response = requests.get(
            f"{API_BASE}/mindful/recommendation",
            params={"user_id": user_id},
            timeout=10
        )
        if response.status_code != 200:
            st.error(f"Feed error: status {response.status_code}")
            return []
        data = response.json()
        if isinstance(data, dict):
            st.error(f"Feed error: {data}")
            return []
        return data
    except Exception as e:
        st.error(f"Could not fetch feed: {e}")
        return []


def record_article_open(article_id):
    st.session_state["article_opened_at"] = datetime.now()
    st.session_state["article_opened_id"] = article_id


def resolve_read_or_bounce(user_id, session_id):
    opened_at = st.session_state.get("article_opened_at")
    article_id = st.session_state.get("article_opened_id")

    if not opened_at or not article_id:
        return

    elapsed = (datetime.now() - opened_at).total_seconds()

    if elapsed >= READ_THRESHOLD_SECONDS:
        fire_event(user_id, session_id, article_id, "article_read", "feed")
    else:
        fire_event(user_id, session_id, article_id, "article_bounce", "feed")

    del st.session_state["article_opened_at"]
    del st.session_state["article_opened_id"]