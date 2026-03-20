import sys
import os

import requests
import streamlit as st

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from frontend.utils import get_cookies, setup_user, fire_event

# ── Cookie + User Setup ───────────────────────────────────────────────────────

cookies = get_cookies()
if not cookies.ready():
    st.stop()

user_id, session_id = setup_user(cookies)

# ── Conversation memory ───────────────────────────────────────────────────────

if "memory" not in st.session_state:
    st.session_state.memory = []

# ── Render conversation history ───────────────────────────────────────────────

for message in st.session_state.memory:
    with st.chat_message(message["role"]):
        if message["role"] == "assistant":
            # strip sources block from answer — rendered separately below
            answer = message["content"]
            if "**Sources Used:**" in answer:
                answer = answer.split("**Sources Used:**")[0].replace("**Answer:**", "").strip()
            st.markdown(answer)

            # render sources as buttons so we can intercept the click and fire events
            sources = message.get("sources", [])
            if sources:
                st.markdown("---")
                st.caption("**Sources:**")
                for s in sources:
                    article_id = s.get("article_id")
                    title = s.get("title", "Unknown")
                    source_name = s.get("source", "")

                    if article_id:
                        # button instead of markdown link — lets us fire event before navigating
                        if st.button(f"→ {title} — {source_name}", key=f"src_{article_id}_{message.get('id','')}"):
                            # fire article_open_from_chatbot event before navigating
                            fire_event(user_id, session_id, article_id, "article_open_from_chatbot", "rag_chatbot")
                            # navigate to article detail on Home.py
                            st.query_params["article_id"] = article_id
                            st.switch_page("Home.py")
                    else:
                        st.markdown(f"→ {title} — *{source_name}*")
        else:
            st.markdown(message["content"])

# ── Chat input ────────────────────────────────────────────────────────────────

user_input = st.chat_input("Ask Mindful anything...")

if user_input:
    # build clean memory without sources metadata — backend only needs role + content
    clean_memory = [{"role": m["role"], "content": m["content"]} for m in st.session_state.memory]

    try:
        response = requests.post("http://127.0.0.1:8000/mindful/rag", json={
            "query": user_input,
            "memory": clean_memory
        })
        data = response.json()
    except Exception as e:
        st.error(f"Could not reach backend: {e}")
        st.stop()

    # attach a unique id to each assistant message — used to key source buttons uniquely
    import uuid
    st.session_state.memory.append({
        "role": "user",
        "content": user_input
    })
    st.session_state.memory.append({
        "id": str(uuid.uuid4()),
        "role": "assistant",
        "content": data.get("answer", ""),
        "sources": data.get("sources", [])
    })

    st.rerun()