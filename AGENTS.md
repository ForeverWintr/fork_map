# AGENTS.md

Guidance for coding agents working in this repository.

## What this is

`fork_map` is a small library providing a `map`-like function that runs each call in a child process created with `os.fork`. Unlike `multiprocessing.Pool.map`, only the function's **outputs** (return values and exceptions) need to be pickleable — inputs and the function itself (e.g. lambdas, closures) are inherited by the forked child.

Caveats from the README that constrain any change:
- POSIX only (`os.fork` is unavailable on Windows).
- Not safe in multithreaded programs (fork-with-threads deadlocks).

## Commands

Dependencies and the virtualenv are managed with uv (build backend `uv_build`; dev tools are in the `dev` dependency group, which `uv sync` installs by default).

```sh
uv sync                                          # create .venv, install runtime + dev deps
uv run pytest                                    # run all tests
uv run pytest fork_map/tests/test_fork_map.py::test_exceptions   # single test
uv run ruff check .                              # lint (rules: E, F, UP, B, SIM, I)
uv run mypy fork_map                             # type check
```

`demo.py` contrasts `fork_map` with `Pool.map`; its second half is expected to fail (lambdas aren't pickleable).

## Architecture

All logic lives in `fork_map/fork_map.py`. `fork_map/__init__.py` is empty, so `from fork_map import fork_map` yields the **submodule**, and the function is `fork_map.fork_map(...)` (this is how the tests call it). The README example calls `fork_map(...)` directly, which does not match the current package layout.

Flow of `fork_map(f, iterable, maxworkers=os.cpu_count())`:

1. A single `multiprocessing.Queue` is shared by all children for results.
2. For each item, `_process_in_fork` calls `os.fork()`. The parent gets back a `psutil.Process`; the child runs `f(item)`.
3. In the child, the return value is pickled *inside* the `try` so pickling failures are reported as exceptions rather than crashing the `finally`. Exceptions are pickled too; if an exception itself is unpicklable, it's replaced with an `AttributeError` describing it. The child puts a `_ConcurrentResult(idx, result, exception)` on the queue, then closes the queue and `join_thread()`s it before `os._exit(0)`. The explicit flush is required because `os._exit` skips cleanup; `os._exit` (not `sys.exit`) is used so that callers catching `SystemExit` (e.g. test frameworks) can't keep the child alive.
4. The parent throttles to `maxworkers` live children by polling `psutil.Process.wait(0.01)`.
5. After all children exit, the parent pushes a `None` sentinel, drains the queue, sorts by `idx` to restore input order, and either returns the unpickled results or raises the first (by index) unpickled exception.

`_ConcurrentResult` is defined at module level so it can be pickled. `_has_finished` is a `waitpid(WNOHANG)` helper that is tested but not used by `fork_map` itself.

## Testing notes

Tests fork real processes. Tests like `test_has_finished` fork directly and rely on the child calling `os._exit`; when writing new tests, make sure every forked child exits via `os._exit` so it can't continue running the pytest session.
