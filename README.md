# fork_map
`fork_map` is like python's builtin `map` function, but uses `os.fork` to execute the mapped
function in child processes. Unlike the builtin multiprocessing map functions, `fork_map` requires only its outputs (not its inputs) to be [pickleable](https://docs.python.org/3/library/pickle.html#what-can-be-pickled-and-unpickled).

```python
from fork_map import fork_map

result = fork_map(lambda x: x*2, range(10))
```

The example above isn't possible with `multiprocessing`'s `Pool.map`, because lambdas aren't pickleable.

## Caveats:
Because `fork_map` uses [`os.fork`](https://docs.python.org/3/library/os.html#os.fork), it has the same limitations as `os.fork`, namely:

- It only works on operating systems where it's available (e.g., not Windows).
- It is **not safe to use** in multithreaded code, because deadlocks may occur. See the warnings on [`os.fork`](https://docs.python.org/3/library/os.html#os.fork) or [this discussion](https://discuss.python.org/t/concerns-regarding-deprecation-of-fork-with-alive-threads/33555) for more information.

I wrote an article explaining the drawbacks to using `os.fork` like this. Read it here:

### [The Power and Danger of os.fork](https://medium.com/@tmrutherford/the-default-method-of-spawning-processes-on-linux-is-changing-in-python-3-14-heres-why-b9711df0d1b1)
