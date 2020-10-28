Database schema
###############

The ATF15xx chip database is the ultimate artefact produced by Project Bureau. Most importantly, it assigns a symbolic name to each known fuse or group of fuses and a symbolic value to each known pattern these fuses can take. Aside from that, it establishes relationships between basic elements: macrocells and logic blocks, macrocells and pins, pads and special functions.

The canonical form of the chip database distributed by the project is its `JSON serialization <database/database.json.gz>`_. A machine-readable `JSON schema <database/schema.json>`_ that describes the chip database structure is also available. The rest of this document contains a human-readable description of the chip database format.

General structure
=================

The chip database contains two kinds of entries: nodes and leaves. A *node* is a container (object or array) that may include other nodes and leaves. A *leaf* is an arbitrary data structure describing a feature of the device, e.g. the location of a fuse in a JED file plus its symbolic description. The chip database only uses a small amount of different leaf structures, which are described below.

.. _leaf-reference:

Reference leaf
--------------

Example: ``"M0"``.

The reference leaf links a single node to the node it's in. It is a string containing the name of the linked node.

Sequence leaf
-------------

Example: ``["MC1", "MC2"]``.

The sequence leaf links an ordered set of nodes to the node it's in. It is an array of :ref:`references <leaf-reference>`.

Mapping leaf
------------

Example: ``{"M1": "42", "M2": "43"}``.

The mapping leaf describes a one-to-one correspondence between nodes. It is an object containing :ref:`references <leaf-reference>` where the keys are also :ref:`references <leaf-reference>`.

Range leaf
----------

Example: ``[100, 200]``.

The range leaf describes a contiguous sequence of fuse indexes. It is an array containing two integers: the inclusive lower bound and the exclusive upper bound.

Xpoints leaf
------------

Example: ``{"UIM2_P": 16, "UIM2_N": 17}``.

The crosspoints leaf describes a one-to-one correspondence between networks and fuse offsets. It is an object containing integer fuse offsets where the keys are network names. (This leaf is only used once, to describe product term layout.)

Option leaf
-----------

Example: ``{"fuses": [123, 124], "values": {"high_z": 3, "pull_up": 2, "pull_down": 0}}``.

The option leaf assigns symbolic names to combinations of fuse values, and describes a configurable device feature. It is an object with two keys, ``fuses`` and ``values``.

The ``fuses`` key is an array of fuse indexes that unambiguously maps fuse combinations to integers--the value of first specified fuse is the least significant bit in the binary notation.

The ``values`` key is an object containing symbolic names for known fuse combinations. All names point to unique fuse combiantions, though not every possible fuse combination may have a name assigned to it.

Node ``database``
=================

The root node is a map from device names (e.g. ``ATF1502AS``) to device specifications. The rest of this page is written in the context of a single device specification.

For ``device_name, device`` in ``database``:

Node ``device['pins']``
=======================

This node is a map from packages (e.g. ``TQFP44``) to pinouts.

For ``package, pinout`` in ``device['pins']``:

Mapping ``pinout``
------------------

This mapping relates pads (e.g. ``C2``, ``M1``) to package pins (e.g. ``40``, ``42``).

Mapping ``device['specials']``
==============================

This mapping relates special functions (e.g. ``CLK1``, ``TMS``) to pads (e.g. ``C1``, ``M9``).

Node ``device['blocks']``
=========================

This node is a map from block names (e.g. ``A``) to block specifications.

For ``block_name, block`` in ``device['blocks']``:

Sequence ``block['macrocells']``
--------------------------------

This sequence contains the names of macrocells in the logic block.

Sequence ``block['switches']``
------------------------------

This sequence contains the names of interconnect switches in the logic block.

Xpoints ``block['pterm_points']``
---------------------------------

This leaf relates block-local networks to product term fuse offsets. All macrocells in this block share an identical layout of product term fuses. To find a fuse that would include a specific network in a product term, add the index of the first fuse in the product term to the offset corresponding to the network in this leaf.

Node ``device['macrocells']``
=============================

This node is a map from macrocell names (e.g. ``MC1``) to macrocell specifications.

For ``macrocell_name, macrocell`` in ``device['macrocells']``:

Reference ``macrocell['block']``
--------------------------------

This reference links the macrocell to the block that contains the macrocell.

