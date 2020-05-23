Tools package
====================================

The ``Tools`` class has various small utility functions:

.. code:: python

   def fn_to_try():
       raise ValueError('')
   from dscience.full import *
   Tools.git_description('.').tag                # the tag, or None
   Tools.ms_to_minsec(7512000)                   # '02:05:12'
   Tools.fix_greek('beta,eta and Gamma')         # 'β,η and Γ'
   Tools.pretty_function(lambda s: 55)           # '<λ(1)>'
   Tools.pretty_function(list)                   # '<list>'
   Tools.strip_paired_brackets('(ab[cd)')   # 'ab[cd'
   Tools.iceilopt(None), Tools.iceilopt(5.3)     # None, 6
   Tools.succeeds(fn_to_try)                     # True or False
   Tools.or_null(fn_to_try)                      # None if it failed
   Tools.only([1]), Tools.only([1, 2])           # 1, MultipleMatchesError
   Tools.is_probable_null(np.nan)                # True
   Tools.read_properties_file('abc.properties')  # returns a dict
   important_info = Tools.get_env_info()         # a dict of info like memory usage, cpu, host name, etc.

``Chars`` contains useful Unicode characters that are annoying to type,
plus some related functions:

.. code:: python

   from dscience.full import *
   print(Chars.hairspace)             # hair space
   print(Chars.range(1, 2))           # '1–2' (with en dash)


``Tools`` actually subclasses from several Tools-like classes. You can
import only the ones you want instead:

.. code:: python

   from dscience.tools.path_tools import PathTools
   print(PathTools.sanitize_file_path('ABC|xyz'))  # logs a warning & returns 'ABC_xyz'
   print(PathTools.sanitize_file_path('COM1'))     # complains!! illegal path on Windows.
   from dscience.tools.console_tools import ConsoleTools
   if ConsoleTools.prompt_yes_no('Delete?'):
       #  Takes 10s, writing Deleting my_dir.......... Done.
       ConsoleTools.slow_delete('my_dir', wait=10)
