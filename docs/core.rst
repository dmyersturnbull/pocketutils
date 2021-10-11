Core utility classes
====================================

A couple of other things were imported, including ``DevNull``,
``DelegatingWriter``, and ``TieredIterator``.

You can also make a Pandas DataFrame with pretty display and convenience
functions using ``TrivialExtendedDataFrame``.

``LazyWrap`` creates lazy classes, extremely useful in some cases:

.. code:: python

   from datetime import datetime
   from pocketutils.core import LazyWrap


   def fetch_datetime():
       return datetime.now()


   RemoteTime = LazyWrap.new_type("RemoteTime", fetch_datetime)
   now = RemoteTime()
   # nothing happens until now:
   print(now.get())


Exceptions and warnings
~~~~~~~~~~~~~~~~~~~~~~~

Sometimes certain modes of failure are expected (think: checked
exceptions). We want callers to be able to handle and potentially
recover from them, but granularity in exception types and relevant
values are needed. For example, if we couldn’t load a “resource” file,
what was the path? If something was wrong with a database record, what
was its ID? Examples of exceptions defined here are ``LockedError``,
``IncompatibleDataError``, ````HashValidationError``,
``MissingEnvVarError``, ``MultipleMatchesError``, ``AlreadyUsedError``,
and ``IllegalPathError``.

.. code:: python

   import time
   from pocketutils.core.exceptions import *

   resource = Path("resources/mydata.dat")


   def update_resource():
       if resource.with_suffix(".lockfile").exists():
           raise LockedError("Resource is locked and may be in use.", key=resource)
       # ... do stuff


   try:
       update_resource()
   except LockedError as e:
       if e.key == resource:
           print(f"{e.key} is locked. Waiting 5s and trying again.")
           print(e.info())
           time.sleep(5.0)
           update_resource()
       else:
           raise e
