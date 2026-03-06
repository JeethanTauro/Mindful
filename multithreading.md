# Python Multithreading — Complete Guide

> *"Do multiple things at once — but understand exactly what that means in Python."*

---

## Table of Contents

1. [The Problem Multithreading Solves](#1-the-problem-multithreading-solves)
2. [Processes vs Threads — The Mental Model](#2-processes-vs-threads--the-mental-model)
3. [The GIL — Python's Most Misunderstood Feature](#3-the-gil--pythons-most-misunderstood-feature)
4. [CPU-Bound vs I/O-Bound Work](#4-cpu-bound-vs-io-bound-work)
5. [The threading Module — Low Level](#5-the-threading-module--low-level)
6. [ThreadPoolExecutor — The Modern Way](#6-threadpoolexecutor--the-modern-way)
7. [Futures — Handling Results and Exceptions](#7-futures--handling-results-and-exceptions)
8. [Shared State and Race Conditions](#8-shared-state-and-race-conditions)
9. [Locks — Protecting Shared Data](#9-locks--protecting-shared-data)
10. [Thread Safety — What It Means](#10-thread-safety--what-it-means)
11. [Multiprocessing — When Threads Aren't Enough](#11-multiprocessing--when-threads-arent-enough)
12. [Async/Await — The Third Option](#12-asyncawait--the-third-option)
13. [Choosing the Right Tool](#13-choosing-the-right-tool)
14. [How Multithreading Works in Mindful](#14-how-multithreading-works-in-mindful)

---

## 1. The Problem Multithreading Solves

Imagine you're cooking a meal. You need to:
- Boil water — takes 10 minutes, you just wait
- Chop vegetables — takes 5 minutes of active work
- Bake bread — takes 30 minutes, you just wait

Doing them sequentially:
```
Boil water (10 min wait)
→ Chop vegetables (5 min work)
→ Bake bread (30 min wait)
Total: 45 minutes
```

Doing them concurrently — start boiling, start baking, chop while waiting:
```
Start boiling + start baking simultaneously
Chop vegetables while waiting (5 min)
Everything finishes around the 30 min mark
Total: ~30 minutes
```

Same work, less wall clock time. You didn't work harder — you stopped waiting doing nothing and used the waiting time productively.

This is exactly what multithreading does in software. Instead of your program sitting idle waiting for a network response, it starts another task and comes back when the response arrives.

---

## 2. Processes vs Threads — The Mental Model

Before diving into threads, understand the difference between a **process** and a **thread**.

### Process
A process is a running program. When you run `python hackernews.py`, the OS creates a process. That process has:
- Its own memory space — completely isolated from other processes
- Its own Python interpreter
- Its own GIL
- Its own resources — file handles, network connections

Processes are heavy. Creating one takes time and memory. Communication between processes requires special mechanisms — pipes, queues, shared memory.

### Thread
A thread is a unit of execution that lives inside a process. One process can have many threads. All threads in a process share:
- The same memory space — they can all read and write the same variables
- The same resources — same file handles, same network connections
- The same Python interpreter
- The same GIL

Threads are lightweight. Creating one is fast. Communication between threads is easy — they already share memory.

### Visualizing It

```
Process (your Python program)
├── Memory (variables, objects, data)
├── Thread 1 ← main thread, always exists
├── Thread 2 ← you create this
├── Thread 3 ← you create this
└── Thread 4 ← you create this

All threads share the same memory.
```

When your `main.py` starts, there's one thread — the main thread. You can spawn additional threads to run functions concurrently. All threads live in the same process and share the same variables.

---

## 3. The GIL — Python's Most Misunderstood Feature

The **GIL (Global Interpreter Lock)** is a mutex — a lock — that allows only one thread to execute Python bytecode at a time.

This means:
- You can have 4 threads
- But only 1 thread runs Python code at any given microsecond
- The other 3 are waiting for the GIL to be released

This sounds like it makes threads useless. It doesn't. Here's why:

### When the GIL is Released

The GIL is released during **I/O operations**. When a thread makes a network request, reads a file, writes to a database, or sleeps — it releases the GIL. While that thread is waiting for the I/O to complete, other threads can run.

```
Thread 1: makes HTTP request → releases GIL → waits for response
                                    ↓
Thread 2: gets GIL → runs Python code → makes its HTTP request → releases GIL
                                    ↓
Thread 3: gets GIL → runs Python code → makes its HTTP request → releases GIL
                                    ↓
Thread 1: HTTP response arrives → reacquires GIL → processes response
```

All three HTTP requests are in-flight simultaneously even though only one thread runs Python code at a time. The network waiting is truly parallel.

### The GIL Diagram

```
Time →
Thread 1: [Python][===WAIT FOR HTTP===][Python][===WAIT===]
Thread 2:         [Python][===WAIT FOR HTTP===][Python]
Thread 3:                [Python][===WAIT FOR HTTP===]

[Python] = actually executing Python code (GIL held)
[===] = waiting for I/O (GIL released, other threads can run)
```

For I/O-bound work, threads give you real concurrency because most time is spent in the waiting blocks, not the Python blocks.

### Why the GIL Exists

The GIL was added to CPython (the standard Python interpreter) to make memory management simpler and safer. Python uses reference counting for garbage collection — every object tracks how many references point to it. Without the GIL, multiple threads modifying reference counts simultaneously could corrupt memory.

Removing the GIL is extremely difficult because so much of the Python ecosystem assumes it exists. There's active work on this (PEP 703 in Python 3.13 allows optional GIL disabling) but for now, the GIL is a fundamental reality of CPython.

---

## 4. CPU-Bound vs I/O-Bound Work

This distinction determines which concurrency tool to use.

### CPU-Bound Work
Work that keeps the CPU busy continuously — number crunching, image processing, machine learning training, sorting huge arrays, cryptography.

```python
# CPU-bound — the CPU is always working, never waiting
def compute_primes(limit):
    primes = []
    for n in range(2, limit):
        if all(n % i != 0 for i in range(2, n)):
            primes.append(n)
    return primes
```

For CPU-bound work, threads don't help because the GIL prevents true parallel execution. Only one thread crunches numbers at a time. Use **multiprocessing** instead — each process has its own GIL and can truly run in parallel on separate CPU cores.

### I/O-Bound Work
Work that spends most time waiting for external operations — network requests, file reads/writes, database queries, API calls.

```python
# I/O-bound — most time is spent waiting for the network
def fetch_article(url):
    response = requests.get(url)  # waiting... waiting... waiting...
    return response.json()        # finally, process the response
```

For I/O-bound work, threads work great because the GIL is released during the wait. Multiple requests can be in-flight simultaneously.

### The Rule

```
CPU-bound → multiprocessing (parallel execution on multiple cores)
I/O-bound → threading or async (concurrent waiting)
```

Web scraping is I/O-bound. API calls are I/O-bound. Database writes are I/O-bound. Everything Mindful's ingestion layer does is I/O-bound. Threading is exactly the right tool.

---

## 5. The threading Module — Low Level

Python's built-in `threading` module gives you direct control over threads. Understanding it is important even if you use higher-level tools, because it's what everything is built on.

### Creating and Starting a Thread

```python
import threading

def my_function(name, count):
    for i in range(count):
        print(f"Thread {name}: iteration {i}")

# Create a thread
t = threading.Thread(
    target=my_function,    # function to run
    args=("A", 3)          # positional arguments
)

# Start the thread — function begins executing in background
t.start()

# Main thread continues here immediately
print("Main thread continues")

# Wait for thread to finish before proceeding
t.join()

print("Thread finished, main thread resumes")
```

### Running Multiple Threads

```python
import threading
import requests

urls = [
    "https://api.example.com/article/1",
    "https://api.example.com/article/2",
    "https://api.example.com/article/3",
]

results = []

def fetch(url):
    response = requests.get(url)
    results.append(response.json())

# Create all threads
threads = [threading.Thread(target=fetch, args=(url,)) for url in urls]

# Start all threads
for t in threads:
    t.start()

# Wait for all to finish
for t in threads:
    t.join()

print(f"Fetched {len(results)} articles")
```

All three requests fire simultaneously. Total time is roughly the slowest single request, not the sum of all three.

### Thread Arguments — args and kwargs

```python
def process(source, limit, verbose=False):
    pass

# positional args
t = threading.Thread(target=process, args=("hackernews", 100))

# keyword args
t = threading.Thread(target=process, args=("hackernews",), kwargs={"limit": 100, "verbose": True})
```

### daemon Threads

A daemon thread runs in the background and is automatically killed when the main program exits. Non-daemon threads (the default) keep the program alive until they finish.

```python
t = threading.Thread(target=background_task, daemon=True)
t.start()
# program can exit even if t is still running
```

Use daemon threads for background tasks that shouldn't block program exit — like a monitoring thread or a heartbeat.

---

## 6. ThreadPoolExecutor — The Modern Way

The `threading` module is low-level. For most real use cases, `concurrent.futures.ThreadPoolExecutor` is cleaner, safer, and more powerful.

### Basic Usage

```python
from concurrent.futures import ThreadPoolExecutor

def fetch_article(url):
    response = requests.get(url)
    return response.json()

urls = ["url1", "url2", "url3", "url4", "url5"]

# max_workers = how many threads to use simultaneously
with ThreadPoolExecutor(max_workers=3) as executor:
    results = list(executor.map(fetch_article, urls))

# results is a list of return values in the same order as urls
print(results)
```

`executor.map()` is like Python's built-in `map()` but runs in parallel across threads. It:
- Distributes the work across the thread pool
- Returns results in the same order as the inputs
- Blocks until all tasks complete
- Re-raises any exceptions that occurred in threads

### submit() — More Control

`map()` is convenient but `submit()` gives you more control — you get a `Future` object back that you can inspect individually.

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def run_spider(spider_name):
    if spider_name == "hackernews":
        return hackernews.run()
    elif spider_name == "arxiv":
        return arxiv.run()
    elif spider_name == "wikipedia":
        return wikipedia.run()

spiders = ["hackernews", "arxiv", "wikipedia"]

with ThreadPoolExecutor(max_workers=3) as executor:
    # Submit all tasks, get Future objects back
    future_to_spider = {
        executor.submit(run_spider, name): name
        for name in spiders
    }

    # Process results as they complete
    for future in as_completed(future_to_spider):
        spider_name = future_to_spider[future]
        try:
            result = future.result()
            print(f"{spider_name} completed: {result}")
        except Exception as e:
            print(f"{spider_name} failed: {e}")
```

`as_completed()` yields futures in completion order — whichever spider finishes first, its result is processed first. You don't have to wait for the slowest one before seeing any results.

### Context Manager — Why `with`

The `with ThreadPoolExecutor() as executor:` pattern is important. When the `with` block exits:
1. No new tasks are accepted
2. It waits for all submitted tasks to complete (`shutdown(wait=True)`)
3. Resources are cleaned up

Without the context manager, you'd need to manually call `executor.shutdown()`. Always use the context manager.

### max_workers — How Many Threads

```python
ThreadPoolExecutor(max_workers=3)
```

How do you choose this number?

For I/O-bound work — you can use more threads than CPU cores because threads spend most time waiting. A common rule of thumb is `min(32, os.cpu_count() + 4)` which is actually the default in Python 3.8+.

For Mindful's three spiders — `max_workers=3` is perfect. One thread per spider, all three run simultaneously.

For scraping many URLs — `max_workers=10` or `max_workers=20` is reasonable. Don't go too high or you'll overwhelm the target servers and get rate limited.

---

## 7. Futures — Handling Results and Exceptions

A `Future` represents the eventual result of an asynchronous operation. It's a promise — "this computation is running, and when it finishes, the result will be here."

```python
from concurrent.futures import ThreadPoolExecutor

def divide(a, b):
    return a / b

with ThreadPoolExecutor(max_workers=2) as executor:
    future1 = executor.submit(divide, 10, 2)
    future2 = executor.submit(divide, 10, 0)  # will raise ZeroDivisionError

    # Check if done
    print(future1.done())  # might be True or False depending on timing

    # Get result — blocks until complete
    result = future1.result()  # 5.0
    print(result)

    # Exception is stored in the future, re-raised when you call .result()
    try:
        result = future2.result()
    except ZeroDivisionError as e:
        print(f"Task failed: {e}")
```

### Key Future Methods

```python
future.done()       # True if finished (success or failure)
future.running()    # True if currently executing
future.cancelled()  # True if was cancelled

future.result(timeout=5)    # get result, wait up to 5 seconds
future.exception()          # get the exception if one occurred, None otherwise

future.cancel()    # attempt to cancel (only works if not started yet)

# Callback — runs when future completes
future.add_done_callback(lambda f: print(f"Done: {f.result()}"))
```

### as_completed vs executor.map

```python
# executor.map — results in INPUT order, blocks until ALL done
results = list(executor.map(fetch, urls))
# if url[0] takes 10 seconds and url[1] takes 1 second,
# you wait 10 seconds before seeing ANY result

# as_completed — results in COMPLETION order, process each as it arrives
for future in as_completed(futures):
    result = future.result()
    # url[1] result appears after 1 second
    # url[0] result appears after 10 seconds
```

Use `executor.map` when you need all results together and order matters.
Use `as_completed` when you want to process results as they arrive and can handle any order.

---

## 8. Shared State and Race Conditions

Since all threads share the same memory, they can read and write the same variables. This is both the power and the danger of threading.

### The Race Condition

```python
import threading

counter = 0

def increment():
    global counter
    for _ in range(100000):
        counter += 1  # THIS IS NOT ATOMIC

threads = [threading.Thread(target=increment) for _ in range(5)]
for t in threads: t.start()
for t in threads: t.join()

print(counter)  # Expected: 500000. Actual: something less, varies each run
```

Why does this go wrong? `counter += 1` looks like one operation but it's actually three:
1. Read `counter` from memory
2. Add 1 to the value
3. Write the result back to memory

If two threads both read `counter = 100` simultaneously, both add 1, and both write back `101` — the counter only incremented once instead of twice. This is a **race condition** — the result depends on the timing of thread execution, which is unpredictable.

### Why Race Conditions Are Dangerous

They produce bugs that:
- Only happen sometimes — not every run
- Are impossible to reproduce reliably
- Don't appear in testing but show up in production
- Produce subtly wrong results, not crashes

The counter example is obvious. Real race conditions are subtle — duplicate database records, partial writes, corrupted caches.

---

## 9. Locks — Protecting Shared Data

A **Lock** (also called a mutex — mutual exclusion) ensures only one thread can execute a critical section at a time.

```python
import threading

counter = 0
lock = threading.Lock()

def increment():
    global counter
    for _ in range(100000):
        with lock:           # acquire lock — only one thread at a time
            counter += 1    # safe — no other thread can be here simultaneously
        # lock released — other threads can proceed

threads = [threading.Thread(target=increment) for _ in range(5)]
for t in threads: t.start()
for t in threads: t.join()

print(counter)  # Always 500000 — correct
```

`with lock:` is the context manager syntax. It acquires the lock on entry and releases it on exit — even if an exception is raised inside. Always use `with lock:` rather than manual `lock.acquire()` / `lock.release()`.

### The Cost of Locking

Every `with lock:` call is a potential waiting point. If Thread A holds the lock, Threads B, C, D all wait. Lock contention can serialize your threads and eliminate the benefit of threading entirely.

The rule: **lock as little as possible, for as short as possible.**

```python
# BAD — holds lock for entire function including I/O
def fetch_and_store(url):
    with lock:
        response = requests.get(url)  # waiting... everyone else waiting too
        results.append(response.json())

# GOOD — only lock the tiny write operation
def fetch_and_store(url):
    response = requests.get(url)  # I/O outside lock — other threads run freely
    with lock:
        results.append(response.json())  # lock only for the list write
```

### Other Synchronization Primitives

```python
# RLock — reentrant lock, same thread can acquire it multiple times
rlock = threading.RLock()

# Event — one thread signals others that something happened
event = threading.Event()
event.set()           # signal
event.wait()          # block until signaled
event.clear()         # reset

# Semaphore — allows N threads through simultaneously (like a rate limiter)
semaphore = threading.Semaphore(3)  # max 3 threads at once
with semaphore:
    # only 3 threads can be here simultaneously
    make_api_call()

# Queue — thread-safe queue for producer/consumer patterns
from queue import Queue
q = Queue()
q.put(item)           # producer adds item
item = q.get()        # consumer gets item (blocks if empty)
q.task_done()         # signal that item was processed
```

---

## 10. Thread Safety — What It Means

A function or object is **thread-safe** if it works correctly when called from multiple threads simultaneously, without requiring external locking.

### Thread-Safe Operations in Python

Python's built-in data structures have atomic operations protected by the GIL:

```python
# These are thread-safe — atomic under the GIL
list.append(item)      # safe
list.pop()             # safe
dict[key] = value      # safe
dict.get(key)          # safe
set.add(item)          # safe
```

But compound operations are not:

```python
# NOT thread-safe — read-modify-write is not atomic
if key not in dict:
    dict[key] = []          # another thread could set dict[key] between check and set
dict[key].append(value)     # another thread could have modified dict[key]
```

### Checking if Libraries are Thread-Safe

Before sharing an object across threads, always check the library's documentation for thread safety. Common answers:

- **boto3 S3 client** — thread-safe, can be shared across threads
- **requests.Session** — not thread-safe, create one per thread
- **SQLite connections** — not thread-safe by default, use `check_same_thread=False` or one connection per thread
- **walrus Database** — check docs, assume not safe, create per thread or use a connection pool

---

## 11. Multiprocessing — When Threads Aren't Enough

For CPU-bound work, use `multiprocessing` instead of `threading`. Each process gets its own Python interpreter and its own GIL — true parallelism across CPU cores.

```python
from concurrent.futures import ProcessPoolExecutor

def heavy_computation(data):
    # CPU-intensive work
    return process(data)

with ProcessPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(heavy_computation, large_dataset))
```

The API is identical to `ThreadPoolExecutor` — just swap the class name. That's intentional — `concurrent.futures` gives you a unified interface for both.

### Threads vs Processes Summary

| | Threads | Processes |
|---|---|---|
| Memory | Shared | Separate |
| Communication | Easy (shared variables) | Hard (queues, pipes) |
| Creation cost | Low | High |
| GIL limitation | Yes | No (each has own) |
| True parallelism | No (GIL) | Yes |
| Best for | I/O-bound | CPU-bound |
| Crash isolation | No (crash kills all) | Yes (crashes isolated) |

---

## 12. Async/Await — The Third Option

Threading isn't the only way to handle concurrency. Python also has `asyncio` — cooperative multitasking using `async/await` syntax.

The key difference:
- **Threading** — OS switches between threads (preemptive)
- **Asyncio** — code explicitly yields control (cooperative)

```python
import asyncio
import aiohttp  # async HTTP library

async def fetch(session, url):
    async with session.get(url) as response:
        return await response.json()

async def main():
    async with aiohttp.ClientSession() as session:
        tasks = [fetch(session, url) for url in urls]
        results = await asyncio.gather(*tasks)

asyncio.run(main())
```

### Threading vs Asyncio

| | Threading | Asyncio |
|---|---|---|
| Syntax | Normal Python | async/await |
| Library support | Everything works | Need async libraries |
| Switching | OS-controlled | Code-controlled |
| Debugging | Harder (non-deterministic) | Easier (deterministic) |
| Performance | Good | Better for very high concurrency |
| Learning curve | Medium | Higher |

For Mindful, threading is the right choice. You're using `requests`, `boto3`, `walrus` — all synchronous libraries. Switching to asyncio would require replacing all of them with async equivalents (`aiohttp`, `aioboto3`, async Redis client). The complexity isn't worth it for three spiders.

Asyncio shines when you need thousands of concurrent connections — a web server handling 10,000 simultaneous requests, or a scraper hitting 500 URLs at once. For three spiders, threading is simpler and sufficient.

---

## 13. Choosing the Right Tool

```
What kind of work is it?
│
├── CPU-bound (number crunching, ML, image processing)
│   └── Use multiprocessing — true parallelism across cores
│
└── I/O-bound (network, files, databases)
    │
    ├── How many concurrent tasks?
    │
    ├── Small number (< 100)
    │   └── Use threading with ThreadPoolExecutor — simple, works with all libraries
    │
    └── Large number (100s to 1000s)
        └── Use asyncio — lower overhead per task, but requires async libraries
```

For Mindful's ingestion layer:
- I/O-bound ✅
- Small number of concurrent tasks (3 spiders) ✅
- Using synchronous libraries (requests, boto3, walrus) ✅

**→ ThreadPoolExecutor with max_workers=3**

---

## 14. How Multithreading Works in Mindful

Here's exactly how `main.py` uses threading to run all three spiders simultaneously:

```
main.py starts
     │
     ▼
ThreadPoolExecutor(max_workers=3) created
     │
     ├── Thread 1 starts → run_hackernews_spider()
     │       │
     │       ├── fetch_ids() — HTTP request, GIL released
     │       ├── hit_item_endpoint() — 20 HTTP requests, GIL released each time
     │       └── upload() — MinIO + Redis writes, GIL released
     │
     ├── Thread 2 starts → run_arxiv_spider()
     │       │
     │       ├── fetch_content() — arxiv API calls, GIL released
     │       └── upload() — MinIO + Redis writes, GIL released
     │
     └── Thread 3 starts → run_wikipedia_spider()
             │
             ├── fetch_pages() — wikipedia API calls, GIL released
             └── upload() — MinIO + Redis writes, GIL released

All three run concurrently — GIL released during all I/O
Main thread waits for all three to finish
Summary printed — total articles, failures, time taken
```

The three spiders write to different MinIO paths (`raw/hackernews/`, `raw/arxiv/`, `raw/wikipedia/`) and different Redis streams (`raw/hackernews`, `raw/arxiv`, `raw/wikipedia`). No shared mutable state between threads. No locks needed. Thread-safe by design.

The S3 client in `lake_writer.py` is created once at module level and shared across all three threads — boto3 clients are thread-safe so this is fine.

Total time goes from `time(HN) + time(ArXiv) + time(Wikipedia)` to `max(time(HN), time(ArXiv), time(Wikipedia))`. For spiders that each take 5 minutes, that's 15 minutes → 5 minutes. For free.

---

*This is one of the most important concepts in backend engineering.*
*Almost every real system — web servers, data pipelines, scrapers — relies on concurrency.*
*Understanding threads, the GIL, race conditions, and when to use what tool makes you a significantly better engineer.*