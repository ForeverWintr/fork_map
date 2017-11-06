import os
from multiprocessing import Queue
import typing as tp
import itertools
from collections import namedtuple
import functools


# Result tuple to be sent back from workers. Defined at module level for ease of pickling
_ConcurrentResult = namedtuple('_ConcurrentResult', 'index result call_state_data exception location')


def _process_in_fork(idx, func, result_q, args, kwargs):
    '''Call `func` in a child process. This function returns the ID of the child
    in the parent process, while the child process calls _call_function, puts the results in
    the provided queues, then exits.
    '''
    pid = os.fork()
    if pid:
        return pid

    #here we are the child
    make_result = functools.partial(_ConcurrentResult,
                                    result=None,
            exception=None,
            index=idx,
            call_state_data=None,
            location='',
            )

    result = None
    try:
        r = func(*args, **kwargs)

        #pickle here, so that we can't crash with pickle errors in the finally clause
        pickled_r = pickle.dumps(r)
        data = pickle.dumps(kwargs['call_state'].data)
        result = make_result(result=pickled_r, call_state_data=data)
    except Exception as e:
        try:
            # In case func does something stupid like raising an unpicklable exception
            pickled_exception = pickle.dumps(e)
        except AttributeError:
            pickled_exception = pickle.dumps(
                AttributeError(f'Unplicklable exception raised in {func}'))
        result = make_result(exception=pickled_exception,
                             location=kwargs['call_state'].highlight_active_function())
    finally:
        result_q.put(result)
        # it's necessary to explicitly close the result_q and join its background thread here,
        # because the below os._exit won't allow time for any cleanup.
        result_q.close()
        result_q.join_thread()

        # This is the one place that the python docs say it's normal to use os._exit. Because
        # this is executed in a child process, calling sys.exit can have unintended
        # consequences. e.g., anything above this that catches the resulting SystemExit can
        # cause the child process to stay alive. the unittest framework does this.
        os._exit(0)


def _has_finished(pid):
    '''Return true if the process identified by pid has finished, false otherwise'''
    if os.waitpid(pid, os.WNOHANG) == (0, 0):
        return False
    return True


def fork_map(f: tp.Callable,
             iterable: tp.Iterable,
             maxworkers: int=os.cpu_count()):
    '''
    Call function `f` once for each item in iterable, using forked processes.

    Args:
        maxworkers: limit the number of forked processes.
    '''
    if maxworkers < 1:
        raise ValueError('maxworkers must be >= 1')

    result_q = Queue()
    children = []
    for i, item in enumerate(iterable):
        child_pid = _process_in_fork(i, f, result_q, (item, ), {})
        children.append(child_pid)
        while len(children) == maxworkers:
            #wait for a child to finish before forking again
            exited = []
            for cpid in children:

                asdf
