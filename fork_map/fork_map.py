import functools
import os
import pickle
import typing as tp
from collections import namedtuple
from multiprocessing import Queue
from operator import itemgetter

import psutil

# Result tuple to be sent back from workers. Defined at module level for ease of pickling
_ConcurrentResult = namedtuple("_ConcurrentResult", ["index", "result", "exception"])


def _process_in_fork(
    idx: int,
    func: tp.Callable[..., tp.Any],
    result_q: Queue[_ConcurrentResult],
    args: tp.Iterable[tp.Any],
    kwargs: dict[str, tp.Any],
) -> psutil.Process | tp.NoReturn:
    """Call `func` in a child process. This function returns the ID of the child
    in the parent process, while the child process calls _call_function, puts the results in
    the provided queue, then exits.
    """
    pid = os.fork()
    if pid:
        return psutil.Process(pid)

    # here we are the child
    make_result = functools.partial(
        _ConcurrentResult,
        result=None,
        exception=None,
        index=idx,
    )

    result = None
    try:
        r = func(*args, **kwargs)

        # pickle here, so that we can't crash with pickle errors in the finally clause
        pickled_r = pickle.dumps(r)
        result = make_result(result=pickled_r)
    except Exception as e:
        try:
            # In case func does something stupid like raising an unpicklable exception
            pickled_exception = pickle.dumps(e)
        except AttributeError:
            pickled_exception = pickle.dumps(
                AttributeError(f'{func} raised unpicklable exception "{e!r}"')
            )
        result = make_result(exception=pickled_exception)
    finally:
        result_q.put(result)
        # it's necessary to explicitly close the result_q and join its background thread here,
        # because the below os._exit won't allow time for any cleanup.
        result_q.close()
        result_q.join_thread()

        # This is the one place that the python docs say it's normal to use os._exit. Because this
        # is executed in a child process, calling sys.exit can have unintended consequences. e.g.,
        # anything above this that catches the resulting SystemExit (e.g., the unittest framework)
        # can cause the child process to stay alive.
        os._exit(0)


def _has_finished(pid):
    """Return true if the process identified by pid has finished, false otherwise"""
    if os.waitpid(pid, os.WNOHANG) == (0, 0):
        return False
    return True


def fork_map(f: tp.Callable, iterable: tp.Iterable, maxworkers: int = os.cpu_count()):
    """
    Call function `f` once for each item in iterable, using forked processes.

    Args:
        maxworkers: limit the number of forked processes.
    """
    if maxworkers < 1:
        raise ValueError("maxworkers must be >= 1")

    result_q = Queue()

    children = []
    for i, item in enumerate(iterable):
        child = _process_in_fork(i, f, result_q, (item,), {})
        children.append(child)

        while len(children) == maxworkers:
            # wait for a child to finish before forking again
            exited = []
            for c in children:
                try:
                    c.wait(0.01)
                except psutil.TimeoutExpired:
                    pass
                else:
                    exited.append(c)
            children = [c for c in children if c not in exited]

    # the parent waits for all children to complete
    for c in children:
        c.wait()

    results = []
    # iterate over the result q in sorted order
    result_q.put(None)
    for r in sorted(iter(result_q.get, None), key=itemgetter(0)):
        if r.exception:
            raise pickle.loads(r.exception)
        results.append(pickle.loads(r.result))
    return results