Reference ``macrocell['pad']``
------------------------------

This reference links the macrocell to the name of the pad connected to the macrocell. The pad connected to a macrocell ``MCx`` is always called ``Mx``; this leaf is provided for convenience.

Node ``macrocell['pterm_ranges']``
----------------------------------

This node is a map from product term names (which are always ``PT1``, ``PT2``, ``PT3``, ``PT4``, ``PT5``) to product term fuse ranges.

For ``pterm_name, pterm_range`` in ``macrocell['pterm_ranges']``:

Range ``pterm_range``
~~~~~~~~~~~~~~~~~~~~~

This range contains the product term fuses. The functions of the individual fuses are specified in the block that contains the macrocell.

.. fuse:: pt1_mux

Option ``macrocell['pt1_mux']``
-------------------------------

This option :ref:`configures <pt1_mux>` whether the ``PT1`` product term feeds the sum term or the special function (logic foldback node, and in rare cases XOR term).

.. fuse:: pt2_mux

Option ``macrocell['pt2_mux']``
-------------------------------

This option :ref:`configures <pt2_mux>` whether the ``PT2`` product term feeds the sum term or the special function (XOR term).

.. fuse:: pt3_mux

Option ``macrocell['pt3_mux']``
-------------------------------

This option :ref:`configures <pt3_mux>` whether the ``PT3`` product term feeds the sum term or the special function (asynchronous reset).

.. fuse:: gclr_mux

Option ``macrocell['gclr_mux']``
--------------------------------

This option :ref:`configures <gclr_mux>` whether the ``GCLR`` global network will reset the storage element of the macrocell.

.. fuse:: pt4_mux

Option ``macrocell['pt4_mux']``
-------------------------------

This option :ref:`configures <pt4_mux>` whether the ``PT4`` product term feeds the sum term or the special function (clock or clock enable).

.. fuse:: pt4_func

Option ``macrocell['pt4_func']``
--------------------------------

This option :ref:`configures <pt4_func>` whether, if it drives a special function, the ``PT4`` product term clocks the storage element of the macrocell, or enables the storage element driven by a global clock network.

.. fuse:: gclk_mux

Option ``macrocell['gclk_mux']``
--------------------------------

This option :ref:`configures <gclk_mux>` which ``GCLKx`` global network will clock of the storage element of the macrocell when the macrocell is clocked by a global network.

.. fuse:: pt5_mux

Option ``macrocell['pt5_mux']``
-------------------------------

This option :ref:`configures <pt5_mux>` whether the ``PT5`` product term feeds the sum term or the special function (asynchronous set or output enable).

.. fuse:: pt5_func

Option ``macrocell['pt5_func']``
--------------------------------

This option :ref:`configures <pt5_func>` whether, if it drives a special function, the ``PT5`` product term presets the storage element of the macrocell, or enables the output buffer.

.. fuse:: xor_a_mux

Option ``macrocell['xor_a_mux']``
---------------------------------

This option :ref:`configures <xor_a_mux>` whether the 1st input of the XOR term is driven by the sum term or the ``PT2`` product term.

.. warning::

   This option and :fuse:`cas_mux` cannot be simultaneously set to arbitrary values because they share a fuse.

.. fuse:: xor_b_mux

Option ``macrocell['xor_b_mux']``
---------------------------------

This option :ref:`configures <xor_b_mux>` whether the 2nd input of the XOR term is driven by the output of the storage element, the inverse of the ``PT1`` product term, the inverse of the ``PT2`` product term, or a constant low.

.. fuse:: cas_mux

Option ``macrocell['cas_mux']``
-------------------------------

This option :ref:`configures <cas_mux>` whether the sum term feeds the XOR term or the cascade output of the macrocell.

.. warning::

   This option and :fuse:`xor_a_mux` cannot be simultaneously set to arbitrary values because they share a fuse.

.. fuse:: xor_invert

Option ``macrocell['xor_invert']``
----------------------------------

This option :ref:`configures <xor_invert>` whether the output of the XOR term is inverted.

.. warning::

   This option and :fuse:`reset` cannot be simultaneously set to arbitrary values because they share a fuse.

.. fuse:: d_mux

Option ``macrocell['d_mux']``
-----------------------------

This option :ref:`configures <d_mux>` whether the storage element samples the combinatorial function or the fast input.

