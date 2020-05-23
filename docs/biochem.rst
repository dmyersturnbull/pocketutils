
biochem package
====================================

``WB1`` is a multiwell plate with 1-based coordinates (read *well
base-1*).

.. code:: python

   from dscience.biochem.multiwell_plates import WB1
   wb1 = WB1(8, 12)               # 96-well plate
   print(wb1.index_to_label(13))  # prints 'B01'
   for well in wb1.block_range('A01', 'H11'):
       print(well)                # prints 'A01', 'A02', etc.

Getting tissue-specific expression data in humans:

.. code:: python

   from dscience.biochem.tissue_expression import TissueTable
   tissues = TissueTable()
   # returns a Pandas DataFrame of expression levels per cell type per gene for this tissue.
   tissues.tissue('MKNK2')
