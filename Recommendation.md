# Recommendation Engine — Architecture & System Design

---

## What We're Actually Building

Mindful is a content platform. Users come, read articles, interact with content. The recommendation engine's job is to answer one question: **"Given everything I know about this user, what article should they read next?"**

This sounds simple. It isn't. The reason Netflix, YouTube, and Spotify have entire teams dedicated to this problem is because "what a user wants" is not a static thing — it shifts based on mood, time of day, what they just read, what they've been reading over the past month, and what they don't even know they want yet. A good recommendation engine captures all of this.

---

## The Cold Start Problem

Before anything else, you need to understand the hardest problem in recommendation systems — cold start.

**User cold start** — A brand new user has no history. You know nothing about them. What do you recommend? You can't personalize yet because there's nothing to personalize on.

**Item cold start** — A brand new article just got ingested. No one has read it yet. How does it get discovered if the engine only recommends things people have already interacted with?

Everything about the architecture is designed around solving or mitigating cold start. It's not an edge case — every single user starts cold. Your first impression on a new user depends entirely on how well you handle this.

For Mindful the cold start solution is:

For new users — recommend by global popularity within categories. Show what's trending, what's most read, what's highest rated. Not personalized but not random either. As soon as the user reads even one article, you have a signal.

For new articles — they enter the pool immediately. The embedding already exists in ChromaDB from the ETL pipeline. Content-based similarity means new articles get recommended to users whose interest vectors overlap with the article's content — no interaction history required.

---

## The Two Fundamental Approaches

Every recommendation engine is built on one or both of these foundations:

### Collaborative Filtering

"Users who behaved like you also liked these things."

The insight is that human taste clusters. People who read about system design at Netflix also tend to read about distributed databases and microservices. You don't need to understand why — the pattern is enough. If User A and User B have read 80% of the same articles, and User B read something User A hasn't seen yet, that's a strong recommendation signal.

Collaborative filtering requires no understanding of the content at all. It's purely behavioral. This is why Spotify can recommend music in genres it doesn't understand — it just finds users with similar listening patterns.

The weakness is cold start — new users have no behavior, new items have no interactions, the model has nothing to work with.

### Content-Based Filtering

"You liked this article, here are articles with similar content."

The insight is that if you can represent both users and content in the same vector space, similarity becomes a distance calculation. An article about Netflix's CDN architecture and an article about Cloudflare's edge network are close in vector space even if no user has ever read both.

This is where Mindful has a natural advantage — every article is already embedded in ChromaDB. The content representation is already built. Content-based filtering is almost free.

The weakness is the filter bubble — users only get recommendations similar to what they've already seen. Discovery suffers. The engine never surprises you.

### The Hybrid Approach — What Mindful Should Build

Neither approach alone is sufficient. The industry standard is hybrid — use content-based filtering to solve cold start and provide a baseline, use collaborative filtering as you accumulate behavioral data to improve personalization, blend the two signals with weights that shift as data accumulates.

New user → 100% content-based. Read 5 articles → 80% content, 20% collaborative. Read 50 articles → 50/50. Power user with hundreds of interactions → lean collaborative.

---

## User Interest Representation — The Interest Vector

This is the core data structure of the entire system.

Every article has a 384-dimensional embedding vector from `all-MiniLM-L6-v2`. This vector represents the semantic content of the article. The idea is to represent the user in the same 384-dimensional space.

How? The **weighted centroid** approach.

When a user reads an article, you take that article's embedding vector and add it to the user's interest vector with some weight. The weight depends on the strength of the interaction — just reading an article is a weak signal, reading it fully is stronger, saving it is stronger still, explicitly liking it is the strongest signal.

Over time the user's interest vector becomes the weighted average of all the article embeddings they've interacted with. This vector sits in the same space as every article embedding in ChromaDB. Finding recommendations becomes a nearest-neighbor search — find the articles closest to the user's interest vector.

This is elegant because it unifies the user representation and the content representation into one mathematical framework. The same ChromaDB collection that powers the RAG chatbot also powers the recommendation engine.

**Decay** is important here. A user who read Python articles two years ago and JavaScript articles last week is currently interested in JavaScript. Older interactions should contribute less to the interest vector than recent ones. Time-weighted decay — multiply each interaction's contribution by an exponential decay factor based on how old it is — keeps the interest vector fresh and representative of current taste rather than entire lifetime history.

---

## The Events Table — Capturing Behavioral Signals

The interest vector is computed from user events. Every meaningful interaction a user has with content is an event that gets logged.

Events have different weights because they carry different amounts of signal:

**Impression** — the article appeared in the user's feed. Weakest signal, might not even be worth logging individually, but aggregate impression data tells you what the user chose not to click.

**Click / Read** — the user opened the article. Medium signal. They were interested enough to start.

**Read completion** — the user scrolled through the full article. Strong signal. They found it worth finishing. This is hard to fake — you can click accidentally, but reading to the end is intentional.

**Save / Bookmark** — the user explicitly wanted to keep this. Very strong signal.

**Like / Upvote** — explicit positive feedback. Strongest signal.

**Dislike / Skip** — explicit negative feedback. Important negative signal — tells you what to stop recommending.

**Session context** — what did the user read just before this? Temporal context matters. A user on a "deep work" reading session is in a different mental mode than someone casually browsing.

The events table in DuckDB stores all of this with timestamps, session IDs, and the article ID. From this table you compute everything else.

---

## The Recommendation Pipeline — Step by Step

When a user opens Mindful's feed, this is what happens:

**Step 1 — Retrieve user interest vector**

Look up the user's precomputed interest vector from the users table. This is a 384-dimensional vector that represents their taste. It was last updated the previous time they interacted with content.

