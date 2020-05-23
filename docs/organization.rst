
project organization
~~~~~~~~~~~~~~~~~~~~

-  ``dscience.core`` contains code used internally in dscience,
   including some that are useful in their own right
-  ``dscience.tools`` contains the static tool classes like
   ``StringTools``
-  ``dscience.support`` contains data structures and supporting tools,
   such as ``FlexibleLogger``, ``TomlData``, and ``WB1`` (for multiwell
   plates).
-  ``dscience.analysis`` contains algorithms such as ``PeakFinder``
-  ``dscience.biochem`` contains code specific to bioinformatics,
   cheminformatics, etc., such as ``UniprotGoTerms``, ``AtcTree``
-  ``dscience.ml`` contains models for machine learning, including
   ``DecisionFrame`` and ``ConfusionMatrix``
