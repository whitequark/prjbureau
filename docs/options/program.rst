Programming options
###################

This document describes global device options related to Flash programming.

.. _jtag_pin_func:

JTAG pin multiplexing
=====================

ATF15xx CPLDs do not have dedicated JTAG pins. Instead, the four JTAG signals, ``TMS``, ``TCK``, ``TDI``, and ``TDO``, are multiplexed with normal macrocell I/O signals. Setting the device configuration option :fuse:`jtag_pin_func` to ``jtag`` (or erasing the device) selects the JTAG special function, leaving the macrocell buried; setting it to ``user`` selects the regular function. This option carries two inherent hazards.

First, the option takes effect immediately once it is programmed. Because of this, the fuse corresponding to this option must be programmed during the very last operation, or the device could never be fully programmed. To verify the device, a fuse map altered to exclude this option must be programmed first, the altered map must be verified, and then the option must be programmed in isolation by taking advantage of the wired-AND nature of the Flash memory.

Second, the option takes effect immediately after power-up, preventing any further programming of the device by ordinary means. Although not (usefully) documented, this option can be overridden; applying +12 V to the :pin:`OE1` pin selects the JTAG special function regardless of the state of the :fuse:`jtag_pin_func` option. Similarly to the fuse itself, the fuse override is not latched, and is active only while the high voltage is applied. High voltage applied to :pin:`OE1` does not serve any purpose beyond overriding the JTAG configuration option.

.. _read_protection:

Read protection
===============

It is possible to prevent the fuses programmed into the device from being read without disabling the JTAG interface by setting the device configuration option :fuse:`read_protection` to ``on``. The user signature fuses can still be read using a dedicated JTAG instruction.

Similarly to the :ref:`pin multiplexing option <jtag_pin_func>`, the fuse corresponding to this option must be programmed during the very last operation.

.. _arming_switch:

Arming switch
=============

ATF15xx CPLDs include a feature that prevents partially programmed devices from erroneously driving its outputs during in-circuit programming. Setting the device configuration option :fuse:`arming_switch` to ``safe`` (or erasing the device) disables all output drivers; setting it to ``armed`` enables regular operation.

.. the doc says: "The ATF15xxSE Family also incorporates a protection feature that locks the device and prevents the inputs and I/O from driving if the programming process is interrupted for any reason."
.. wtf does "prevents the inputs from driving" mean? does it prevent the CPLD core from being driven? does it disable input termination? who knows

The fuse corresponding to this option must be programmed after every other fuse, but before the :ref:`pin multiplexing option <jtag_pin_func>` or the :ref:`read protection option <read_protection>`, since they are located in different Flash words.
