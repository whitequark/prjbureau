-m util.fuseconv
################

.. argparse::
   :ref: util.fuseconv.arg_parser
   :prog: python3 -m util.fuseconv

Examples
========

To prepare a JED file emitted by the fitter for flashing:

.. code-block:: console

   $ python3 -m util.fuseconv design.jed design.svf

To convert the resulting SVF file back to a fuse map:

.. code-block:: console

   $ python3 -m util.fuseconv design.svf design.jed
