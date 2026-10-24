# Async Web Crawler

An asynchronous web crawler built with Python, `asyncio`, and `aiohttp`.

The project is developed in 7 stages, gradually introducing HTML parsing, concurrency control, error handling, rate limiting, and data storage.

## Day 1 — Async HTTP Client

Implemented features:
- Asynchronous HTTP requests using `aiohttp`
- Concurrent URL fetching with `asyncio.gather()`
- Concurrency limiting with `asyncio.Semaphore`
- HTTP connection pooling with `ClientSession`
- Timeout and HTTP error handling
- Request logging and execution time measurement
- Basic asynchronous tests with `pytest`

## Tech Stack

Python 3.12, asyncio, aiohttp, pytest, pytest-asyncio.

## Installation

```bash
python -m venv .venv
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

## Tests

```bash
python -m pytest tests/ -v
```

## Roadmap

- [x] Day 1 — Async HTTP Client
- [ ] Day 2–7 — Further crawler development
