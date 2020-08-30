I/O buffer options
##################

This section describes macrocell input/output buffer options and global input buffer options.

.. _termination:

Pin termination
===============

ATF15xx CPLDs provide configurable :wiki:`pull-up <Pull-up resistor>`/:wiki:`pull-down <Pull-down resistor>` resistors and :wiki:`bus keeper <Bus-holder>` circuits connected to the pins, collectively called *pin termination* circuits. Available termination types depend on the series and the pin, though it is always possible to turn termination off.

On ATF15xxAS, the device configuration option :fuse:`config.termination <device-termination>` selects the termination (``high_z`` or ``bus_keeper``) for every macrocell at once.

On ATF15xxBE, the macrocell configuration option :fuse:`macrocells[].termination <macrocell-termination>` selects the termination (``high_z``, ``pull_up``, or ``bus_keeper``) individually for each macrocell, and the pin configuration options :fuse:`pins[CLR,CLK1,CLK2,OE1].termination <special-termination>` select the termination (``high_z``, ``pull_up``, ``pull_down``, or ``bus_keeper``) individually for each of the global input pins.

On both series, if the :ref:`special function <jtag_pin_func>` of the JTAG pins is selected, the pin configuration options :fuse:`pins[TMS,TDI].termination <special-termination>` select the termination (``high_z`` or ``pull_up``) individually for each of the JTAG input pins.

The following table describes the possible termination options:

.. |global-inputs| replace:: :pin:`CLR`, :pin:`CLK1`, :pin:`CLK2`, :pin:`OE1`
.. |jtag-inputs| replace:: :pin:`TMS`, :pin:`TDI`

.. table::
   :widths: auto
   :class: narrow

   ======================= ==== ==== ==== ==== ==== ==== ==== ====
   Series                       ATF15xxAS           ATF15xxBE
   ----------------------- ------------------- -------------------
   Pins                    Hi-Z P-Up P-Dn Keep Hi-Z P-Up P-Dn Keep
   ======================= ==== ==== ==== ==== ==== ==== ==== ====
   :pin:`MCn` (global)     |x|  |o|  |o|  |x|  |-|
   ----------------------- ---- ---- ---- ---- -------------------
   :pin:`MCn` (individual) |-|                 |x|  |x|  |o|  |x|
   ----------------------- ------------------- ---- ---- ---- ----
   |global-inputs|         |o|  |o|  |o|  |o|  |x|  |x|  |x|  |x|
   ----------------------- ---- ---- ---- ---- ---- ---- ---- ----
   |jtag-inputs|\ [#]_     |x|  |x|  |o|  |o|  |x|  |x|  |o|  |o|
   ======================= ==== ==== ==== ==== ==== ==== ==== ====

.. [#] Used when the :ref:`special function <jtag_pin_func>` of the pin is selected; otherwise, pin termination is controlled by the macrocell option, if any.

.. _output_driver:

Output driver type
==================

On ATF15xx CPLDs, every macrocell output buffer can be configured as :wiki:`push-pull <Push-pull output>` or :wiki:`open drain (open collector) <Open collector>`. Setting the macrocell configuration option :fuse:`output_driver` to ``push_pull`` enables both CMOS transistors in the output driver; setting it to ``open_drain`` enables only the NMOS transistor.

.. _slew_rate:

Output slew rate
================

On ATF15xx CPLDs, every macrocell output buffer features individual slew rate control, which may be used to reduce :wiki:`EMI <Electromagnetic interference>` in designs without fast-switching signals. Setting the macrocell configuration option :fuse:`slew_rate` to ``fast`` selects high strength output drivers for maximum performance; setting it to ``slow`` selects low strength output drivers for reducing noise.

.. _hysteresis:

Input hysteresis
================

.. admonition:: Portability

   This option is present only in BE-series devices.

On ATF15xxBE devices, every macrocell input/output pin and the four global input pins :pin:`CLR`, :pin:`CLK1`, :pin:`CLK2`, :pin:`OE1` can be configured with or without :wiki:`hysteresis`. On these devices, setting the configuration options :fuse:`macrocells[].hysteresis <macrocell-hysteresis>` or :fuse:`pins[].hysteresis <special-hysteresis>` to ``on`` selects the :wiki:`Schmitt trigger` input buffer; setting them to ``off`` selects the simple CMOS input buffer.

.. _io_standard:

I/O standards
=============

.. admonition:: Portability

   This option is present only in BE-series devices with 64 macrocells or more.

Normally, ATF15xx CPLD inputs and outputs follow TTL/LVTTL\ [#ttl]_ or CMOS/LVCMOS\ [#cmos]_ signaling standards. However, BE-series devices starting with ATF1504BE also support SSTL signaling standards.

On these devices, setting the macrocell configuration option :fuse:`io_standard` to ``sstl`` (or erasing the device) selects the differential input buffer (referenced to the :pin:`VREFA` or :pin:`VREFB` pins); setting it to ``lvcmos`` selects the single-ended CMOS input buffer. Pins for the first half of the macrocells are referenced to :pin:`VREFA`, and for the second half of the macrocells to :pin:`VREFB`. If any pin is referenced to :pin:`VREFx`, then that :pin:`VREFx` pin may only be used for the SSTL reference voltage function.

The following table describes the I/O standards that can be used with different devices and configurations:

.. table::
   :widths: auto

   ============= ======= ========= ========== ========= =========
   Standard      Voltage ATF15xxAS ATF15xxASV ATF1502BE ATF15xxBE\ [#be]_
   ============= ======= ========= ========== ========= =========
   TTL output    5 V     |x|       |x|        |x|       |x|
   TTL input     5 V     |x|       |o|        |o|       |o|
   CMOS I/O      5 V     |x|       |o|        |o|       |o|
   LVTTL output  3.3 V   |o|       |x|        |x|       |x|
   LVTTL input   3.3 V   |x|       |x|        |x|       |x|
   LVCMOS I/O    3.3 V   |o|       |x|        |x|       |x|
   SSTL output   3.3 V   |o|       |o|        |x|       |x|
   SSTL input    3.3 V   |o|       |o|        |o|       |x|
   LVCMOS I/O    2.5 V   |o|       |o|        |x|       |x|
   SSTL output   2.5 V   |o|       |o|        |x|       |x|
   SSTL input    2.5 V   |o|       |o|        |o|       |x|
   LVCMOS I/O    1.8 V   |o|       |o|        |x|       |x|
   LVCMOS I/O    1.5 V   |o|       |o|        |x|       |x|
   ============= ======= ========= ========== ========= =========

.. [#ttl] Briefly, in TTL and LVTTL, V\ :sub:`IL`/V\ :sub:`IH` = 0.8/2.0 V and V\ :sub:`OL`/V\ :sub:`OH` = 0.4/2.4 V.
.. [#cmos] Briefly, in CMOS and LVCMOS, V\ :sub:`IL`/V\ :sub:`IH` = 30%/70% Vcc and V\ :sub:`OL`/V\ :sub:`OH` = 20%/80% Vcc.
.. [#be] Other than ATF1502BE.
