
Introduction / getting started
====================================

To install dscience and its optional packages via pip, run:

.. code:: bash

   pip install dscience[all]

You can avoid installing some dependencies by installing only what you need.
For example:

.. code:: bash

   pip install dscience
   pip install dscience[numeric]

The optional dependency sets are:

- numeric
- db
- jupyter
- test
- extra

You can import the most general-purpose parts of dscience like this:

.. code:: python

   from dscience.full import *
   print(Tools)

This will load:

- ``Tools``, containing various utility functions
- ``Chars``, containing common Unicode characters
- ``abcd``, containing decorators
- ~10 miscellaneous classes, such as ``SmartEnum``
- a collection of exceptions such as ``MultipleMatchesError`` and ``DataWarning``
- numpy as ``np`` and pandas as ``pd``
