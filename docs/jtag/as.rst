AS-series programming
#####################

ATF15xxAS devices are always controlled by the contents of the integrated Flash memory. They are in-system programmable via `JTAG <https://en.wikipedia.org/wiki/JTAG>`_ using a command set close to but not entirely compatible with `IEEE 1532 <https://standards.ieee.org/standard/1532-2000.html>`_.

See also :doc:`programming options <../options/program>`.

.. _jtagas-instrs:

JTAG instructions
=================

AS-family CPLDs have a 10 bit long instruction register, and support the following programming-related JTAG instructions:

.. table::
   :widths: auto

   ===================== ============ =============== =========
   Instruction           IR value     Selected DR     DR length
   ===================== ============ =============== =========
   ``IDCODE``            ``059``      ``IDCODE``      32
   ``ATF_READ_UES``      ``270``      ``UES``         16
   ``ATF_CONFIG``        ``280``      ``FLASH_KEY``   10
   ``ATF_READ``          ``28c``      ``BYPASS``      1
   ``ATF_DATA0..3``      ``290..293`` ``FLASH_DATA``  varies
   ``ATF_PROGRAM_ERASE`` ``29e``      ``BYPASS``      1
   ``ATF_ADDRESS``       ``2a1``      ``FLASH_ADDR``  11
   ``ATF_LATCH_ERASE``   ``2b3``      ``BYPASS``      1
   ``ATF_UNKNOWN``       ``2bf``      ``BYPASS``      1
   ===================== ============ =============== =========

.. todo::

   Update the description and usage for the ``ATF_UNKNOWN`` instruction based on recent discoveries.

.. _jtagas-layout:

Memory layout
=============

The geometry of the Flash memory varies with the CPLD density. The following table describes the memory layouts for all device densities:

.. table::
   :widths: auto

   ======= =========== ===== =========== ===== =========== =====
   Device     ATF1502AS         ATF1504AS         ATF1508AS
   ------- ----------------- ----------------- -----------------
   Region  Address(es) Width Address(es) Width Address(es) Width
   ======= =========== ===== =========== ===== =========== =====
   A-side  ``00..6c``  86    ``00..6c``  166   ``00..6c``  326
   B-side  ``80..e5``  86    ``80..e9``  166   ``80..fb``  326
   Config  ``100``     32    ``100``     32    ``100``     32
   JTAG    ``200``     4     ``200``     4     ``200``     4
   UES     ``300``     16    ``300``     16    ``300``     16
   ======= =========== ===== =========== ===== =========== =====

During :ref:`programming <flowas-program>` or :ref:`reading <flowas-read>`, the actual DR size is determined by the contents of ``FLASH_ADDR`` and the table above.

.. _jtagas-flows:

Programming flows
=================

In all programming flows below, after shifting into IR or DR, enter Run-Test/Idle.

.. _flowas-read-ues:

Read UES
--------

To read the user signature ``ues``:

  1. Shift ``ATF_READ_UES`` into IR.
  2. Shift ``ues`` out of DR.
  3. Bit-reverse ``ues``.

.. _flowas-enable:

Enable
------

To enter programming mode:

  1. Shift ``ATF_CONFIG`` into IR.
  2. Shift ``1b9`` into DR.

This sequence disables normal operation and enables programming operations. It also disables the output buffers. If bus keepers are enabled with the corresponding fuse, the outputs will weakly hold their current state during programming.

.. _flowas-disable:

Disable
-------

To leave programming mode:

  1. Shift ``ATF_CONFIG`` into IR.
  2. Shift ``000`` into DR.

This sequence disables programming operations and enables normal operation. It also resets both the macrocells and the JTAG TAP.

.. _flowas-erase:

Erase
-----

To erase the currently programmed configuration:

  1. Shift ``ATF_LATCH_ERASE`` into IR.
  2. Shift ``ATF_PROGRAM_ERASE`` into IR.
  3. Wait 210 ms.

.. _flowas-program:

Program
-------

To program a configuration word ``data`` to address ``addr``:

  1. Shift ``ATF_ADDRESS`` into IR.
  2. Shift ``addr`` into DR.
  3. Shift ``ATF_DATA0 + (addr >> 8)`` into IR.
  4. Shift ``data`` into DR.
     DR length is determined by the address and the :ref:`memory layout <jtagas-layout>`.
  5. Shift ``ATF_PROGRAM_ERASE`` into IR.
  6. Wait 30 ms.

.. _flowas-read:

Read
----

To read a configuration word ``data`` from address ``addr``:

  1. Shift ``ATF_ADDRESS`` into IR.
  2. Shift ``addr`` into DR.
  3. Shift ``ATF_READ`` into IR.
  4. Wait 20 ms.
  5. Shift ``ATF_DATA0 + (addr >> 8)`` into IR.
  6. Shift ``data`` out of DR.
     DR length is determined by the address and the :ref:`memory layout <jtagas-layout>`.

.. _jtagas-fusemap:

Fuse packing
============

Running the place & route tool produces a fuse map; a 1d sequence of fuses. However, the device's Flash memory is organized as a series of words; a 2d array of cells. Fuses can be packed into and unpacked from the Flash memory by applying the permutations described below.

In all of the code fragments below, let ``jed_index`` be the index of a fuse, ``svf_row`` be the address of a word, and ``svf_col`` be the bit offset into the word. Then, packing and unpacking are bit copy operations between the two representations.

ATF1502AS
---------

The following snippet implements the packing (``jed_to_svf_coords``) and unpacking (``svf_to_jed_coords``) permutations for ATF1502AS:

.. literalinclude:: ../../util/device.py
   :linenos:
   :lines: 85-105,107-134
   :dedent: 4

ATF1504AS
---------

The following snippet implements the packing (``jed_to_svf_coords``) and unpacking (``svf_to_jed_coords``) permutations for ATF1504AS:

.. literalinclude:: ../../util/device.py
   :linenos:
   :lines: 150-168,170-197
   :dedent: 4

ATF1508AS
---------

The following snippet implements the packing (``jed_to_svf_coords``) and unpacking (``svf_to_jed_coords``) permutations for ATF1508AS:

.. literalinclude:: ../../util/device.py
   :linenos:
   :lines: 213-231,233-260
   :dedent: 4
