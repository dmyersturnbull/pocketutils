Core utility classes
====================================

A couple of other things were imported, including ``DevNull``,
``DelegatingWriter``, and ``TieredIterator``.

You can also make a Pandas DataFrame with pretty display and convenience
functions using ``TrivialExtendedDataFrame``.

``LazyWrap`` creates lazy classes, extremely useful in some cases:

.. code:: python

   from datetime import datetime
   from dscience.core import LazyWrap
   def fetch_datetime(): return datetime.now()
   RemoteTime = LazyWrap.new_type('RemoteTime', fetch_datetime)
   now = RemoteTime()
   # nothing happens until now:
   print(now.get())
