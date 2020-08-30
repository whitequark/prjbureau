Power control options
#####################

This section describes global device options related to power management.

.. _pd1_pin_func:
.. _pd2_pin_func:

PDx pin multiplexing
====================

ATF15xx CPLDs do not have dedicated power gating pins. Instead, the two power gating signals, ``PD1`` and ``PD2``, are multiplexed with normal macrocell I/O signals. Setting the device configuration options :fuse:`pd1_pin_func` or :fuse:`pd2_pin_func` to ``pd`` selects the power gating special function, leaving the macrocell buried; setting it to ``user`` selects the regular function.

Aside from reducing power consumption, asserting either of the power gating inputs latches and holds all internal and external signals, effectively freezing the device state.

.. _standby_wakeup:

Input transition detection
==========================

.. admonition:: Portability

   This option is present only in AS-series devices, and operational only in devices with an L suffix.

ATF15xxAS CPLDs can automatically enter and leave a low-power standby mode, determined by the frequency of transitions on one or more of the :pin:`CLKx` pins. In this low-power mode, the device has reduced performance, but otherwise operates normally. Setting the pin configuration option :fuse:`pins[CLK1,CLK2,CLK3].standby_wakeup <standby_wakeup>` to ``on`` causes the device to leave the standby mode when transitions occur sufficiently often on the corresponding :pin:`CLKx` pin; setting it to ``off`` causes transitions to be ignored on that pin. When running at full power, device performance increases to match the next lowest speed grade.

.. _reset_hysteresis:

Reset hysteresis
================

.. admonition:: Portability

   This option is present only in AS-series devices.

ATF15xxAS CPLDs may not reliably initialize the macrocell registers as a part of power-on reset if V\ :sub:`CC` stays too close to the reset level V\ :sub:`RSTH`. Setting the device configuration option :fuse:`reset_hysteresis` to ``large`` ensures reliable initialization, but requires V\ :sub:`CC` to shut off completely if it falls below V\ :sub:`RSTL`; setting it to ``small`` reverses the tradeoff.

.. note::

   The values of V\ :sub:`RSTH` and V\ :sub:`RSTL` are not definitively known. For 3.3 V devices, it is likely that V\ :sub:`RSTH`/V\ :sub:`RSTL` are 3.0/2.0 V. For 5 V devices, it is likely that V\ :sub:`RSTH` is 4.0 V.

.. _low_power:

Reducing macrocell power
========================

.. admonition:: Portability

   This option is present only in AS-series devices.

ATF15xxAS CPLDs provide a mechanism to reduce power consumed by a macrocell without completely disabling it. Setting the macrocell configuration option :fuse:`low_power` to ``on`` reduces power by approx. 50% and performance by approx. 80%; setting it to ``off`` results in nominal power and performance.

.. _pt_power:

Gating product term power
=========================

.. admonition:: Portability

   This option is present only in AS-series devices.

Product terms of ATF15xxAS CPLDs consume significant active power when their inputs are switching, which is especially undesirable for unused macrocells (or macrocells that do not use product terms, e.g. driving an output with a fixed level). Setting the macrocell configuration option :fuse:`pt_power` to ``off`` disables product term circuits and reduces power consumption; setting it to ``on`` makes it possible to use product terms to drive the macrocell.

.. warning::

   When product term power is gated, every product term fuse must be set to ``0``; then and only then the output of the product term stays low.

   Vendor toolchain never sets fuses to ``1`` in disabled product terms. Hardware testing shows that setting any single fuse to ``1`` results in the output of the product term becoming high, is at odds with the definition of a product term. It's not clear why this happens (parasitics?) but it is clear that the fuses of gated product terms should be always zeroed.
