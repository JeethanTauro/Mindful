import requests
import streamlit as st

# frontend/pages/Chat.py — add at the top
from streamlit_cookies_manager import EncryptedCookieManager

cookies = EncryptedCookieManager(prefix="mindful_", password="mindful_secret_key")
if not cookies.ready():
    st.stop()

user_id = cookies.get("user_id")

# initialize memory
if "memory" not in st.session_state:
    st.session_state.memory = []

# render conversation history (point 2 + 4 — display before input)
for message in st.session_state.memory:
    with st.chat_message(message["role"]):
        if message["role"] == "assistant":
            # strip the Sources Used block from answer — we render sources ourselves
            answer = message["content"]
            if "**Sources Used:**" in answer:
                answer = answer.split("**Sources Used:**")[0].replace("**Answer:**", "").strip()
            st.markdown(answer)

            # render sources as clickable links
            sources = message.get("sources", [])
            if sources:
                st.markdown("---")
                st.caption("**Sources:**")
                for s in sources:
                    article_id = s.get("article_id")
                    title = s.get("title", "Unknown")
                    source_name = s.get("source", "")
                    if article_id:
                        st.markdown(f"→ [{title}](/?article_id={article_id}) — *{source_name}*")
                    else:
                        st.markdown(f"→ {title} — *{source_name}*")
        else:
            st.markdown(message["content"])

# input at the bottom
user_input = st.chat_input("Ask Mindful anything...")

if user_input:
    clean_memory = [{"role": m["role"], "content": m["content"]} for m in st.session_state.memory]

    response = requests.post("http://127.0.0.1:8000/mindful/rag", json={
        "query": user_input,
        "memory": clean_memory
    })
    data = response.json()

    st.session_state.memory.append({"role": "user", "content": user_input})
    st.session_state.memory.append({"role": "assistant", "content": data["answer"], "sources": data.get("sources", [])})

    st.rerun()