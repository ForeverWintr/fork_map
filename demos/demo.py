from fork_map import fork_map

result = fork_map(lambda x: x * 2, range(5))
print(result)

## -----------------------------------

from multiprocessing.pool import Pool

# This fails, as lambdas aren't pickleable.
with Pool() as p:
    result = p.map(lambda x: x * 2, range(5))

print(result)
