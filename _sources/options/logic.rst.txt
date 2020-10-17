Macrocell options (WIP)
#################

The design of the ATF15xx macrocell is remarkably complicated; the combination of backwards compatibility, cost optimization, ad-hoc evolution, and pressure to add more routing options has resulted in a circuit that is almost biological in nature. The amount of macrocell edge cases that bring out bugs in the vendor toolchain seems to demonstrate that it is challenging to use even with first-party documentation. Nevertheless, with the right approach, even this macrocell can be painlessly understood.

The ATF15xx macrocell appears to have been designed by strictly following two rules:

  1. Never route a product term to more than one destination.
  2. Never let a fuse combination become redundant.

Rule (1) requires that, even though a product term may be routed through multiple muxes/decoders, these components (and by extension the fuses that drive them) must act together to prevent the product term from being connected to more than one possible destination at once. E.g. there must be no configuration where ``PT4`` drives ``CLK`` and ``CE`` simultaneously.

Rule (2) requires that, when any redundancies happen to arise from the layout of the macrocell routing paths, the fuse combinations that encode the redundant configurations must be repurposed for a new capability, without particular regard to orthogonality, and even at the cost of eliminating some rarely needed but otherwise reasonable configurations. E.g. the fuse that controls the fast registered input, :fuse:`dfast_mux`, is physically shared with the fuse that controls the output multiplexer, :fuse:`o_mux`.

.. admonition:: Fun fact

   Both of these rules are violated in exactly one obscure corner case, specific to each rule.

In reality, these "rules" could well have been a natural consequence of conserving NVM cells and/or routability and not something that was followed explicitly. Regardless, the macrocell design is a lot easier to understand from this perspective.

Overview
--------

.. todo:: write this

.. _pt1_mux:
.. _pt2_mux:
.. _xor_a_mux:
.. _xor_b_mux:
.. _xor_invert:
.. _cas_mux:

PT1/PT2 routing group
---------------------

.. todo:: write this

.. _pt3_mux:
.. _gclr_mux:

PT3 routing group
-----------------

.. todo:: write this

.. _pt4_mux:
.. _pt4_func:
.. _gclk_mux:

PT4 routing group
-----------------

.. todo:: write this

.. _pt5_mux:
.. _pt5_func:
.. _oe_mux:

PT5 routing group
-----------------

.. todo:: write this

.. _d_mux:
.. _dfast_mux:
.. _o_mux:

D/Q routing group
-----------------

.. todo:: write this

.. _fb_mux:

FB routing group
----------------

.. todo:: write this

.. _storage:
.. _reset:

FF/latch configuration
----------------------

.. todo:: write this
