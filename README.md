# fork_map
`fork_map` is like python's builtin `map` function, but uses `os.fork` to execute the mapped
function in child processes. Unlike the builtin multiprocessing map functions, `fork_map` requires only its outputs (not its inputs) to be [pickleable](https://docs.python.org/3/library/pickle.html#what-can-be-pickled-and-unpickled).

```python
from fork_map import fork_map

result = fork_map(lambda x: x*2, range(10))
```