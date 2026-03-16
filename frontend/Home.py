import uuid
from datetime import datetime, timedelta

import streamlit as st
import extra_streamlit_components as stx
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from etl.warehouse import con

st.set_page_config(page_title="Mindful", page_icon="🧠", layout="wide")

# ── UUID cookie management ──────────────────────────────────────────────────

cookie_manager = stx.CookieManager()

def get_or_create_uuid():
    user_id = cookie_manager.get("mindful_user_id")
    if not user_id:
        user_id = str(uuid.uuid4())
        cookie_manager.set(
            "mindful_user_id",
            user_id,
            expires_at=datetime.now() + timedelta(days=365)
        )
    return user_id

user_id = get_or_create_uuid()

# ── Fetch articles from DuckDB ───────────────────────────────────────────────

@st.cache_data(ttl=300)
def fetch_articles(limit=30):
    rows = con.execute("""
        SELECT id, title, author, source, word_count, reading_time, 
               published_at, content, scraped_at
        FROM articles_warehouse
        ORDER BY scraped_at DESC
        LIMIT ?
    """, [limit]).fetchdf()
    return rows

df = fetch_articles()

# ── Header ───────────────────────────────────────────────────────────────────

st.markdown("""
    <h1 style='text-align: center; font-size: 3rem; margin-bottom: 0;'>🧠 Mindful</h1>
    <p style='text-align: center; color: gray; font-size: 1.1rem; margin-top: 0;'>
        Your intelligent content feed
    </p>
    <hr/>
""", unsafe_allow_html=True)

# ── Article cards ────────────────────────────────────────────────────────────

COLS = 3

def render_card(article):
    preview = article["content"][:200].strip() + "..." if article["content"] else ""
    source_tag = article["source"] or "unknown"
    reading_time = f"{article['reading_time']} min read" if article.get("reading_time") else ""

    st.markdown(f"""
        <div style="
            border: 1px solid #2e2e2e;
            border-radius: 12px;
            padding: 1.2rem;
            height: 260px;
            overflow: hidden;
            background-color: #1a1a1a;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            margin-bottom: 1rem;
        ">
            <div>
                <div style="display:flex; gap:8px; margin-bottom:8px; flex-wrap:wrap;">
                    <span style="background:#2a2a2a; color:#aaa; padding:2px 10px; 
                                 border-radius:20px; font-size:0.72rem;">{source_tag}</span>
                </div>
                <p style="font-size:1rem; font-weight:600; margin:0 0 8px 0; 
                          line-height:1.4; color:#f0f0f0;">{article['title']}</p>
                <p style="font-size:0.82rem; color:#888; margin:0; line-height:1.5;">
                    {preview}
                </p>
            </div>
            <div style="font-size:0.75rem; color:#555; margin-top:8px;">
                {reading_time}
            </div>
        </div>
    """, unsafe_allow_html=True)

    if st.button("Read →", key=f"read_{article['id']}"):
        st.session_state["selected_article"] = article.to_dict()
        st.rerun()

# ── Article detail view ──────────────────────────────────────────────────────

if "selected_article" in st.session_state:
    article = st.session_state["selected_article"]

    if st.button("← Back to Feed"):
        del st.session_state["selected_article"]
        st.rerun()

    reading_time = f"{article['reading_time']} min read" if article.get("reading_time") else ""
    author = article.get("author") or "Unknown"

    st.markdown(f"## {article['title']}")
    st.markdown(f"""
        <p style='color:gray; font-size:0.85rem;'>
            {author} · {article['source']} · {reading_time}
        </p>
        <hr/>
    """, unsafe_allow_html=True)
    st.write(article["content"])

# ── Feed grid ────────────────────────────────────────────────────────────────

else:
    rows = [df.iloc[i:i+COLS] for i in range(0, len(df), COLS)]
    for row in rows:
        cols = st.columns(COLS)
        for col, (_, article) in zip(cols, row.iterrows()):
            with col:
                render_card(article)