If the user is new and has no vector — fall back to the global popularity ranking for their detected or selected categories.

**Step 2 — Candidate generation**

Query ChromaDB with the user's interest vector as the query embedding. Get the top 50-100 candidate articles by cosine similarity. This is the same operation as RAG retrieval — nearest neighbor search in vector space.

Why 50-100 candidates? Because you're going to filter and rerank. The retrieval stage optimizes for recall — get everything potentially interesting. Subsequent stages optimize for precision.

**Step 3 — Filtering**

Remove articles the user has already read — no point recommending something they've seen. Remove articles that are too old if freshness matters for the category (news articles older than 3 days are stale; deep analysis articles from 6 months ago are still relevant). Remove articles the user has explicitly disliked.

**Step 4 — Diversity injection**

If all 50 candidates are about Netflix system design, the feed will be boring even if the user likes system design. Cap representation from any single category, source, or author. Ensure the feed has a mix — some directly on-interest content, some adjacent topics that might expand the user's interests, some trending content for discovery.

This is where the filter bubble gets broken deliberately. A small percentage of every feed should be exploratory — content slightly outside the user's established interest vector. This is how taste evolves. Spotify calls this "peripheral listening." Netflix calls it "long-tail discovery."

**Step 5 — Scoring and ranking**

Each candidate article gets a composite score built from multiple signals:

- **Relevance score** — cosine similarity between article embedding and user interest vector. How well does this match what they've read before.
- **Popularity score** — how many total reads, saves, likes has this article gotten globally. Normalized to avoid recency bias toward older viral content.
- **Freshness score** — how recently was this article published. Newer content gets a boost, especially for news categories.
- **Diversity bonus** — if this article is slightly outside the user's comfort zone but high quality, give it a small boost to serve the exploration function.
- **Collaborative signal** — if this article was highly engaged by users with similar interest vectors, boost it.

These signals combine into one final score. The weights on each signal are tunable — this is where you experiment and iterate based on actual engagement metrics.

**Step 6 — Serve top N**

Return the top 10-20 articles sorted by final score. These become the user's feed.

---

## Interest Vector Update — When and How

The interest vector should update in near real-time as users interact with content. Two approaches:

**Synchronous update** — update the vector immediately when an event occurs. Simple but adds latency to every interaction — the user clicks an article, you recompute the vector, then return the response. Acceptable at small scale.

**Async update** — log the event to a Redis Stream, a background worker consumes events and updates interest vectors in batches. This is the right architecture for Mindful — it fits perfectly into the existing event-driven infrastructure. The user interaction fires an event, the ETL-style consumer processes it, updates the vector in DuckDB. No latency added to the user experience.

The vector update itself: take the current interest vector, add the new article's embedding scaled by the interaction weight and a recency factor, renormalize so the vector magnitude stays consistent. Older contributions decay with each new interaction.

---

## The Popularity Engine — Solving Cold Start and Discovery

Separate from personalized recommendations, you need a global popularity ranking that runs continuously. This serves three purposes: cold start fallback for new users, discovery surface for all users, and a baseline to compare personalized recommendations against.

Popularity isn't just raw view count — that would permanently favor the oldest articles. Hacker News solved this elegantly with their ranking formula. Score decays over time but gets boosted by interactions. Recent high-engagement articles beat old medium-engagement articles. This formula keeps the popularity feed fresh and meritocratic.

For Mindful, compute a trending score for each article every hour based on: interactions in the last 24 hours weighted more than interactions in the last week, article age penalty so older content gradually falls off, and category normalization so a niche finance article with 50 reads isn't crushed by a viral tech article with 5000 reads.

---

## The Architecture in Full

```
User opens feed
        ↓
┌─────────────────────────────────────┐
│      INTEREST VECTOR LOOKUP         │
│  DuckDB users table                 │
│  New user → popularity fallback     │
└─────────────────────────────────────┘
        ↓
┌─────────────────────────────────────┐
│      CANDIDATE GENERATION           │
│  ChromaDB nearest-neighbor search   │
│  Top 50-100 by cosine similarity    │
└─────────────────────────────────────┘
        ↓
┌─────────────────────────────────────┐
│           FILTERING                 │
│  Remove already read                │
│  Remove disliked                    │
│  Apply freshness rules              │
└─────────────────────────────────────┘
        ↓
┌─────────────────────────────────────┐
│       DIVERSITY INJECTION           │
│  Cap per-category representation    │
│  Add exploratory content            │
└─────────────────────────────────────┘
        ↓
┌─────────────────────────────────────┐
│         SCORING & RANKING           │
│  Relevance + Popularity +           │
│  Freshness + Collaborative          │
│  → composite score per article      │
└─────────────────────────────────────┘
        ↓
      Top 10-20 articles served
        ↓
┌─────────────────────────────────────┐
│         EVENT LOGGING               │
│  User interactions → Redis Stream   │
│  Background worker updates          │
│  interest vector in DuckDB          │
└─────────────────────────────────────┘
```

---

## What Makes This Architecture Right for Mindful Specifically

Three reasons this design fits:

**ChromaDB is already there.** The entire article corpus is embedded. Candidate generation is already built — it's the same nearest-neighbor search as RAG retrieval. You're reusing infrastructure that already works.

**Redis Streams are already there.** Event logging fits naturally into the existing event-driven architecture. User interactions become events on a stream, a consumer processes them and updates interest vectors. Same pattern as the ETL pipeline.

**DuckDB is already there.** The users table, events table, and interest vectors live alongside the articles warehouse. No new database to operate.

The recommendation engine doesn't require new infrastructure — it's a new application layer on top of existing infrastructure. That's the payoff of building the data pipeline correctly from day one.