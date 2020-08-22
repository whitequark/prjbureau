-m util.fusecli
###############

.. argparse::
   :ref: util.fusecli.arg_parser
   :prog: python3 -m util.fusecli

Examples
========

Examining fuses
---------------

To print all known fuses:

.. code-block:: console

   $ python3 -m util.fusecli design.jed get
   MC1:
     PT1: GND
     PT2: GND
   [output trimmed]

To print macrocell ``MC1`` product term ``PT1``:

.. code-block:: console

   $ python3 -m util.fusecli design.jed get MC1.PT1
   MC1:
     PT1: GND

To print all product terms of macrocell ``MC1``:

.. code-block:: console

   $ python3 -m util.fusecli design.jed get MC1.PT
   MC1:
     PT1: GND
     PT2: GND
     PT3: GND
     PT4: GND
     PT5: GND

To print option ``gclk_mux`` of every macrocell:

.. code-block:: console

   $ python3 -m util.fusecli design.jed get MC.gclk_mux
   MC1:
     CFG:
       gclk_mux       = GCLK2
   MC2:
     CFG:
       gclk_mux       = GCLK2
   MC3:
   [output trimmed]

To print options ``pt1_mux`` and ``pt2_mux`` of every macrocell:

.. code-block:: console

   $ python3 -m util.fusecli design.jed get MC.pt1_mux MC.pt2_mux
   MC1:
     CFG:
       pt1_mux        = sum
       pt2_mux        = sum
   MC2:
   [output trimmed]

Modifying fuses
---------------

To change option ``gclk_mux`` of macrocell ``MC8`` to be ``GCLK2``:

.. code-block:: console

   $ python3 -m util.fusecli design.jed set MC8.gclk_mux GCLK2
   MC8:
     CFG:
       gclk_mux       = GCLK2
   Changed 1 fields, 2 fuses.

To change option ``low_power`` of every macrocell to be ``on``:

.. code-block:: console

   $ python3 -m util.fusecli design.jed set MC.low_power on
   MC1:
     CFG:
       low_power      = on
   [output trimmed]
   MC32:
     CFG:
       low_power      = on
   Changed 32 fields, 32 fuses.

To change options ``pt1_mux`` and ``pt2_mux`` of every macrocell to be ``sum``:

.. code-block:: console

   $ python3 -m util.fusecli design.jed set MC.pt1_mux sum MC.pt2_mux sum
   MC1:
     CFG:
       pt1_mux        = sum
   [output trimmed]
   MC32:
     CFG:
       pt2_mux        = sum
   Changed 64 fields, 0 fuses.

To set product term ``PT1`` of macrocell ``MC1`` to ``UIM2_P & UIM4_N``:

.. code-block:: console

   $ python3 -m util.fusecli design.jed set MC1.PT1 UIM2_P,UIM4_N
   MC1:
     PT1: UIM2_P,UIM4_N
   Changed 1 fields, 94 fuses.
   $ python3 -m util.fusecli design.jed get MC1.PT1
   MC1:
     PT1: UIM2_P & UIM4_N

To remove ``UIM4_N`` from product term ``PT1`` of macrocell ``MC1`` and add ``UIM8_P`` instead:

.. code-block:: console

   $ python3 -m util.fusecli design.jed set MC1.PT1 -UIM4_N,+UIM8_P
   MC1:
     PT1: -UIM4_N,+UIM8_P
   Changed 1 fields, 2 fuses.
   $ python3 -m util.fusecli design.jed get MC1.PT1
   MC1:
     PT1: UIM2_P & UIM8_P

To clear product term ``PT1`` of every macrocell:

.. code-block:: console

   $ python3 -m util.fusecli design.jed set MC.PT1 GND
   MC1:
     PT1: GND
   [output trimmed]
   MC32:
     PT1: GND
   Changed 32 fields, 94 fuses.
