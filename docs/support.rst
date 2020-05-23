Support package
====================================

These classes range from common to very obscure.

``PrettyRecordFactory`` makes beautiful aligned log messages.

.. code:: python

   import logging
   from dscience.support.log_format import *
   logger = logging.getLogger('myproject')
   log_factory = PrettyRecordFactory(7, 13, 5).modifying(logger)

Output from an analysis might then be…

::

   [20191228:14:20:06] kale>    datasets      :77    INFO    | Downloading QC-DR...
   [20191228:14:21:01] kale>    __init__      :185   NOTICE  | Downloaded QC-DR with 8 runs, 85 names, and 768 wells.
   [20191229:14:26:04] kale>    __init__      :202   INFO    | Registered new type RandomForestClassifier:n_jobs=4,n_estimators=8000

``TomlData`` is a wrapper around toml dict data.
