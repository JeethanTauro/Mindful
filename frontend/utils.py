import uuid
from datetime import datetime

import requests
import streamlit as st
from streamlit_cookies_manager import EncryptedCookieManager

API_BASE = "http://127.0.0.1:8000"
COOKIE_PASSWORD = "mindful_secret_key"
READ_THRESHOLD_SECONDS = 45  # time spent on article before it counts as a read

def get_cookies():
    # initialise cookie manager — call this at the top of every page
    cookies = EncryptedCookieManager(prefix="mindful_", password=COOKIE_PASSWORD)
    return cookies

def setup_user(cookies):
    # get or create user_id from cookie
    user_id = cookies.get("user_id")
    if not user_id:
        user_id = str(uuid.uuid4())
        cookies["user_id"] = user_id
        cookies.save()

    # generate session_id once per streamlit session — not per rerender
    if "session_id" not in st.session_state:
        st.session_state["session_id"] = str(uuid.uuid4())

    # always upsert user into db on page load — handles both new and returning users
    try:
        requests.post(f"{API_BASE}/mindful/users", json={"user_id": user_id})
    except Exception as e:
        st.warning(f"Could not register user: {e}")

    return user_id, st.session_state["session_id"]


def fire_event(user_id, session_id, article_id, event_type, source):
    # fire and forget — streamlit doesnt wait for this to complete
    try:
        requests.post(f"{API_BASE}/mindful/events", json={
            "user_id": user_id,
            "article_id": article_id,
            "event_type": event_type,
            "session_id": session_id,
            "source": source
        })
    except Exception as e:
        # silently fail — event loss is acceptable, dont break the ui
        print(f"Event fire failed: {e}")


def fetch_feed(user_id):
    # fetch personalised or global feed from backend
    try:
        response = requests.get(f"{API_BASE}/mindful/recommendation", params={"user_id": user_id})
        return response.json()
    except Exception as e:
        st.error(f"Could not fetch feed: {e}")
        return []


def record_article_open(article_id):
    # store the time when user opened an article — used later to determine read vs bounce
    st.session_state["article_opened_at"] = datetime.now()
    st.session_state["article_opened_id"] = article_id


def resolve_read_or_bounce(user_id, session_id):
    # called when user navigates back to feed
    opened_at = st.session_state.get("article_opened_at")
    article_id = st.session_state.get("article_opened_id")

    if not opened_at or not article_id:
        return  # no open event recorded, nothing to resolve

    elapsed = (datetime.now() - opened_at).total_seconds()

    if elapsed >= READ_THRESHOLD_SECONDS:
        fire_event(user_id, session_id, article_id, "article_read", "feed")
    else:
        fire_event(user_id, session_id, article_id, "article_bounce", "feed")

    # clear so it doesnt fire again on next rerender
    del st.session_state["article_opened_at"]
    del st.session_state["article_opened_id"]