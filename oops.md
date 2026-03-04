# Python OOP — Everything You Need for Mindful

> *Read this before Day 2. Every major library in this project — Scrapy, FastAPI, Pydantic — is built on these concepts. Understanding them means you understand the tools, not just copy them.*

---

## Table of Contents

1. [Why OOP Exists — The Mental Model](#1-why-oop-exists--the-mental-model)
2. [Classes — The Blueprint](#2-classes--the-blueprint)
3. [Objects — The Actual Thing](#3-objects--the-actual-thing)
4. [The Constructor — `__init__`](#4-the-constructor----init__)
5. [`self` — What It Actually Is](#5-self--what-it-actually-is)
6. [Instance Variables vs Class Variables](#6-instance-variables-vs-class-variables)
7. [Methods — The Three Types](#7-methods--the-three-types)
8. [Inheritance — The Most Important Concept for This Project](#8-inheritance--the-most-important-concept-for-this-project)
9. [`super()` — Talking to Your Parent](#9-super--talking-to-your-parent)
10. [Encapsulation — Public, Protected, Private](#10-encapsulation--public-protected-private)
11. [Dunder / Magic Methods](#11-dunder--magic-methods)
12. [Dataclasses — The Modern Shortcut](#12-dataclasses--the-modern-shortcut)
13. [How All of This Shows Up in Mindful](#13-how-all-of-this-shows-up-in-mindful)

---

## 1. Why OOP Exists — The Mental Model

Before you learn the syntax, understand the *why*. Otherwise OOP feels like unnecessary ceremony.

Imagine you're building Mindful and you need to represent an article. Without OOP, you'd probably use a dictionary:

```python
article = {
    "title": "Why Rust is Fast",
    "author": "john_doe",
    "body": "Rust achieves performance by...",
    "source": "hackernews",
    "score": 342
}
```

That works for one article. But what if you need to:
- Validate that `score` is always a number, never a string?
- Have a method that computes reading time from the body length?
- Ensure every article always has a `title` — it can never be missing?
- Create 50,000 articles with the same structure?

With dictionaries you'd be writing the same validation logic everywhere, there's no guarantee of structure, and nothing stops someone from doing `article["scroe"] = "abc"` and breaking everything silently.

**OOP solves this by letting you define a template — a class — that describes what an article IS and what it can DO. Every article you create from that template is guaranteed to have the right structure and the right behavior.**

That's the entire motivation. OOP is about:
- **Structure** — guaranteed shape for your data
- **Behavior** — functions that belong to the data they operate on
- **Reuse** — define once, use everywhere
- **Safety** — control what can and can't be changed

---

## 2. Classes — The Blueprint

A class is a blueprint. It doesn't exist as a real thing — it's just the description of what a thing will look like when you create one.

```python
class Article:
    pass
```

That's a valid (if useless) class. `Article` is now a blueprint for creating article objects. The `pass` just means "nothing inside yet."

A more real class:

```python
class Article:
    # This is the blueprint for every article in Mindful
    
    source = "unknown"  # this is a class variable — more on this later
    
    def __init__(self, title, author, body):
        self.title = title
        self.author = author
        self.body = body
        self.score = 0
    
    def reading_time(self):
        words = len(self.body.split())
        minutes = words // 200  # average reading speed
        return f"{minutes} min read"
```

Breaking this down:
- `class Article:` — defines the blueprint, named `Article`
- Everything indented inside is part of the class
- `__init__` is the constructor (covered in section 4)
- `reading_time` is a method — a function that belongs to this class
- `self` refers to the specific article instance (covered in section 5)

**Naming convention:** Class names in Python are always `PascalCase` — every word capitalized, no underscores. `Article`, `HackerNewsSpider`, `RedditCrawler`, `DataLakeWriter`.

---

## 3. Objects — The Actual Thing

A class is the blueprint. An **object** (also called an **instance**) is the actual thing built from that blueprint.

```python
# Creating objects from the Article class
article1 = Article("Why Rust is Fast", "john_doe", "Rust achieves performance by...")
article2 = Article("Python is Underrated", "jane_smith", "Python's ecosystem is vast...")

print(article1.title)         # "Why Rust is Fast"
print(article2.title)         # "Python is Underrated"
print(article1.reading_time()) # "0 min read" (short body)
```

`article1` and `article2` are two separate objects. They're both built from the `Article` blueprint, but they're completely independent — changing `article1.title` doesn't affect `article2.title` at all.

This is called **instantiation** — the act of creating an instance (object) from a class.

```python
# You can create as many as you want
articles = [
    Article("Title A", "author1", "body text..."),
    Article("Title B", "author2", "more text..."),
    Article("Title C", "author3", "even more..."),
]

# Each one is independent
for a in articles:
    print(a.title, "—", a.reading_time())
```

**Key insight:** The class lives in memory once. Every object created from it has its own copy of the instance variables (`title`, `author`, `body`) but shares the class-level structure and methods.

---

## 4. The Constructor — `__init__`

`__init__` is a special method that Python calls automatically every time you create a new object. It's where you set up the initial state of the object — give it its starting values.

```python
class Article:
    def __init__(self, title, author, body, source="unknown"):
        self.title = title        # required
        self.author = author      # required
        self.body = body          # required
        self.source = source      # optional, defaults to "unknown"
        self.score = 0            # always starts at 0, user doesn't set this
        self.tags = []            # always starts as empty list
```

When you write:
```python
a = Article("Why Rust is Fast", "john_doe", "Rust is...")
```

Python internally calls:
```python
Article.__init__(a, "Why Rust is Fast", "john_doe", "Rust is...")
```

The `__init__` runs, sets all the attributes on `a`, and hands you back a fully formed object.

### Default Arguments in `__init__`

```python
class Spider:
    def __init__(self, name, delay=2.0, max_retries=3):
        self.name = name
        self.delay = delay
        self.max_retries = max_retries

# These are all valid
s1 = Spider("hackernews")                    # delay=2.0, max_retries=3
s2 = Spider("reddit", delay=1.5)             # max_retries=3
s3 = Spider("arxiv", delay=1.0, max_retries=5)
```

Default arguments make some parameters optional. Always put required parameters before optional ones.

### What NOT to Do in `__init__`

`__init__` should set up state, not do heavy work:

```python
# BAD — making a network call in __init__
class HackerNewsSpider:
    def __init__(self):
        self.data = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json")
        # If this fails, your object doesn't even get created

# GOOD — set up state, separate method for work
class HackerNewsSpider:
    def __init__(self):
        self.base_url = "https://hacker-news.firebaseio.com/v0"
        self.fetched_ids = []
    
    def fetch_top_stories(self):
        # Network call lives here, not in __init__
        response = requests.get(f"{self.base_url}/topstories.json")
        return response.json()
```

---

## 5. `self` — What It Actually Is

`self` confuses almost everyone the first time. Let's kill the confusion completely.

`self` is just a reference to **the specific object the method is being called on.** It's how a method knows which object's data to work with.

```python
class Article:
    def __init__(self, title):
        self.title = title
    
    def shout_title(self):
        print(self.title.upper())

a1 = Article("Rust is Fast")
a2 = Article("Python is Great")

a1.shout_title()  # prints "RUST IS FAST"
a2.shout_title()  # prints "PYTHON IS GREAT"
```

When you call `a1.shout_title()`, Python internally does:
```python
Article.shout_title(a1)  # passes a1 as 'self'
```

So inside `shout_title`, `self` IS `a1`. `self.title` is `a1.title` which is `"Rust is Fast"`.

When you call `a2.shout_title()`, `self` IS `a2`. Same method, different object, different data.

### Why Is It Called `self`?

It doesn't have to be. `self` is just a convention — Python doesn't enforce the name. You could write:

```python
def shout_title(this):
    print(this.title.upper())
```

And it would work identically. But every Python programmer in the world uses `self`, so use `self`. Breaking this convention will confuse everyone including future you.

### The Golden Rule of `self`

**Every method in a class takes `self` as its first parameter. Every attribute stored on an object is accessed via `self.attribute_name`. If you forget `self`, Python thinks you're talking about a local variable that doesn't exist.**

```python
class Article:
    def __init__(self, title):
        title = title      # WRONG — this is a local variable, lost immediately
        self.title = title # RIGHT — stored on the object, accessible everywhere
```

---

## 6. Instance Variables vs Class Variables

This is a subtle but important distinction.

### Instance Variables

Defined inside `__init__` using `self`. Each object gets its own copy. Changing one object's instance variable doesn't affect any other object.

```python
class Article:
    def __init__(self, title):
        self.title = title    # instance variable

a1 = Article("Rust")
a2 = Article("Python")

a1.title = "Go"  # only changes a1
print(a1.title)  # "Go"
print(a2.title)  # "Python" — completely unaffected
```

### Class Variables

Defined at the class level, outside `__init__`. **Shared across all instances.** Changing a class variable affects every object.

```python
class Article:
    total_articles = 0    # class variable — shared by all articles
    
    def __init__(self, title):
        self.title = title           # instance variable
        Article.total_articles += 1  # increment the shared counter

a1 = Article("Rust")
a2 = Article("Python")
a3 = Article("Go")

print(Article.total_articles)  # 3
print(a1.total_articles)       # 3 — accessible from instance too
print(a2.total_articles)       # 3
```

### The Trap — Mutable Class Variables

Be careful with mutable class variables (lists, dicts):

```python
class Spider:
    visited_urls = []  # DANGEROUS if mutable

s1 = Spider()
s2 = Spider()

s1.visited_urls.append("https://example.com")
print(s2.visited_urls)  # ["https://example.com"] — SURPRISE! Shared!
```

If you want each instance to have its own list, define it in `__init__`:

```python
class Spider:
    def __init__(self):
        self.visited_urls = []  # each spider gets its own list
```

### When to Use Each

| Class Variable | Instance Variable |
|---|---|
| Constants shared by all instances | Data unique to each object |
| Counters tracking all instances | Object's own state |
| Configuration defaults | Per-object configuration |

---

## 7. Methods — The Three Types

A method is just a function defined inside a class. But there are three distinct types, each with a different purpose.

### Type 1 — Instance Methods (Most Common)

Takes `self` as the first argument. Can read and modify the object's state. This is what you'll write 90% of the time.

```python
class Article:
    def __init__(self, title, body):
        self.title = title
        self.body = body
        self.is_published = False
    
    def publish(self):
        self.is_published = True
        print(f"'{self.title}' is now published")
    
    def word_count(self):
        return len(self.body.split())
    
    def summary(self):
        words = self.body.split()[:20]
        return " ".join(words) + "..."

a = Article("Rust is Fast", "Rust achieves performance by eliminating garbage collection...")
a.publish()           # "'Rust is Fast' is now published"
print(a.word_count()) # number of words
print(a.summary())    # first 20 words + "..."
```

### Type 2 — Class Methods (`@classmethod`)

Takes `cls` (the class itself) as the first argument instead of `self`. Can't access instance data — it doesn't have an instance. Used for alternative constructors and factory methods.

```python
class Article:
    def __init__(self, title, author, body, source):
        self.title = title
        self.author = author
        self.body = body
        self.source = source
    
    @classmethod
    def from_hackernews(cls, hn_data):
        # Alternative constructor that knows how to parse HN API format
        return cls(
            title=hn_data["title"],
            author=hn_data["by"],
            body=hn_data.get("text", ""),
            source="hackernews"
        )
    
    @classmethod
    def from_reddit(cls, reddit_post):
        # Alternative constructor for Reddit's format
        return cls(
            title=reddit_post.title,
            author=str(reddit_post.author),
            body=reddit_post.selftext,
            source="reddit"
        )

# Usage — creates an Article from HN API response
hn_response = {"title": "Rust 2024", "by": "johndoe", "text": "..."}
article = Article.from_hackernews(hn_response)
```

This is an incredibly common pattern. Each data source has a different format — `@classmethod` lets you define one constructor per source format, all producing the same `Article` object. You'll use this exact pattern in Mindful.

### Type 3 — Static Methods (`@staticmethod`)

Takes neither `self` nor `cls`. It's just a regular function that logically belongs inside a class for organizational reasons. Can't access or modify any instance or class data.

```python
class Article:
    @staticmethod
    def is_valid_url(url):
        return url.startswith("http://") or url.startswith("https://")
    
    @staticmethod
    def estimate_reading_time(word_count):
        return max(1, word_count // 200)

# Can be called on the class or an instance — doesn't matter
print(Article.is_valid_url("https://example.com"))  # True
print(Article.estimate_reading_time(500))            # 2
```

Use static methods when the logic is related to the class conceptually but doesn't need to touch any object's state.

---

## 8. Inheritance — The Most Important Concept for This Project

Inheritance lets one class **inherit** the attributes and methods of another class. This is why you can write a Scrapy spider by just extending `scrapy.Spider` — you get all of Scrapy's functionality for free, and you only write what's specific to your use case.

```python
# Parent class (also called Base class or Superclass)
class Spider:
    def __init__(self, name, delay=2.0):
        self.name = name
        self.delay = delay
        self.items_scraped = 0
    
    def fetch(self, url):
        print(f"[{self.name}] Fetching {url}")
        # ... HTTP request logic
    
    def log(self, message):
        print(f"[{self.name}] {message}")
    
    def run(self):
        raise NotImplementedError("Subclasses must implement run()")

# Child class (also called Subclass or Derived class)
class HackerNewsSpider(Spider):  # inherits from Spider
    def __init__(self):
        super().__init__(name="hackernews", delay=1.0)  # calls parent __init__
        self.base_url = "https://hacker-news.firebaseio.com/v0"
    
    def run(self):
        self.log("Starting HN crawl...")
        # HN-specific logic here
        self.fetch(f"{self.base_url}/topstories.json")

class RedditSpider(Spider):  # also inherits from Spider
    def __init__(self, subreddit):
        super().__init__(name=f"reddit-{subreddit}", delay=2.0)
        self.subreddit = subreddit
    
    def run(self):
        self.log(f"Starting r/{self.subreddit} crawl...")
        # Reddit-specific logic here

# Usage
hn = HackerNewsSpider()
hn.log("hello")    # works — inherited from Spider
hn.run()           # works — defined in HackerNewsSpider

reddit = RedditSpider("programming")
reddit.log("hello") # works — inherited from Spider
reddit.run()        # works — defined in RedditSpider
```

`HackerNewsSpider` gets `fetch()`, `log()`, `items_scraped` for free — it doesn't have to define them. It only defines what's unique to Hacker News.

### The Inheritance Hierarchy

```
Spider (base — shared logic for all spiders)
    ├── HackerNewsSpider (HN-specific)
    ├── RedditSpider (Reddit-specific)
    ├── ArXivSpider (ArXiv-specific)
    └── WikipediaSpider (Wikipedia-specific)
```

This is literally the structure Mindful uses. And it's the same structure Scrapy uses internally — you inherit from `scrapy.Spider` and fill in the specifics.

### Method Overriding

A child class can redefine a method from the parent:

```python
class Spider:
    def handle_error(self, error):
        print(f"Error: {error}")  # basic error handling

class HackerNewsSpider(Spider):
    def handle_error(self, error):
        # Override with more specific behavior
        print(f"HN Spider Error: {error}")
        # retry logic specific to HN
        self.retry_count += 1
```

When you call `hn_spider.handle_error(...)`, Python uses `HackerNewsSpider`'s version, not `Spider`'s. This is called **method overriding** or **polymorphism** — same method name, different behavior depending on the object.

---

## 9. `super()` — Talking to Your Parent

`super()` gives you access to the parent class. Most commonly used in `__init__` to call the parent's constructor before adding child-specific setup.

```python
class Spider:
    def __init__(self, name, delay):
        self.name = name
        self.delay = delay
        self.items_scraped = 0
        self.errors = []

class HackerNewsSpider(Spider):
    def __init__(self):
        super().__init__(name="hackernews", delay=1.0)
        # After super().__init__ runs, self.name, self.delay,
        # self.items_scraped, and self.errors already exist
        self.base_url = "https://hacker-news.firebaseio.com/v0"
        # now add HN-specific attributes
```

Without `super().__init__()`, the parent's `__init__` never runs, and the child object is missing `name`, `delay`, `items_scraped`, and `errors`.

### `super()` for Method Extension

You can also use `super()` to call the parent's version of a method *and then* add more behavior:

```python
class Spider:
    def close(self):
        print(f"Spider {self.name} shutting down")

class HackerNewsSpider(Spider):
    def close(self):
        super().close()                          # run parent's close first
        print("Saving HN-specific state...")    # then do HN-specific cleanup
```

---

## 10. Encapsulation — Public, Protected, Private

Encapsulation is about controlling access to an object's internal data. Python's approach is more relaxed than Java or C++ — it uses naming conventions rather than hard enforcement.

### Public (No Underscore)

Accessible from anywhere. This is the default.

```python
class Article:
    def __init__(self, title):
        self.title = title      # public — anyone can read/write

a = Article("Rust")
print(a.title)   # fine
a.title = "Go"   # also fine
```

### Protected (Single Underscore `_`)

Convention saying "this is internal — don't touch it from outside unless you know what you're doing." Python doesn't actually prevent access, it's just a signal to other developers.

```python
class Spider:
    def __init__(self):
        self._session = None      # protected — internal implementation detail
        self._retry_count = 0     # protected

    def _create_session(self):    # protected method
        # internal setup
        pass
```

You'll see `_variable` constantly in library code. It means "this is how the library works internally — if you depend on it, you're on your own when it changes."

### Private (Double Underscore `__`)

Python actually does something here — it **name mangles** the attribute to make it harder (not impossible) to access from outside. Used for things that really should not be touched.

```python
class DataLakeWriter:
    def __init__(self, access_key, secret_key):
        self.__access_key = access_key   # private — never expose credentials
        self.__secret_key = secret_key

writer = DataLakeWriter("key123", "secret456")
print(writer.__access_key)           # AttributeError — can't access directly
print(writer._DataLakeWriter__access_key)  # technically works, but you're being naughty
```

### Python's Philosophy

Python's attitude is "we're all adults here." It doesn't go out of its way to enforce private access. The underscore conventions exist to communicate intent to other developers. In practice, use `_` for internal things and `__` only for credentials or truly sensitive data.

---

## 11. Dunder / Magic Methods

Dunder methods (short for "double underscore") are special methods Python calls automatically in certain situations. They're what makes your objects feel like native Python objects.

### `__str__` and `__repr__`

```python
class Article:
    def __init__(self, title, author):
        self.title = title
        self.author = author
    
    def __str__(self):
        # Human-readable string — used by print()
        return f"'{self.title}' by {self.author}"
    
    def __repr__(self):
        # Developer-readable string — used in the REPL and for debugging
        return f"Article(title='{self.title}', author='{self.author}')"

a = Article("Rust is Fast", "john_doe")
print(a)      # 'Rust is Fast' by john_doe   (uses __str__)
a             # Article(title='Rust is Fast', author='john_doe')  (uses __repr__)
```

### `__len__`

```python
class ArticleCollection:
    def __init__(self):
        self.articles = []
    
    def add(self, article):
        self.articles.append(article)
    
    def __len__(self):
        return len(self.articles)

collection = ArticleCollection()
collection.add(Article("Rust", "john"))
collection.add(Article("Python", "jane"))

print(len(collection))  # 2 — Python calls __len__ automatically
```

### `__getitem__` — Makes Your Object Subscriptable

```python
class ArticleCollection:
    def __init__(self):
        self.articles = []
    
    def __getitem__(self, index):
        return self.articles[index]

collection = ArticleCollection()
# ... add articles ...
print(collection[0])   # works like a list
print(collection[1:3]) # slicing works too
```

### `__contains__` — Makes `in` Work

```python
class ArticleCollection:
    def __contains__(self, url):
        return any(a.url == url for a in self.articles)

if "https://example.com/post" in collection:
    print("Already scraped")
```

### `__enter__` and `__exit__` — Context Managers

This is how `with` statements work. You'll see this constantly with database connections and file handles:

```python
class DatabaseConnection:
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()  # always runs, even if an exception occurred
        return False

# Usage
with DatabaseConnection() as db:
    db.query("SELECT * FROM articles")
# disconnect() is automatically called here, even if query raised an error
```

---

## 12. Dataclasses — The Modern Shortcut

Dataclasses are a Python 3.7+ feature that automatically generates `__init__`, `__repr__`, and `__eq__` for you based on type-annotated class variables. They're perfect for data containers — exactly what Mindful uses to represent articles, events, and pipeline messages.

### Without Dataclass

```python
class Article:
    def __init__(self, title: str, author: str, body: str, score: int = 0):
        self.title = title
        self.author = author
        self.body = body
        self.score = score
    
    def __repr__(self):
        return f"Article(title='{self.title}', author='{self.author}', score={self.score})"
    
    def __eq__(self, other):
        return self.title == other.title and self.author == other.author
```

### With Dataclass — Exactly the Same Result

```python
from dataclasses import dataclass, field

@dataclass
class Article:
    title: str
    author: str
    body: str
    score: int = 0
    tags: list = field(default_factory=list)  # mutable default — use field()
```

Python automatically generates `__init__`, `__repr__`, and `__eq__` from the type annotations. That's it. Cleaner, less code, same result.

### `field()` for Mutable Defaults

Never use a mutable object (list, dict) as a default value directly — it would be shared across all instances (the same trap from class variables). Use `field(default_factory=...)` instead:

```python
@dataclass
class Article:
    tags: list = field(default_factory=list)   # each Article gets its own list
    metadata: dict = field(default_factory=dict) # each Article gets its own dict
```

### Frozen Dataclasses (Immutable)

```python
@dataclass(frozen=True)
class ArticleID:
    source: str
    url: str
    # Once created, cannot be modified — raises FrozenInstanceError
    # Also becomes hashable — can be used as a dict key or in a set
```

### In Mindful, dataclasses represent:

```python
@dataclass
class RawArticle:
    """What the spider produces and drops into MinIO"""
    id: str
    source: str
    url: str
    title: str
    body: str
    author: str
    scraped_at: str
    tags: list = field(default_factory=list)

@dataclass
class StreamMessage:
    """What gets published to the Redis Stream"""
    event_type: str
    minio_path: str
    article_id: str
    timestamp: str
```

---

## 13. How All of This Shows Up in Mindful

Let's connect everything you just learned to the actual project so it doesn't feel abstract.

### Scrapy Spider — Inheritance in Action

```python
import scrapy  # scrapy.Spider is the parent class

class HackerNewsSpider(scrapy.Spider):  # inheriting
    name = "hackernews"           # class variable Scrapy reads
    
    def __init__(self):
        super().__init__()        # call Scrapy's __init__
        self.base_url = "https://hacker-news.firebaseio.com/v0"
    
    def start_requests(self):     # overriding Scrapy's method
        yield scrapy.Request(f"{self.base_url}/topstories.json", 
                             callback=self.parse)
    
    def parse(self, response):    # Scrapy calls this automatically
        # extract data from response
        pass
```

Everything Scrapy does under the hood — concurrency, retry logic, rate limiting, robots.txt — you get for free by inheriting from `scrapy.Spider`. You only define what's specific to Hacker News.

### Pydantic Models — Dataclasses on Steroids

Pydantic (used by FastAPI) is like dataclasses but with built-in validation:

```python
from pydantic import BaseModel

class Article(BaseModel):  # inheriting from BaseModel
    title: str
    author: str
    score: int
    tags: list[str] = []

# Pydantic validates types automatically
a = Article(title="Rust", author="john", score="not_a_number")
# ValidationError: score must be int
```

### FastAPI Routes — Decorators and Classes

```python
from fastapi import FastAPI

app = FastAPI()  # creating an instance of FastAPI class

@app.get("/feed")  # decorator — app.get is a method on the FastAPI instance
async def get_feed(user_id: str):
    # ...
    return recommendations
```

### The DataLakeWriter — Encapsulation

```python
class DataLakeWriter:
    def __init__(self, endpoint, access_key, secret_key):
        self.__access_key = access_key   # private — hide credentials
        self.__secret_key = secret_key
        self._client = self._create_client(endpoint)  # protected
    
    def _create_client(self, endpoint):  # protected — internal detail
        import boto3
        return boto3.client('s3', endpoint_url=endpoint,
                           aws_access_key_id=self.__access_key,
                           aws_secret_access_key=self.__secret_key)
    
    def write(self, path, data):  # public — the only thing outside code uses
        self._client.put_object(Bucket="raw", Key=path, Body=data)
```

Outside code only ever calls `writer.write(path, data)`. The credentials, the client setup, the boto3 details — all hidden.

---

## Quick Reference — Cheat Sheet

```python
# Class definition
class MyClass:
    class_var = "shared"          # class variable

    def __init__(self, x):        # constructor
        self.x = x                # instance variable

    def instance_method(self):    # instance method
        return self.x

    @classmethod
    def class_method(cls):        # class method
        return cls.class_var

    @staticmethod
    def static_method():          # static method
        return "no self needed"

# Inheritance
class Child(MyClass):
    def __init__(self, x, y):
        super().__init__(x)       # call parent constructor
        self.y = y

    def instance_method(self):    # override parent method
        parent_result = super().instance_method()
        return f"{parent_result} + {self.y}"

# Dataclass
from dataclasses import dataclass, field

@dataclass
class Data:
    name: str                              # required
    value: int = 0                         # optional with default
    items: list = field(default_factory=list)  # mutable default

# Access modifiers (convention only)
self.public = "anyone"
self._protected = "be careful"
self.__private = "hands off"
```

---

*Read next: Start Day 2 — Environment Setup & First Spider*
*Reference this doc any time a class concept feels unclear during the build.*