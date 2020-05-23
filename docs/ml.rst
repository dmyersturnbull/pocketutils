
Machine learning package
====================================


.. code:: python

   from dscience.ml.confusion_matrix import ConfusionMatrix
   mx = ConfusionMatrix.read_csv('mx.csv')                         # just a subclass of pd.DataFrame
   print(mx.sum_diagonal() - mx.sum_off_diagonal())
   mx = mx.sort(cooling_factor=0.98).symmetrize().triagonalize()   # sort to show block-diagonal structure, plus more
