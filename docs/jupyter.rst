Jupyter utilities
====================================

``J`` for Jupyter display
~~~~~~~~~~~~~~~~~~~~~~~~~

The class ``J`` has tools for display in Jupyter:

.. code:: python

   from dscience.j import *
   J.red('This is bad.')            # show red text
   if J.prompt('Really delete?'):   # ask the user
       J.bold('Deleting.')

Filling in templates
~~~~~~~~~~~~~~~~~~~~~~~~~

``MagicTemplate`` can build and register a Jupyter magic function that
fills the cell from a template. Ex:

.. code:: python

   import os
   from dscience.support.magic_template import *
   def get_current_resource():
       return 'something dynamic'
   template_text = '''
   # My notebook
   <Write a description here>
   **Datetime:      ${{datetime}}**
   **Hostname:      ${{version}}**
   **Resource name: ${{resource}}**
   '''
   MagicTemplate.from_text(template_text)\
       .add('hostname', os.hostname)\
       .add_datetime()\
       .add('resource', lambda: get_current_resource())\
       .register_magic('mymagic')

Now you can type in ``%mymagic`` to replace with the parsed template.
