import os

pid = os.fork()
if pid:
    print('I am the parent')
else:
    print('I am the child')