.. fuse:: dfast_mux

Option ``macrocell['dfast_mux']``
---------------------------------

This option :ref:`configures <dfast_mux>` whether the pad or the ``PT2`` product term is selected as the fast input.

.. warning::

   This option and :fuse:`o_mux` cannot be simultaneously set to arbitrary values because they share a fuse.

.. fuse:: storage

Option ``macrocell['storage']``
-------------------------------

This option :ref:`configures <storage>` whether the storage element functions as a D-flip-flop or a D-latch. On BE-series devices with 64 macrocells or more, it can also configure the storage element as a T-flip-flop.

.. fuse:: reset

Option ``macrocell['reset']``
-------------------------------

This option :ref:`configures <reset>` the power-on reset value of the storage element.

.. warning::

   This option and :fuse:`xor_invert` cannot be simultaneously set to arbitrary values because they share a fuse.

.. fuse:: fb_mux

Option ``macrocell['fb_mux']``
------------------------------

This option :ref:`configures <fb_mux>` whether the feedback signal ``MCx_FB`` is driven by the combinatorial function or the storage element.

.. fuse:: o_mux

Option ``macrocell['o_mux']``
-----------------------------

This option :ref:`configures <o_mux>` whether the output buffer is driven by the combinatorial function or the storage element.

.. warning::

   This option and :fuse:`dfast_mux` cannot be simultaneously set to arbitrary values because they share a fuse.

.. fuse:: oe_mux

Option ``macrocell['oe_mux']``
------------------------------

This option :ref:`configures <oe_mux>` whether the output buffer is enabled by one of the ``GOEx`` global networks, by the ``PT5`` product term, or is always disabled.

.. fuse:: slew_rate

Option ``macrocell['slew_rate']``
-----------------------------------

This option :ref:`configures <slew_rate>` the slew rate of the output buffer of the macrocell.

.. fuse:: output_driver

Option ``macrocell['output_driver']``
--------------------------------------

This option :ref:`configures <output_driver>` the output buffer of the macrocell as push-pull or open-collector.

.. fuse:: pt_power

Option ``macrocell['pt_power']``
--------------------------------

.. admonition:: Portability

   This option is present only in AS-series devices.

This option :ref:`configures <pt_power>` whether the macrocell's product terms are active or disabled to save power.

.. fuse:: low_power

Option ``macrocell['low_power']``
---------------------------------

.. admonition:: Portability

   This option is present only in AS-series devices.

This option :ref:`configures <low_power>` whether the macrocell operates at reduced power and reduced switching speed.

.. fuse:: macrocell-termination

Option ``macrocell['termination']``
-----------------------------------

.. admonition:: Portability

   This option is present only in BE-series devices.

This option configures the :ref:`termination <termination>` of the macrocell pin.

.. fuse:: macrocell-hysteresis

Option ``macrocell['hysteresis']``
---------------------------------------

.. admonition:: Portability

   This option is present only in BE-series devices.

This option configures whether the input buffer of the macrocell has :ref:`hysteresis <hysteresis>`.

.. fuse:: io_standard

Option ``macrocell['io_standard']``
-----------------------------------

.. admonition:: Portability

   This option is present only in BE-series devices with 64 macrocells or more.
   This option is absent on :pin:`VREFx` pins.

This option :ref:`configures <io_standard>` whether the input buffer of the macrocell follows the LVCMOS or SSTL signaling standard.

Node ``device['switches']``
===========================

This node is a map from switch names (e.g. ``UIM1``) to switch specifications.

For ``switch_name, switch`` in ``device['switches']``:

Reference ``switch['block']``
-----------------------------

This reference links the switch to the block that contains the switch.

Option ``switch['mux']``
------------------------

This option configures the network selected by the switch.

Node ``device['globals']``
==========================

This node is a map from global network names (e.g. ``GCLR``, ``GCLK1``) to global network specifications.

For ``switch_name, switch`` in ``device['globals']``:

Option ``switch['mux']``
------------------------

.. note::
   This option is absent for the ``GCLR`` global network.

This option configures the network selected by the switch.

Option ``switch['invert']``
---------------------------

This option configures the output buffer of the switch as inverting or non-inverting.

Node ``device['config']['pins']``
=================================

