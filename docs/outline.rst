Functional outline (WIP)
##################

.. todo::

   This document is incomplete.

Product terms
=============
Most input signals used by a macrocell need to be routed through one of the macrocell's five product terms.  A product term computes an 96-in AND, which can be connected to up to 96 signals: 40 signals selected by the current logic block's interconnect switches, the complements of those signals, and the 16 macrocell foldback signals from the current logic block.

There are 96 fuses that control which signals reach the AND gate.  Setting a fuse to 0 enables its corresponding signal, while leaving it at 1 ignores it, though this interpretation breaks down if all the fuses are 1—what is the output of an AND gate with 0 inputs?  A better interpretation that handles this case is that the fuse and signal are OR-ed before being input into the AND gate.  This means that a product term with all fuses set to 1 will always be high.

A product term can be configured to always be low by setting all its fuses to 0.  This works because it's impossible for a signal and its complement to both be high simultaneously.  Unused product terms are normally configured this way.
