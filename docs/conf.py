import sys, os


sys.path.insert(0, os.path.abspath('.') + '/_extensions')


project = 'Project Bureau'
copyright = '2019-2020, whitequark'

master_doc = 'index'

rst_epilog = """
.. |o| raw:: html

      <i class="fa fa-times" style="display:block;text-align:center;color:darkred;"></i>

.. |x| raw:: html

      <i class="fa fa-check" style="display:block;text-align:center;color:green;"></i>

.. |-| raw:: html

      <i class="fa fa-minus" style="display:block;text-align:center;"></i>
"""

extensions = [
    'sphinx.ext.todo',
    'sphinx_rtd_theme',
    'sphinxarg.ext',
    'sphinx_prjbureau',
]

todo_include_todos = True

templates_path = ['_templates']

html_theme = 'sphinx_rtd_theme'
html_static_path = ["_static"]
html_css_files = ["custom.css"]
