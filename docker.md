# Docker — Complete Understanding

> *"How do people even know to write this from scratch?"*
> The answer at the end. Read everything first.

---

## Table of Contents

1. [The Problem Docker Solves](#1-the-problem-docker-solves)
2. [The Core Concepts — Mental Model First](#2-the-core-concepts--mental-model-first)
3. [Docker Image — The Blueprint](#3-docker-image--the-blueprint)
4. [Docker Container — The Running Thing](#4-docker-container--the-running-thing)
5. [Dockerfile — How You Build an Image](#5-dockerfile--how-you-build-an-image)
6. [Docker Compose — Running Multiple Containers Together](#6-docker-compose--running-multiple-containers-together)
7. [How a docker-compose.yml is Structured](#7-how-a-docker-composeyml-is-structured)
8. [Networking in Docker Compose](#8-networking-in-docker-compose)
9. [Volumes — Persisting Data](#9-volumes--persisting-data)
10. [Environment Variables in Docker](#10-environment-variables-in-docker)
11. [The Mindful docker-compose.yml — Explained Line by Line](#11-the-mindful-docker-composeyml--explained-line-by-line)
12. [How Do People Know to Write This From Scratch?](#12-how-do-people-know-to-write-this-from-scratch)
13. [Essential Docker Commands](#13-essential-docker-commands)

---

## 1. The Problem Docker Solves

Before Docker, deploying software was a nightmare summarized in one sentence that every developer has said:

> **"It works on my machine."**

Here's why that happens. Your Python app depends on:
- Python 3.11 specifically
- A specific version of every library in `requirements.txt`
- System libraries like `libpq` for Postgres, `libxml2` for parsing
- Environment variables set a certain way
- A specific OS (sometimes)

Your machine has all of that set up correctly. Your teammate's machine has Python 3.9, different library versions, different system libraries. The server in production runs Ubuntu, your machine runs macOS. Nothing matches. Everything breaks.

**Docker's solution:** Package the application *and its entire environment* together into one unit that runs identically everywhere. Your machine, your teammate's machine, a server in a data center — doesn't matter. Same container, same behavior, every time.

Think of it like a shipping container. Before shipping containers existed, loading a ship was chaos — every item was different, needed different handling. The shipping container standardized everything. You put your stuff in a container, and the ship, truck, and crane don't care what's inside — they just move the container. Docker does this for software.

---

## 2. The Core Concepts — Mental Model First

There are four things to understand. Get these four right and everything else follows.

```
Dockerfile  →  (build)  →  Image  →  (run)  →  Container
```

**Dockerfile** — A text file. A recipe. Instructions for building an image.

**Image** — A snapshot. A frozen, read-only package of an application and everything it needs. Like a `.iso` file for an OS, or an `.apk` for an Android app. You build it once, distribute it, run it anywhere.

**Container** — A running instance of an image. Like how a process is a running instance of a program. You can run 10 containers from the same image simultaneously — they're all identical but completely isolated from each other.

**Docker Compose** — A tool for defining and running *multiple containers* together as a single application. Mindful needs MinIO, Redis, and RedisInsight all running at once. Docker Compose starts all of them with one command.

---

## 3. Docker Image — The Blueprint

An image is a layered, read-only filesystem snapshot. Every instruction in a Dockerfile adds a new layer on top of the previous one.

```
Layer 4:  COPY . /app          ← your application code
Layer 3:  RUN pip install...   ← your Python dependencies
Layer 2:  RUN apt-get install  ← system packages
Layer 1:  FROM python:3.11     ← base OS + Python runtime
```

This layering is clever for two reasons:

**Caching** — Docker caches each layer. If you rebuild an image and only your code changed (Layer 4), Docker reuses Layers 1, 2, and 3 from cache. Only Layer 4 gets rebuilt. This makes rebuilds fast.

**Sharing** — If you have 10 images all based on `python:3.11`, they all share the same base layer in storage. Not 10 copies — 1 copy shared by all.

### Where Images Come From

**Docker Hub** — The public registry. Like npm for Docker. When you write `FROM python:3.11` in a Dockerfile, Docker pulls the official Python image from Docker Hub. MinIO, Redis, PostgreSQL — all have official images there.

**You build them** — When you write a Dockerfile and run `docker build`, you create your own image locally.

**You push them** — You can push your image to Docker Hub or a private registry so others (or a server) can pull and run it.

For Mindful, we don't build custom images for MinIO and Redis — we use their official images directly. We only write a Dockerfile for our own Python application.

---

## 4. Docker Container — The Running Thing

A container is what you actually interact with day-to-day. It's a running process that thinks it's on its own computer — it has its own filesystem, its own network interface, its own process list — but it's sharing the host machine's kernel.

**Container vs Virtual Machine:**

| | Virtual Machine | Container |
|---|---|---|
| Startup time | Minutes | Seconds |
| Size | Gigabytes | Megabytes |
| Isolation | Full OS | Process-level |
| Overhead | High | Very low |

A VM runs a full operating system inside another operating system. A container shares the host OS kernel and only isolates the process. Much lighter, much faster.

### Container Lifecycle

```
docker pull redis        ← download the image
docker run redis         ← create and start a container from it
docker stop <id>         ← stop the container (process stops, data preserved)
docker start <id>        ← start it again (data still there)
docker rm <id>           ← delete the container (data gone unless using volumes)
```

**Key insight:** Containers are ephemeral by default. If you delete a container, everything inside it is gone. This is why volumes exist — to persist data outside the container.

---

## 5. Dockerfile — How You Build an Image

A Dockerfile is a plain text file named exactly `Dockerfile` (no extension). Every line is an instruction. Docker reads them top to bottom and builds a layer for each one.

### The Instructions You'll Use

**`FROM`** — Every Dockerfile starts with this. Sets the base image you're building on top of.
```dockerfile
FROM python:3.11-slim
```
`python:3.11-slim` is the official Python image, slim variant (smaller size, fewer pre-installed tools). Always pin a specific version — never use `FROM python:latest` because "latest" changes and your build breaks without warning.

**`WORKDIR`** — Sets the working directory inside the container for all following instructions. Creates the directory if it doesn't exist.
```dockerfile
WORKDIR /app
```
After this, all paths are relative to `/app`.

**`COPY`** — Copies files from your machine into the image.
```dockerfile
COPY requirements.txt .        # copy requirements.txt into /app/
COPY . .                       # copy everything into /app/
```
Why copy `requirements.txt` separately before copying everything? Because of layer caching. If requirements.txt hasn't changed, the `pip install` layer gets reused from cache even if your code changed. Smart ordering = fast rebuilds.

**`RUN`** — Executes a command during the image build. Used to install dependencies, create directories, set permissions.
```dockerfile
RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y curl
```
Combine related commands with `&&` to keep them in one layer — fewer layers = smaller image.

**`ENV`** — Sets environment variables inside the container.
```dockerfile
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
```
`PYTHONUNBUFFERED=1` means Python output appears in logs immediately, not buffered. Always set this.

**`EXPOSE`** — Documents which port the container listens on. Doesn't actually open the port — that happens at runtime. It's documentation.
```dockerfile
EXPOSE 8000
```

**`CMD`** — The default command to run when the container starts. Only one CMD per Dockerfile (last one wins).
```dockerfile
CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**`ENTRYPOINT`** — Like CMD but harder to override. CMD arguments get appended to ENTRYPOINT. Not commonly needed for simple projects.

### A Complete Dockerfile for Mindful's API

```dockerfile
# Start from official Python 3.11 slim image
FROM python:3.11-slim

# Set working directory inside container
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies (if any)
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Document the port
EXPOSE 8000

# Start the API server
CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Building and Running This Dockerfile

```bash
docker build -t mindful-api .        # build image, tag it "mindful-api"
docker run -p 8000:8000 mindful-api  # run it, map port 8000
```

`-p 8000:8000` means "connect port 8000 on my machine to port 8000 inside the container." Without this, the container's port is unreachable from outside.

---

## 6. Docker Compose — Running Multiple Containers Together

Mindful is not one thing — it's MinIO, Redis, RedisInsight, and eventually your Python services all running together. Managing each container manually with `docker run` would be:

```bash
docker run -d -p 9000:9000 -p 9001:9001 \
  -e MINIO_ROOT_USER=admin \
  -e MINIO_ROOT_PASSWORD=password \
  -v minio_data:/data \
  --name minio \
  minio/minio server /data --console-address ":9001"

docker run -d -p 6379:6379 --name redis redis:7-alpine

docker run -d -p 8001:8001 --name redisinsight \
  --link redis:redis \
  redislabs/redisinsight
```

That's already unwieldy with just three services. And you have to remember to start them in the right order. And when you shut down, you stop each one manually. And what about networking between them?

**Docker Compose solves all of this.** You describe all your services in one `docker-compose.yml` file and then:

```bash
docker compose up      # start everything
docker compose down    # stop and remove everything
docker compose logs    # see logs from all services
```

One file. One command. Everything starts, networked together, with the right configuration.

---

## 7. How a docker-compose.yml is Structured

A `docker-compose.yml` is written in YAML — indentation matters, use 2 spaces (never tabs).

The top-level structure:

```yaml
services:       # define your containers here
  service1:
    ...
  service2:
    ...

volumes:        # define persistent storage here
  volume1:
  volume2:

networks:       # define custom networks (optional, compose creates a default)
  network1:
```

### Service Configuration Keys

For each service, the most important keys are:

**`image`** — Which Docker image to use. Pulled from Docker Hub if not local.
```yaml
image: redis:7-alpine
```

**`build`** — Build from a Dockerfile instead of pulling an image.
```yaml
build:
  context: .          # where to find the Dockerfile
  dockerfile: Dockerfile
```

**`ports`** — Map host ports to container ports. Format: `"host:container"`
```yaml
ports:
  - "6379:6379"      # localhost:6379 → container:6379
  - "9000:9000"
```

**`environment`** — Set environment variables inside the container.
```yaml
environment:
  MINIO_ROOT_USER: admin
  MINIO_ROOT_PASSWORD: password123
```

**`env_file`** — Load environment variables from a file (your `.env`).
```yaml
env_file:
  - .env
```

**`volumes`** — Mount storage into the container.
```yaml
volumes:
  - minio_data:/data           # named volume
  - ./config:/app/config       # bind mount (local folder → container folder)
```

**`depends_on`** — Start this service only after another is running.
```yaml
depends_on:
  - redis
  - minio
```

**`command`** — Override the default CMD from the Dockerfile.
```yaml
command: server /data --console-address ":9001"
```

**`restart`** — What to do if the container crashes.
```yaml
restart: unless-stopped    # restart always except when you manually stop it
```

**`healthcheck`** — How Docker knows the service is actually ready (not just started).
```yaml
healthcheck:
  test: ["CMD", "redis-cli", "ping"]
  interval: 10s
  timeout: 5s
  retries: 5
```

---

## 8. Networking in Docker Compose

This is the part that confuses people most. Here's the key insight:

**When you use Docker Compose, all services are automatically on the same network and can reach each other by their service name.**

That means inside your Python code running in a container, you don't connect to Redis at `localhost:6379`. You connect to `redis:6379` — where `redis` is the service name you defined in `docker-compose.yml`.

```yaml
services:
  redis:           # ← this name becomes the hostname
    image: redis:7-alpine
    ports:
      - "6379:6379"

  my-app:
    build: .
    environment:
      REDIS_URL: redis://redis:6379    # "redis" resolves to the redis container
```

From your laptop (outside containers), you connect to `localhost:6379` because of the port mapping. From inside a container, you connect to `redis:6379` because of Docker's internal DNS.

This is a common source of confusion. Two different addresses for the same Redis:
- **From your laptop:** `localhost:6379`
- **From inside a container:** `redis:6379`

---

## 9. Volumes — Persisting Data

By default, when a container stops or is deleted, everything inside it is gone. For a database or file storage system, that's catastrophic. Volumes solve this.

### Named Volumes

Docker manages the storage. Data lives on your host machine in a Docker-managed location. The volume persists even when the container is deleted.

```yaml
services:
  minio:
    image: minio/minio
    volumes:
      - minio_data:/data    # mount named volume "minio_data" at /data inside container

volumes:
  minio_data:               # declare the named volume here
```

Delete the MinIO container → volume still exists → start a new MinIO container with the same volume → all your data is back.

### Bind Mounts

Mount a specific folder from your host machine into the container. Changes on either side are immediately reflected on the other.

```yaml
volumes:
  - ./config:/app/config    # your local ./config folder → /app/config in container
  - ./logs:/app/logs        # useful for seeing logs outside the container
```

Useful for development — mount your code into the container so you don't have to rebuild the image every time you change a line.

---

## 10. Environment Variables in Docker

Never hardcode secrets in a Dockerfile or docker-compose.yml — those get committed to git. Use environment variables loaded from your `.env` file.

Your `.env` file (never committed, in `.gitignore`):
```
MINIO_ROOT_USER=admin
MINIO_ROOT_PASSWORD=supersecret
REDIS_PASSWORD=anothersecret
```

Your `docker-compose.yml` references it:
```yaml
services:
  minio:
    image: minio/minio
    env_file:
      - .env
```

Docker reads `.env` and injects those variables into the container's environment. Your Python code reads them with `os.getenv()` or `python-dotenv`.

---

## 11. The Mindful docker-compose.yml — Explained Line by Line

```yaml
# Docker Compose file format version
# (version key is optional in modern Docker Compose but good to know)

services:

  # ── MinIO — our S3-compatible data lake ──────────────────────────────────
  minio:
    image: minio/minio:latest         # official MinIO image from Docker Hub
    container_name: mindful-minio     # give it a readable name
    command: server /data --console-address ":9001"
    # "server /data" starts MinIO serving files from /data
    # "--console-address :9001" starts the web UI on port 9001
    ports:
      - "9000:9000"    # S3 API — your Python code talks to this
      - "9001:9001"    # MinIO web console — you open this in browser
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER}         # read from .env
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD} # read from .env
    volumes:
      - minio_data:/data    # persist all files here
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 10s
      retries: 3

  # ── Redis — our message broker and cache ─────────────────────────────────
  redis:
    image: redis:7-alpine    # alpine = tiny linux, much smaller image
    container_name: mindful-redis
    ports:
      - "6379:6379"          # standard Redis port
    volumes:
      - redis_data:/data     # persist Redis data (streams, cached scores)
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      # redis-cli ping returns "PONG" if Redis is healthy
      interval: 10s
      timeout: 5s
      retries: 5

  # ── RedisInsight — visual UI to see what's in Redis ──────────────────────
  redisinsight:
    image: redis/redisinsight:latest
    container_name: mindful-redisinsight
    ports:
      - "5540:5540"          # open localhost:5540 in browser
    depends_on:
      redis:
        condition: service_healthy    # wait until Redis passes healthcheck
    restart: unless-stopped

# ── Named volumes declaration ─────────────────────────────────────────────
volumes:
  minio_data:      # Docker manages where this actually lives on your machine
  redis_data:
```

### What You'll See After `docker compose up`

- `localhost:9001` → MinIO web console (login with your .env credentials)
- `localhost:6379` → Redis (connect from Python with `redis-py`)
- `localhost:5540` → RedisInsight (visual Redis browser)

---

## 12. How Do People Know to Write This From Scratch?

This is the real question. The honest answer is: **they don't write it from scratch. Nobody does.**

Here's what actually happens:

**Step 1 — Read the official image docs**
Every image on Docker Hub has a documentation page that shows you exactly how to run it. MinIO's Docker Hub page shows you the exact `docker run` command with all the environment variables and volume mounts. You translate that into `docker-compose.yml` syntax. That's it.

**Step 2 — Know the docker-compose.yml structure**
Once you know that services, ports, volumes, environment, depends_on, and healthcheck exist and what they do — you can read any docker-compose.yml and write your own. The structure is always the same. This doc just taught you that.

**Step 3 — Copy, understand, modify**
Nobody writes Docker configs from memory. They find a working example, read it until they understand every line, then modify it for their needs. The difference between a beginner and an experienced developer is not that the experienced one memorized it — it's that the experienced one knows which parts to look up and what to look for.

**Step 4 — Official docs and Docker Hub are enough**
For 90% of common services, the official Docker Hub page gives you everything. MinIO, Redis, PostgreSQL, Elasticsearch — all have comprehensive examples. You combine what they give you with the structure in this doc and you have a working compose file.

**The real secret:** Experience with Docker is just having seen enough images and compose files that the patterns become familiar. After you write the Mindful compose file, you'll find every future compose file easier because the concepts are the same. It's pattern recognition, not memorization.

---

## 13. Essential Docker Commands

```bash
# ── Images ────────────────────────────────────────────────────────────────
docker images                     # list all local images
docker pull redis:7-alpine        # download an image
docker rmi redis:7-alpine         # delete an image
docker build -t my-app .          # build image from Dockerfile in current dir

# ── Containers ────────────────────────────────────────────────────────────
docker ps                         # list running containers
docker ps -a                      # list all containers (including stopped)
docker run redis                  # create and start a container
docker run -d redis               # run in background (detached)
docker run -d -p 6379:6379 redis  # run with port mapping
docker stop <id or name>          # stop a container
docker start <id or name>         # start a stopped container
docker rm <id or name>            # delete a container
docker logs <id or name>          # see container logs
docker exec -it <id> bash         # open a shell inside a running container

# ── Docker Compose ────────────────────────────────────────────────────────
docker compose up                 # start all services (foreground)
docker compose up -d              # start all services (background)
docker compose down               # stop and remove all containers
docker compose down -v            # also delete volumes (wipes all data)
docker compose logs               # see logs from all services
docker compose logs redis         # see logs from one service
docker compose ps                 # see status of all services
docker compose restart redis      # restart one service
docker compose build              # rebuild images without starting

# ── Cleanup ───────────────────────────────────────────────────────────────
docker system prune               # remove all stopped containers, unused images
docker volume prune               # remove all unused volumes
```

---

*Reference this doc any time something in docker-compose.yml is unclear.*
*Next: Write the actual Mindful docker-compose.yml and get MinIO + Redis running.*