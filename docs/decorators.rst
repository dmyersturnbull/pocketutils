
Decorators
====================================

The ``abcd`` package has useful decorators. For example, output timing
info:

.. code:: python

   from dscience.full import *
   @abcd.takes_seconds
   def slow_fn():
       for _ in range(1000000): pass
   slow_fn()  # prints 'Done. Took 23s.'

Or for an immutable class with nice ``str`` and ``repr``:

.. code:: python

   from dscience.full import *
   @abcd.auto_repr_str()  # can also set 'include' or 'exclude'
   @abcd.immutable
   class CannotChange:
       def __init__(self, x: str):
           self.x = x
   obj = CannotChange('sdf')
   print('obj')  # prints 'CannotChange(x='sdf')
   obj.x = 5  # breaks!!
