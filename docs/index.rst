Pocket Utils
============

.. warning::

    A lot of this documentation is out of date.

.. toctree::
    :maxdepth: 1

    core
    tools
    jupyter
    biochem
    plotting
    misc


Introduction / getting started
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To install pocketutils and its optional packages via pip, run:

.. code:: bash

   pip install pocketutils[all]

You can avoid installing some dependencies by installing only what you need.
For example:

.. code:: bash

   pip install pocketutils
   pip install pocketutils[numeric]

The optional dependency sets are:

- tools
- plotting
- notebooks
- misc

You can import the most general-purpose parts of pocketutils like this:

.. code:: python

   from pocketutils.full import *

   print(Tools)


This will load:

- ``Tools``, containing various utility functions
- ``Chars``, containing common Unicode characters
- ``abcd``, containing decorators
- ~10 miscellaneous classes, such as ``SmartEnum``
- a collection of exceptions such as ``MultipleMatchesError`` and ``DataWarning``
- numpy as ``np`` and pandas as ``pd``
