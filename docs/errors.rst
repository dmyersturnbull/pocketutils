
Exceptions and warnings
====================================

Sometimes certain modes of failure are expected (think: checked
exceptions). We want callers to be able to handle and potentially
recover from them, but granularity in exception types and relevant
values are needed. For example, if we couldn’t load a “resource” file,
what was the path? If something was wrong with a database record, what
was its ID? Examples of exceptions defined here are ``LockedError``,
``IncompatibleDataError``, ``HashValidationFailedError``,
``MissingEnvVarError``, ``MultipleMatchesError``, ``AlreadyUsedError``,
and ``IllegalPathError``.

.. code:: python

   import time
   from dscience.core.exceptions import *
   resource = Path('resources/mydata.dat')
   def update_resource():
       if resource.with_suffix('.lockfile').exists():
           raise LockedError('Resource is locked and may be in use.', key=resource)
       # ... do stuff
   try:
       update_resource()
   except LockedError as e:
       if e.key == resource:
           print('{} is locked. Waiting 5s and trying again.'.format(e.key))
           print(e.info())
           time.sleep(5.0)
           update_resource()
       else:
           raise e
