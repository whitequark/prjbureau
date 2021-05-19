Introduction
############

*Project Bureau* enables a fully open-source flow for Microchip_ (Atmel) ATF15xx family CPLDs_ by documenting their fuse maps and programming algorithms.

You can discuss the project at the IRC channel `#prjbureau at libera.chat <https://libera.chat>`_.

.. _Microchip: https://microchip.com
.. _CPLDs: https://en.wikipedia.org/wiki/Complex_programmable_logic_device

Motivation
==========

In 2020, CPLDs_ are widely considered obsolete. Why, then, work on a CPLD toolchain? Although in applications relying on reconfigurable logic alone, CPLDs are outclassed by FPGAs_ in every conceivable aspect, they still have advantages in system design: integrated configuration memory, single rail operation, powerful and rugged I/O buffers, and compatibility with 5 V TTL & CMOS systems. It is the last aspect that has motivated the research resulting in Project Bureau.

.. _FPGAs: https://en.wikipedia.org/wiki/Field-programmable_gate_array

Although 5 V logic has essentially disappeared from modern digital design, it did not become irrelevant. For decades, the microelectronics industry produced 5 V circuits, many of which are still in use, while others are of historical importance or pursued by retrocomputing enthusiasts. These circuits often use parallel, bidirectional buses, which are challenging to interface with today's serial, low pin count, low voltage hardware.

Microchip_ ATF15xx is the last CPLD family in active production that offers true 5 V operation, i.e. rail-to-rail 5 V outputs, providing maximum compatibility with legacy devices. (While some similar devices are still available, such as Lattice_ ispMACH4A5_, they are being phased out, employ 5 V tolerant I/O buffers rather than true 5 V ones, or both.)

Although ATF15xx devices are widely available from distributors, they are not accessible: the proprietary vendor toolchain, developed in late 1990s and last updated in mid-2000s, uses an obscure hardware definition language called CUPL_, is Windows-only, requires an expensive programming adapter, and does not properly run on anything newer than Windows XP.

.. _Lattice: https://www.latticesemi.com/
.. _ispMACH4A5: https://www.latticesemi.com/en/Support/MatureAndDiscontinuedDevices/ispMACH4A5
.. _CUPL: https://en.wikipedia.org/wiki/Programmable_Array_Logic#CUPL

Wouldn't it be convenient if this CPLD could be used with modern open-source tools like Yosys_? Unfortunately, the vendor does not publish information required to develop a toolchain. Fortunately, it isn't necessary to rely on the vendor here.

.. _Yosys: https://github.com/YosysHQ/yosys

Supported devices
=================

ATF15xx family devices are currently available in three densities: ATF1502 (32 macrocells), ATF1504 (64 macrocells), and ATF1508 (128 macrocells). Note that ATF1500_ is an obsolete device that is, confusingly, **not** a part of the ATF15xx family.

AS-series (``AS``, ``ASV`` and ``ASL`` suffixes) devices, such as ATF1502AS_, ATF1504ASV_, and ATF1508ASL_, are actively produced and widely available. BE-series (``BE`` suffix) devices, such as ATF1502BE_, ATF1504BE_, and ATF1508BE_, are produced on demand and are seldom in stock.

.. _ATF1500: https://www.microchip.com/wwwproducts/en/ATF1500A
.. _ATF1502AS: https://www.microchip.com/wwwproducts/en/ATF1502AS
.. _ATF1504ASV: https://www.microchip.com/wwwproducts/en/ATF1504ASV
.. _ATF1508ASL: https://www.microchip.com/wwwproducts/en/ATF1508ASL
.. _ATF1502BE: https://www.microchip.com/wwwproducts/en/ATF1502BE
.. _ATF1504BE: https://www.microchip.com/wwwproducts/en/ATF1504BE
.. _ATF1508BE: https://www.microchip.com/wwwproducts/en/ATF1508BE

Virtually every aspect of the ATF15xx architecture is well-understood. However, peculiarities of the toolchain result in practical difficulties producing complete fuse map documentation. The following table summarizes the state of the project:

.. table::
   :widths: auto

   ===================== ============= ============
   Device(s)             Fuse database Programming
   ===================== ============= ============
   **ATF1502AS/ASV/ASL** **Complete**  **Complete**
   ATF1504AS/ASV/ASL     Near-complete Untested
   ATF1508AS/ASV/ASL     Partial       Untested
   ATF1502BE             Near-complete None
   ATF1504BE             Near-complete None
   ATF1508BE             Partial       None
   ===================== ============= ============

Installation
============

There is nothing to install! Aside from this document, the ultimate artefact of Project Bureau is a single `chip database file <database/database.json.gz>`__ containing a machine-readable description of every known fuse in every supported device. This file, together with the detailed descriptions from this document, can be used by downstream tooling to produce or manipulate fuse maps. It can also be :doc:`explored <explore>` as hypertext.

.. _develop:

Development
===========

This project provides several :doc:`utilities <tools/index>` for manipulating fuse maps. They require Python 3.6 and the bitarray_ PyPI package. These utilities are provided for *experimental purposes only* and are intentionally not packaged; to use them, add this repository to ``PYTHONPATH``:

.. _bitarray: https://pypi.org/project/bitarray

.. code-block:: console

   $ pip3 install bitarray
   $ export PYTHONPATH=../path/to/prjbureau

Acknowledgements
================

Although I (whitequark) wrote virtually all of the code and documentation in this project, it would not exist if not for many people in the open FPGA community and beyond. I would like to express my gratitude, in no particular order, to:

  * `Claire Xenia Wolf <https://www.clairexen.net/>`__, for pioneering open FPGA toolchains with `Project IceStorm <http://www.clifford.at/icestorm/>`__, and inspiring me to start working with programmable logic;
  * `Andrew Zonenberg <https://github.com/azonenberg>`__, for working on `gp4par <https://github.com/azonenberg/openfpga/commits/master/src/gp4par>`__, one of the first open-source place & route tools, and `demonstrating <https://siliconexposed.blogspot.com/2014/03/getting-my-feet-wet-with-invasive.html>`__ clean-room reverse engineering of the interconnect matrix, the most challenging part of a CPLD to document.
  * @interruptinuse, for assistance in fuzzing the interconnect matrix, and supporting my work in general;
  * `Maya E. <mailto:moontouched@moontouched.me>`__, for assistance in validating the interconnect routing and minimizing the macrocell truth table, and contributing the JED↔SVF mapping for ATF1504/ATF1508;
  * `Peter Zieba <http://peterzieba.com/>`__, for bringing the capabilities of the ATF15xx family to my attention, `archiving <http://www.5vpld.com/>`__ the relevant tools and documentation, and recording high-voltage programming traces;
  * `David Shah <https://ds0.me/>`__, for building nextpnr-generic, and revealing that place & route tools don't have to be opaque and arcane;
  * `R. Ou <https://robertou.com/>`__, for working on CPLD synthesis in Yosys, demonstrating a functional CPLD toolchain, and generally ensuring these devices are not forgotten.

License
=======

Unless otherwise noted, the files in this repository are covered by the `0-clause BSD license <https://opensource.org/licenses/0BSD>`__:

    Permission to use, copy, modify, and/or distribute this software for
    any purpose with or without fee is hereby granted.

    THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
    WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
    MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
    ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
    WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN
    AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT
    OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
