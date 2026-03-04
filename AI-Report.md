# Mindful — Build Log
## Day 1: Understanding Web Scraping

> *"Before you write a single line of pipeline code, you need to understand the ground it stands on."*

---

## Table of Contents

1. [What is Web Scraping, Really?](#1-what-is-web-scraping-really)
2. [Crawling vs Scraping — The Actual Difference](#2-crawling-vs-scraping--the-actual-difference)
3. [How the Web Works (What You're Actually Scraping)](#3-how-the-web-works-what-youre-actually-scraping)
4. [The Two Types of Pages You'll Encounter](#4-the-two-types-of-pages-youll-encounter)
5. [Legal Landscape — What Can Get You in Trouble](#5-legal-landscape--what-can-get-you-in-trouble)
6. [robots.txt — The Gentleman's Agreement](#6-robotstxt--the-gentlemans-agreement)
7. [Rate Limiting and Ethical Scraping](#7-rate-limiting-and-ethical-scraping)
8. [Bot Detection — How Sites Catch You](#8-bot-detection--how-sites-catch-you)
9. [CAPTCHAs — What They Are and How to Handle Them](#9-captchas--what-they-are-and-how-to-handle-them)
10. [Cloudflare — The Big Boss](#10-cloudflare--the-big-boss)
11. [The Scraper's Toolkit — What to Use and When](#11-the-scrapers-toolkit--what-to-use-and-when)
12. [What Mindful Will Scrape and Why It's Safe](#12-what-mindful-will-scrape-and-why-its-safe)
13. [Day 1 Summary & Tomorrow](#13-day-1-summary--tomorrow)

---

## 1. What is Web Scraping, Really?

At its core, web scraping is **programmatically reading a webpage the same way your browser does, then extracting specific data from it.**

When you open Chrome and go to `https://news.ycombinator.com`, your browser does this:

1. Sends an HTTP GET request to Hacker News's server
2. The server responds with HTML — a giant string of text
3. Chrome parses that HTML and renders it visually
4. You read the titles, scores, and comments with your eyes

A scraper does the exact same thing — except instead of Chrome rendering it visually, your Python code parses the HTML and extracts just the data you care about (title, URL, score, author) and stores it somewhere.

That's it. There's no magic. **A scraper is a browser without eyes.**

### What Scraping Is Not

- It is not hacking. You are requesting publicly visible pages.
- It is not accessing a private database. You are reading what any anonymous visitor would see.
- It is not bypassing authentication (unless you intentionally do that, which is a separate and legally problematic thing).

---

## 2. Crawling vs Scraping — The Actual Difference

These two terms are often used interchangeably but they describe fundamentally different activities. In a production system like Mindful, you do **both**, and they happen in sequence.

### Crawling — Finding Pages

Crawling is the act of **discovering URLs**. A crawler starts at one URL, fetches the page, finds all the links on that page, adds those links to a queue, then visits each one, finds more links, and so on. It's recursive URL discovery.

Google's entire search engine is built on a massive crawler called Googlebot. It starts with a seed list of URLs and crawls the entire web by following links.

```
Start: https://news.ycombinator.com
  → finds link: /item?id=12345
    → finds link: https://some-blog.com/post/rust-performance
      → finds link: https://some-blog.com/post/memory-safety
        → ... and so on forever
```

A crawler answers the question: **"Where is the content?"**

### Scraping — Extracting Data

Scraping is what happens once you're on a page. It's the act of **parsing the HTML and pulling out structured data** — titles, authors, article bodies, publication dates, tags, scores. The scraper doesn't care about finding new pages. It cares about extracting meaning from the page it's currently on.

A scraper answers the question: **"What does this page contain?"**

### In Mindful — How Both Work Together

```
[Crawler]
  Knows the seed URLs (HN homepage, Reddit /r/programming, ArXiv new submissions)
  Visits them, discovers individual item URLs
  Adds discovered URLs to a work queue

[Scraper]
  Picks URLs from the queue
  Fetches each page
  Extracts: title, body, author, tags, date, source URL
  Drops the raw data into MinIO
```

Scrapy, the library we'll use, blurs this distinction because it handles both in a single framework. A Scrapy "Spider" crawls and scrapes simultaneously — it extracts data from a page and also follows links to more pages.

---

## 3. How the Web Works (What You're Actually Scraping)

To scrape well, you need to understand what's actually happening under the hood when you request a page.

### HTTP Request-Response

Every page load is a conversation between your code (the client) and a server:

```
Your Code                          Server
    |                                |
    |  GET /posts/123 HTTP/1.1       |
    |  Host: example.com             |
    |  User-Agent: Mozilla/5.0 ...   |
    |------------------------------> |
    |                                |
    |  HTTP/1.1 200 OK               |
    |  Content-Type: text/html       |
    |                                |
    |  <html>                        |
    |    <title>My Post</title>      |
    |    <body>...</body>            |
    |  </html>                       |
    | <-----------------------------|
```

The server doesn't know (or care at a basic level) whether the request came from Chrome or your Python script. A request is a request. This is why scraping is possible at all.

### Headers — The Identity Layer

Every HTTP request carries **headers** — metadata about the request. This is where detection starts. A browser sends headers like:

```
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate, br
Connection: keep-alive
```

A naive Python requests call sends:

```
User-Agent: python-requests/2.28.0
```

That single header immediately identifies you as a bot. **Sending realistic browser headers is the first line of defense.**

### HTML — What You're Parsing

HTML is a tree structure called the DOM (Document Object Model). Every piece of content lives at a specific location in that tree, addressable by CSS selectors or XPath expressions.

```html
<article class="post">
  <h1 class="post-title">Why Rust is Fast</h1>
  <span class="author">john_doe</span>
  <div class="post-body">
    Rust achieves its performance by...
  </div>
</article>
```

Your scraper uses selectors to point at exactly what it wants:

```
CSS:   article.post h1.post-title  →  "Why Rust is Fast"
CSS:   span.author                 →  "john_doe"
```

This is fundamentally what scraping is — navigating a tree of HTML and pulling out nodes.

---

## 4. The Two Types of Pages You'll Encounter

This is one of the most important distinctions in scraping, and getting it wrong wastes a lot of time.

### Type 1 — Static Pages (Server-Side Rendered)

The server responds with complete HTML. All the content you want is present in the HTML string the server sends back. Old-school websites, blogs, Wikipedia, Hacker News, and ArXiv all work this way.

```
Request → Server → Full HTML with all content → Done
```

You can scrape these with simple HTTP requests + an HTML parser. No browser required. Fast, lightweight, easy to run at scale.

**Tools: `requests` + `BeautifulSoup`, or `Scrapy`**

### Type 2 — Dynamic Pages (Client-Side Rendered)

The server responds with a nearly empty HTML shell, and then JavaScript running in the browser makes additional API calls to fetch the actual content and inject it into the DOM.

```
Request → Server → Empty HTML + JavaScript
                           ↓
                  Browser runs JavaScript
                           ↓
                  JS calls /api/posts → gets JSON → injects into DOM
                           ↓
                  Page looks full to the user
```

If you make a simple HTTP request to a dynamic page, you get the empty shell — no content. You have to actually execute the JavaScript to get the real data.

Reddit's new interface, Twitter/X, LinkedIn, and most modern SPAs (Single Page Applications) work this way.

**Tools: `Playwright` or `Selenium` (headless browser)**

### How to Tell Which Type You're Dealing With

1. Right-click the page → "View Page Source" (not Inspect Element)
2. If you can see the actual article text in the source code → static
3. If you see mostly `<div id="root"></div>` or similar → dynamic

### The Hybrid Approach (What We'll Do in Mindful)

Most of our sources are static or have official APIs. We use:
- **Scrapy** for static pages (HN, ArXiv, Wikipedia)
- **Playwright** only when we absolutely must handle JavaScript rendering
- **Official APIs** wherever they exist (HN API, Reddit PRAW, ArXiv API) — always prefer an API over scraping

---

## 5. Legal Landscape — What Can Get You in Trouble

This is the section most scraping tutorials skip. Don't skip it. The legal reality is nuanced and depends heavily on *what* you scrape, *how* you scrape it, and *what you do with the data.*

### The Cases That Matter

**hiQ Labs v. LinkedIn (2022)** — LinkedIn tried to block hiQ (a data analytics company) from scraping public profiles. The Ninth Circuit ruled that scraping *publicly accessible* data does not violate the Computer Fraud and Abuse Act (CFAA). This is currently the strongest legal protection for scraping public data.

**Craigslist v. 3Taps** — 3Taps scraped Craigslist listings after being sent a cease-and-desist. The court ruled that continuing to scrape after a C&D *does* violate CFAA. The lesson: if you get a cease-and-desist letter, you stop.

**Ryanair v. PR Aviation** — EU case establishing that even if you bypass technical measures to scrape, it may not be illegal *if the data is not copyrighted*. But the Terms of Service violation is still a civil issue.

### The Three Legal Buckets

**Generally Safe:**
- Publicly accessible data with no login required
- Data not protected by copyright (facts, prices, metadata)
- Scraping for personal, research, or academic use
- Scraping at rates that don't burden the server
- Respecting robots.txt

**Gray Area:**
- Scraping behind a login (even a free account)
- Violating Terms of Service (civil liability, not criminal, but still real)
- Scraping copyrighted text at scale for commercial purposes
- Bypassing rate limits intentionally

**Clearly Problematic:**
- Scraping after receiving a cease-and-desist
- Bypassing authentication to access private data
- Scraping personal/PII data (GDPR nightmare in EU)
- Circumventing technical access controls (CFAA violation territory)
- DDoSing a server with aggressive scraping

### The Terms of Service Problem

Almost every major website has a ToS clause like: *"You may not scrape, crawl, or use automated means to access our service."*

Violating ToS is generally a **civil matter**, not criminal. The site can ban your IP, terminate your account, and potentially sue you for breach of contract. They cannot have you arrested for reading their public pages.

For Mindful — a student project scraping public, non-login-required content for personal learning — you are in extremely safe territory legally. Academic and research use is consistently treated more leniently, and we're not doing anything commercial with the data.

---

## 6. robots.txt — The Gentleman's Agreement

Every well-behaved website has a file at `/robots.txt` that tells automated agents what they are and aren't allowed to crawl. It looks like this:

```
# Hacker News robots.txt
User-agent: *
Disallow: /x?
Disallow: /r?
Disallow: /vote?
Disallow: /reply?
Allow: /

Crawl-delay: 30
```

Breaking this down:

- `User-agent: *` — applies to all bots
- `Disallow: /vote?` — don't crawl voting endpoints (makes sense — those are actions, not content)
- `Allow: /` — the root and everything not listed is fine
- `Crawl-delay: 30` — wait 30 seconds between requests

### Is robots.txt Legally Binding?

**No.** It is a convention, not a law. There is no legal enforcement mechanism for robots.txt violations. However:

- Google respects it. Every reputable crawler respects it.
- Ignoring it when a cease-and-desist follows strengthens the other side's case.
- For Mindful, we respect it. Period. We're building something good, not trying to be adversarial.

### How Scrapy Handles It

Scrapy has `ROBOTSTXT_OBEY = True` as a setting. When enabled, Scrapy will automatically fetch and parse `/robots.txt` for every domain it crawls and skip any paths that are disallowed. We will always have this on.

---

## 7. Rate Limiting and Ethical Scraping

Even if everything you're doing is legal and you're respecting robots.txt, scraping too aggressively is still a problem — both ethically and practically.

### Why Rate Limiting Matters

A server has finite resources. If your scraper hammers it with 100 requests per second, you are effectively performing a denial-of-service attack, even if unintentionally. Small websites can go down. You'll get banned. And it's just bad behavior.

### The Rules Mindful Will Follow

| Rule | Why |
|---|---|
| Always obey `Crawl-delay` in robots.txt | It's the site's explicit request |
| Default to 1–2 second delay between requests per domain | Polite baseline |
| Randomize delay (1–3s) to avoid looking robotic | Also helps avoid detection |
| Never more than 5 concurrent requests to any single domain | Prevents server overload |
| Stop immediately on repeated 429 (Too Many Requests) responses | Respect the signal |
| Run scrapers during off-peak hours where possible | Lower impact |

### The Exponential Backoff Pattern

When a server responds with a 429 or 503, the correct behavior is:

```
First failure  → wait 5 seconds, retry
Second failure → wait 10 seconds, retry
Third failure  → wait 20 seconds, retry
Fourth failure → wait 40 seconds, retry
...cap at 5 minutes, then give up and move on
```

This is called exponential backoff and it's how every professional scraper handles rate limits.

---

## 8. Bot Detection — How Sites Catch You

Modern websites have sophisticated systems to distinguish real users from bots. Understanding these is essential, not just for evading detection (though that matters), but for understanding *why* certain scraping approaches fail.

### Detection Signal 1 — User-Agent String

The most obvious. Your HTTP library identifies itself by default. Always send a realistic, current browser User-Agent string. Rotate between several to avoid fingerprinting.

### Detection Signal 2 — Request Timing

Humans don't request pages at machine-perfect intervals. A bot that requests a page every exactly 2.000 seconds is obviously a bot. Real users have variable timing: 0.8s, 4.2s, 1.1s, 8.7s. Randomizing your delays is important.

### Detection Signal 3 — Request Patterns

A real user visits a homepage, clicks an article, reads for a while, goes back, clicks another. A bot visits 50 article pages in a row without ever visiting the homepage, never loading CSS or images, never executing JavaScript. Sites analyze navigation patterns.

### Detection Signal 4 — Missing Browser Fingerprints

Browsers send a lot of information beyond just the User-Agent:
- `Accept-Language` (what language the browser prefers)
- `Accept-Encoding` (what compression formats it supports)
- `Referer` (what page you came from)
- `Sec-Fetch-*` headers (a set of security-related headers only real browsers send)
- Cookie behavior (real browsers store and send cookies)
- TLS fingerprint (the specific cipher suites offered during HTTPS handshake — different for each browser)

A basic Python `requests` call is missing most of these. A headless Playwright browser sends all of them correctly.

### Detection Signal 5 — JavaScript Challenges

Some sites execute JavaScript that collects browser-specific data — canvas fingerprinting, WebGL signatures, font enumeration, screen resolution, mouse movement patterns — and sends it back to the server. A server-side HTTP client can't respond to these at all. This is why Playwright (a real browser engine) is sometimes necessary.

### Detection Signal 6 — IP Reputation

Your home IP is probably fine for development. But if you run a scraper on a cloud server (AWS, GCP, DigitalOcean), those IP ranges are well-known and often blocked by default. Datacenter IPs have poor reputation. Residential proxies have good reputation because they look like real users.

### Detection Signal 7 — Honeypot Links

Some pages contain invisible links — visible in the HTML but hidden from human eyes with CSS (`display: none`, white text on white background). A real user never clicks them. A scraper that follows all links will hit them. Hitting a honeypot immediately flags you as a bot.

---

## 9. CAPTCHAs — What They Are and How to Handle Them

CAPTCHA stands for "Completely Automated Public Turing test to tell Computers and Humans Apart." It's a challenge designed to be easy for humans and hard for machines.

### Types You'll Encounter

**reCAPTCHA v2 ("I'm not a robot" checkbox)**
The checkbox itself is easy. What's actually happening is Google is analyzing your mouse movement leading up to the click, your browser history on Google domains, your IP reputation, your cookies, and dozens of other signals. If everything looks human, you pass. If not, you get the image grid.

**reCAPTCHA v3 (invisible)**
No interaction at all. Runs silently in the background, scores your behavior 0.0–1.0, and returns that score to the site. The site decides what threshold to enforce. You won't even know it's running.

**hCaptcha**
Similar to reCAPTCHA v2 but privacy-focused. Common on Cloudflare-protected sites. Used by many sites that have left Google's ecosystem.

**Image/Text CAPTCHAs**
Old-school distorted text. Largely solved by OCR. Almost no serious site uses these alone anymore.

**Proof of Work CAPTCHAs**
Relatively new. Forces the browser to do computational work (solve a hash puzzle) before accessing content. Can be done by a script but takes time.

### How to Handle CAPTCHAs (Honestly)

**Strategy 1 — Don't Trigger Them**
The best approach. If you're scraping politely, using real browser headers, randomizing delays, and not hitting protected endpoints, most sites won't CAPTCHA you at all. For Mindful's sources (HN, ArXiv, Reddit API), CAPTCHAs essentially never appear.

**Strategy 2 — Use APIs Instead**
If a site has an official API, use it. APIs never have CAPTCHAs. Hacker News has a public Firebase API. Reddit has PRAW. ArXiv has an XML API. Always prefer the official channel.

**Strategy 3 — CAPTCHA Solving Services**
Services like 2captcha and Anti-Captcha employ human workers (or ML models) to solve CAPTCHAs on your behalf. You send them the CAPTCHA image, they send back the answer. Costs fractions of a cent per solve. This is legal and widely used. We won't need this for Mindful's sources.

**Strategy 4 — Playwright with Stealth Plugin**
`playwright-stealth` patches a headless browser to pass many bot-detection checks that would normally trigger CAPTCHAs. It modifies WebGL fingerprints, hides automation flags (`navigator.webdriver`), randomizes canvas rendering, and more.

---

## 10. Cloudflare — The Big Boss

Cloudflare sits in front of millions of websites as a reverse proxy. When you request `example.com`, you're not hitting example.com's server directly — you're hitting Cloudflare, which checks you, then passes the request along if you pass.

### What Cloudflare Actually Does

**Layer 1 — IP Reputation Check**
Cloudflare maintains a massive database of IP addresses with known bad behavior — scrapers, spammers, DDoS sources, Tor exit nodes, datacenter ranges. If your IP is in a bad category, you may be blocked before sending a single byte.

**Layer 2 — Browser Challenge (JS Challenge)**
Cloudflare sends back a page with JavaScript that runs in your browser, solves a computational puzzle, sets a cookie (`cf_clearance`), then redirects you to the actual page. A standard `requests` call fails here because it can't run JavaScript. Playwright handles this correctly because it's a real browser.

**Layer 3 — Managed Challenge / Turnstile**
Cloudflare's newer CAPTCHA system. More sophisticated behavioral analysis. Uses the `cf_clearance` cookie same as the JS challenge but with additional proof-of-work.

**Layer 4 — Under Attack Mode**
When a site is being DDoSed, Cloudflare puts up a 5-second delay page with aggressive challenge. Very difficult to bypass with automation.

### How to Handle Cloudflare for Mindful

**Honest answer: don't fight it.**

For sites with Cloudflare protection that don't offer APIs, there are three realistic approaches:

1. **Use Playwright** — A real browser passes the JS challenge naturally. Combined with `playwright-stealth`, you can get through most Cloudflare protections.

2. **Use `cloudscraper`** — A Python library specifically designed to bypass Cloudflare's JS challenge by emulating the JavaScript computation locally. Works on older Cloudflare versions. Often breaks when Cloudflare updates.

3. **Don't scrape that site** — If a site is behind serious Cloudflare protection and has no API, it's a strong signal they don't want to be scraped. Find another source.

For Mindful, none of our primary sources (Hacker News, ArXiv, Reddit API, Wikipedia) use aggressive Cloudflare protection. We simply won't target sites that do.

---

## 11. The Scraper's Toolkit — What to Use and When

Here's a clear decision tree for every scraping scenario:

### Decision Tree

```
Does the site have an official API?
  └── YES → Use the API. Always. No exceptions.
  └── NO  → Is the content visible in Page Source (static HTML)?
              └── YES → Use Scrapy
              └── NO  → Is it a JavaScript-rendered SPA?
                          └── YES → Use Playwright
                          └── NO  → Does it have Cloudflare?
                                      └── YES → Try Playwright + stealth, or skip
                                      └── NO  → Use Scrapy with proper headers
```

### The Tools

**`requests` + `BeautifulSoup`**
The simplest combo. `requests` fetches the page, `BeautifulSoup` parses the HTML. Good for one-off scripts and simple sites. Not built for scale — no concurrency, no crawl management, no retry logic built in.

**`Scrapy`**
The production scraping framework. Built-in support for concurrent requests, retry logic, rate limiting, robots.txt obedience, middleware pipeline, item pipelines for data processing, and more. This is what Mindful uses for all static sources. Steep learning curve day one, but the right tool.

**`Playwright`**
A headless browser library from Microsoft. Launches a real Chrome/Firefox/WebKit instance programmatically. Handles JavaScript, cookies, sessions, and all browser APIs correctly. Slower and heavier than Scrapy (real browser vs HTTP requests) but necessary for dynamic pages. Playwright is Python-native (unlike Selenium which was Java-first).

**`HTTPX`**
A modern, async HTTP library. Think `requests` but with full async/await support and HTTP/2. Good for building custom async scrapers without Scrapy's framework structure.

**`parsel`**
Scrapy's HTML/XML parsing library, available standalone. Uses CSS selectors and XPath. Much faster than BeautifulSoup for high-volume parsing.

### What Mindful Uses

| Source | Approach | Why |
|---|---|---|
| Hacker News | Firebase REST API | Official, structured, no scraping needed |
| Reddit | PRAW library (official API) | Official, rich data, rate limit built in |
| ArXiv | ArXiv API (XML) | Official, academic, ideal |
| Wikipedia | `wikipedia-api` Python library | Official wrapper around MediaWiki API |
| General articles | Scrapy | For any linked articles from the above |
| Dynamic pages (rare) | Playwright | Only when absolutely necessary |

---

## 12. What Mindful Will Scrape and Why It's Safe

Let's be concrete about our sources and our legal/ethical standing:

### Hacker News

- **API**: `https://hacker-news.firebaseio.com/v0/` — official, public, no auth
- **robots.txt**: Allows crawling of all content pages
- **ToS**: No aggressive restrictions on API use
- **Data**: Post titles, URLs, scores, comment counts, authors, timestamps
- **Risk level**: Essentially zero

### Reddit

- **API**: PRAW (official Python Reddit API Wrapper) — requires free API key registration
- **robots.txt**: Allows crawling
- **ToS**: Academic/personal use is fine; commercial redistribution is not
- **Rate limits**: 60 requests/minute on free tier — plenty for Mindful
- **Data**: Post titles, bodies, scores, subreddit, author, comments
- **Risk level**: Zero if you register for API access

### ArXiv

- **API**: `https://export.arxiv.org/api/query` — official, no auth required
- **robots.txt**: Explicitly allows crawling
- **ToS**: Open access is ArXiv's entire mission. They want you to use the data.
- **Data**: Paper titles, abstracts, authors, categories, dates, full PDF links
- **Risk level**: Zero

### Wikipedia

- **API**: MediaWiki API — official, no auth for read operations
- **License**: CC BY-SA — content is freely reusable with attribution
- **Data**: Article text, categories, links, revision history
- **Risk level**: Zero — Wikipedia literally encourages data reuse

---

## 13. Day 1 Summary & Tomorrow

### What We Covered Today

- **Scraping** is programmatically extracting data from web pages. It's legal for public data, has nuances, and requires ethical practice.
- **Crawling** is discovering URLs. **Scraping** is extracting data from those URLs. In Mindful, Scrapy does both.
- The web is **HTTP + HTML**. Static pages are easy. Dynamic JavaScript-rendered pages require a real browser engine.
- **Legal risk** is real but manageable: public data, no login bypass, respecting robots.txt, polite rate limits = safe.
- **Bot detection** works via User-Agent, timing patterns, browser fingerprints, JavaScript challenges, and IP reputation.
- **CAPTCHAs** are best avoided by being polite. For Mindful's sources, we won't encounter them.
- **Cloudflare** is the hardest obstacle. We're avoiding sources that use it aggressively.
- **Use official APIs wherever they exist.** For Mindful: HN, Reddit, ArXiv, and Wikipedia all have them.

### What Mindful's Scraping Layer Will Look Like

```
Prefect Scheduler
    │
    ├── HN Spider (Scrapy + Firebase API)       every 15 min
    ├── Reddit Spider (PRAW)                    every 30 min
    ├── ArXiv Spider (XML API)                  every 2 hours
    └── Wikipedia Spider (MediaWiki API)        once daily

Each spider:
    1. Fetches new items since last run
    2. Validates and normalizes to a common schema
    3. Writes raw JSON to MinIO (raw/ prefix)
    4. Publishes message to Redis Stream
    5. Logs run metadata to DuckDB pipeline_runs table
```

### Tomorrow — Day 2

Day 2 we get our hands dirty:

- Set up the project repository structure
- Write the `docker-compose.yml` that brings up MinIO, Redis, and DuckDB
- Write the first spider — Hacker News via the Firebase API
- Verify raw JSON is landing in MinIO
- Write the Redis Stream publisher so the ETL layer has something to listen to

The pipeline comes to life tomorrow. Today was about understanding the ground we're standing on.

---

*Mindful Build Log — Day 1 of 56*
*Next: Day 2 — Environment Setup & First Spider*

---

> **Before Day 2:** Read [`python_oop.md`](./python_oop.md) — covers classes, objects, constructors, inheritance, and dataclasses. Every tool you use tomorrow is built on these concepts.