This node is a map from special pins (e.g. ``CLR``, ``TMS``) to I/O buffer options.

For ``special, config`` in ``device['config']['pins']``:

.. fuse:: standby_wakeup

Option ``config['standby_wakeup']``
-----------------------------------

.. admonition:: Portability

   This option is present only in AS-series devices for the ``CLKx`` pins.

This option :ref:`configures <standby_wakeup>` whether transitions on a ``CLKx`` pin will wake up the device from a low-power standby mode.

.. fuse:: special-termination

Option ``config['termination']``
--------------------------------

.. admonition:: Portability

   On AS-series devices, this option is present only for the JTAG ``TMS`` and ``TDI`` pins.

This option configures the :ref:`termination <termination>` of the special pin.

.. fuse:: special-hysteresis

Option ``config['hysteresis']``
------------------------------------

.. admonition:: Portability

   This option is present only in BE-series devices for the ``CLK1``, ``CLK2``, ``OE1``, and ``CLR`` pins.

This option configures whether the input buffer of the special pin has :ref:`hysteresis <hysteresis>`.

Node ``device['config']``
=========================

This node enumerates device-wide options.

Let ``config`` be ``device['config']``:

.. fuse:: arming_switch

Option ``config['arming_switch']``
----------------------------------

This option configures the :ref:`arming switch <arming_switch>`.

.. fuse:: read_protection

Option ``config['read_protection']``
------------------------------------

This option configures the :ref:`read protection <read_protection>`.

.. fuse:: jtag_pin_func

Option ``config['jtag_pin_func']``
----------------------------------

This option configures the :ref:`special function of JTAG pins <jtag_pin_func>`.

.. fuse:: pd1_pin_func

Option ``config['pd1_pin_func']``
---------------------------------

This option configures the :ref:`special function of the PD1 pin <pd1_pin_func>`.

.. fuse:: pd2_pin_func

Option ``config['pd2_pin_func']``
---------------------------------

This option configures the :ref:`special function of the PD2 pin <pd2_pin_func>`.

.. fuse:: device-termination

Option ``config['termination']``
--------------------------------

.. admonition:: Portability

   This option is present only in AS-series devices.

This option configures the :ref:`termination <termination>` of every macrocell pin.

.. fuse:: reset_hysteresis

Option ``config['reset_hysteresis']``
-------------------------------------

.. admonition:: Portability

   This option is present only in AS-series devices.

This option :ref:`configures <reset_hysteresis>` the behavior of the power-on reset circuitry when V\ :sub:`CC` is close to V\ :sub:`RST`.

Node ``device['user']``
=======================

This node is an array of user signature byte specifications.

For ``user_byte`` in ``device['user']``:

Option ``user_byte``
--------------------

This option provides one byte (out of two) in the "user electronic signature" register accessible via JTAG (:ref:`ATF1502AS <flowas-read-ues>`, :ref:`ATF1502BE <flowbe-read-ues>`). Unlike with every other option, the values ``bit0``..\ ``bit7`` form a bit field rather than being mutually exclusive.

Node ``device['ranges']``
=========================

In ATF15xx fuse maps, fuses are mostly grouped into contiguous ranges based on their function. This node enumerates the known fuse ranges. These ranges are primarily useful to the fuzzing machinery itself.

Let ``ranges`` be ``device['ranges']``:

Range ``ranges['pterms']``
--------------------------

This range is occupied by product term fuses. It is only useful to the fuzzing machinery itself.

Range ``ranges['macrocells']``
------------------------------

This range is occupied by macrocell options. It is only useful to the fuzzing machinery itself.

Range ``ranges['uim_muxes']``
-----------------------------

This range is occupied by interconnect muxes. It is only useful to the fuzzing machinery itself.

Range ``ranges['goe_muxes']``
-----------------------------

This range is occupied by global output enable muxes. It is only useful to the fuzzing machinery itself.

Range ``ranges['config']``
--------------------------

This range is occupied by global clock muxes, global network inverters, special function options, pin termination options, and other device-wide configuration options. It is only useful to the fuzzing machinery itself.

Range ``ranges['user']``
------------------------

This range is occupied by user signature fuses. It is only useful to the fuzzing machinery itself.

Range ``ranges['reserved']``
----------------------------

This range is reserved. All fuses in this range must be set to ``0``.
