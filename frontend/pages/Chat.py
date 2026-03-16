import requests
import streamlit as st

# frontend/pages/Chat.py — add at the top
import extra_streamlit_components as stx
cookie_manager = stx.CookieManager()
user_id = cookie_manager.get("mindful_user_id")

# initialize memory
if "memory" not in st.session_state:
    st.session_state.memory = []

# render conversation history (point 2 + 4 — display before input)
for message in st.session_state.memory:
    with st.chat_message(message["role"]):
        if message["role"] == "assistant":
            # point 3 — parse answer and sources
            if "**Sources Used:**" in message["content"]:
                answer_part, sources_part = message["content"].split("**Sources Used:**", 1)
                answer_part = answer_part.replace("**Answer:**", "").strip()
                st.markdown(answer_part)
                st.markdown("---")
                st.caption("**Sources Used:**" + sources_part)
            else:
                st.markdown(message["content"])
        else:
            st.markdown(message["content"])

# input at the bottom
user_input = st.chat_input("Ask Mindful anything...")

if user_input:
    response = requests.post("http://127.0.0.1:8000/mindful/rag", json={
        "query": user_input,
        "memory": st.session_state.memory
    })
    data = response.json()

    st.session_state.memory.append({"role": "user", "content": user_input})
    st.session_state.memory.append({"role": "assistant", "content": data["answer"]})

    st.rerun()