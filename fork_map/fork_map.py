import os
import typing as tp
import itertools

list_of_tuples = tp.Iterable[tp.Iterable[tp.Any]]
list_of_dicts = tp.Iterable[tp.Mapping[str, tp.Any]]

def fork_map(f: tp.Callable,
            f_args: list_of_tuples=None,
            f_kwargs: list_of_dicts=None,
            nworkers: int=os.cpu_count()):
    '''
    Call function `f` once for each item in `f_args` and `f_kwargs`, using a forked process. If
    both `f_args` and `f_kwargs` are specified, they must be the same length.
    '''


    #chunk f_args and f_kwargs into groups per worker
    asdf
