Naming conventions
##################

A CPLD, from the point of view of a place & route tool, consists mostly of named networks connected to each other through named buffers. Clearly, consistent and straightforward naming is very important for such tools. Unfortunately, the vendor's naming is neither.

This project always picks clarity and consistency over matching the vendor's naming, even for names that appear in the datasheet. When reading this document, always refer to the pinout in the :doc:`database explorer <explore>`; for example, take a look at the `ATF1502AS pinout <explore.html#/ATF1502AS/pad.html>`__.

Logic blocks
============

A *logic block* is a group of 16 macrocells and 40 interconnect switches. They are called ``A``, ``B``, ... up to ``H`` in the highest density device.

.. _n-mc:

Macrocells
==========

A *macrocell* is the fundamental logic unit of a CPLD. They are called ``MC1``, ``MC2``, ... up to ``MC128`` in the highest density device. Even though every macrocell belongs to a logic block, macrocell names are globally unique.

.. _n-pt:

Product terms
=============

Each macrocell ``MCx`` has five associated *product terms*, ``PT1``, ``PT2``, ... ``PT5``. Product term names repeat in every macrocell. Any product term on the device can be uniquely identified by its full name ``MCx.PTy``.

.. _n-fb:

Feedback signals
================

Each macrocell ``MCx`` uses either its combinatorial function or its storage element to drive a *feedback signal* ``MCx_FB``. Like macrocell names, feedback signal names are globally unique.

.. _n-flb:

Foldback signals
================

Each macrocell ``MCx`` may use its ``PT1`` product term to drive a *foldback signal* ``MCx_FLB``. Like macrocell names, foldback signal names are globally unique.

.. _n-uim:

Interconnect switches
=====================

An *interconnect switch* (also called a logic block switch) is the fundamental routing unit of a CPLD. They are called ``UIM1``, ``UIM2``, ... up to ``UIM320`` in the highest density device, and drive networks with the same name. Even though every interconnect switch belongs to a block, interconnect switch names are globally unique.

The inputs of interconnect switches are driven by the :ref:`input/feedback bus <n-gbus>`.

.. _n-gnet:

Global switches
===============

A *global switch* is functionally similar to an interconnect switch. All devices have the same set of global switches. They are called ``GCLR``, ``GCLK1``, ``GCLK2``, ``GCLK3``, ``GOE1``, ``GOE2``, ... up to ``GOE6``, and drive networks with the same name.

The inputs of global switches are driven by the :ref:`input/feedback bus <n-gbus>`.

.. warning::

   Global networks ``GCLR``, ``GCLK1``, ``GOE1``, etc., should not be confused with special pins **CLR**, **CLK1**, **OE1**, etc.! They are distinct device elements that occupy different namespaces.

.. note::

   While these names can be confusing, they're less confusing than the names assigned in the datasheet, where the global clock networks are called ``GCK[0..2]`` and the special functions are called ``GCLK[1..3]``.

.. _n-pins:

Pins, pads, and specials
========================

While most pins of ATF15xx CPLDs are straightforwardly attached to their macrocell, dedicated inputs, special functions, and differences in pinouts introduce considerable complexity. A particular physical pin can have as many as three different names: a *pad name*, a *pin name*, and a *special name*.

A *pad name* refers to a particular bonding pad on the die. Every logic pin corresponds to a unique pad name. However, a pad is not necessarily connected to a pin: ATF1504 and higher density devices have packages where some pads are not connected. For every macrocell ``MCx``, the device has a pad called ``Mx``; in addition, for the dedicated clear, clock, and output enable inputs, the device has four pads called ``R``, ``C1``, ``C2``, and ``E1``.

A *pin name* refers to a particular pin on the package. Except for power pins, every pin is always connected to a pad. Because pin numbering completely changes depending on the package, pin names only appear in the user interface; everywhere else, pad names are used as canonical identifiers.

A *special name* refers to a particular pad by its function. Some special functions are fixed: pad ``R`` always has special name **CLR**, and pad ``C2`` always has special names **CLK2** and **OE2**; most special functions differ between devices.

.. warning::

   Global networks ``GCLR``, ``GCLK1``, ``GOE1``, etc., should not be confused with special pins **CLR**, **CLK1**, **OE1**, etc.! They are distinct device elements that occupy different namespaces.

   For example, on ATF1502, the pad ``E1``, which has the special name **OE1**, `cannot be routed <explore.html#/ATF1502AS/gsw.html#GOE1>`__ to the ``GOE1`` network at all.

Most device options are related to a macrocell or a global input, in which case they naturally use pad names to refer to logic pins. A few options (e.g. `TDI <explore.html#/ATF1502AS/pin.html#TDI>`__ and `TMS <explore.html#/ATF1502AS/pin.html#TMS>`__ pullups, as well as one of the global clock inputs) are defined only in terms of special functions, though.

.. _n-pad:

Input signals
=============

Each pad ``Px`` uses its input buffer to drive an input signal ``Px_PAD``. Like pad names, input signal names are globally unique.

.. _n-gbus:

Input/feedback bus
==================

Two kinds of signals (besides the :ref:`global networks <n-gnet>`) are routed throughout the entire device: :ref:`input signals <n-pad>` (``Px_PAD``) and :ref:`feedback signals <n-fb>` (``MCy_FB``). Together, they are called the *input/feedback bus*, and each of the :ref:`interconnect <n-uim>` and :ref:`global <n-gnet>` switches selects one of these signals (or a logic low).
