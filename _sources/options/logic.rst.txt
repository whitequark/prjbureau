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

.. table::
   :widths: auto

   ======= ======= ======= ======= ======= ======= =======
   Configuration   Routing
   --------------- ---------------------------------------
   pt1_mux pt2_mux ST.I1   ST.I2   y1      y2      yf
   ======= ======= ======= ======= ======= ======= =======
   ``flb`` ``xor`` ``GND`` ``GND`` ``pt1`` ``pt2`` ``pt1``
   ``sum`` ``xor`` ``pt1`` ``GND`` ``VCC`` ``pt2`` ``GND``
   ``flb`` ``sum`` ``GND`` ``pt2`` ``pt1`` ``VCC`` ``pt1``
   ``sum`` ``sum`` ``pt1`` ``pt2`` ``VCC`` ``VCC`` ``GND``
   ======= ======= ======= ======= ======= ======= =======

.. table::
   :widths: auto

   ============== ============ ============ =============== ====== ======== ========= =========
   Configuration                                            Routing
   -------------------------------------------------------- -----------------------------------
   xor_a_mux [1]_ xor_b_mux    cas_mux [1]_ xor_invert [2]_ XT.A   XT.B     MC.CASOUT MC.FLB
   ============== ============ ============ =============== ====== ======== ========= =========
   ``sum``        ``VCC_pt12`` ``GND``      ``on``          ``st`` ``VCC``  ``GND``   ¬\ ``yf``
   ``sum``        ``VCC_pt12`` ``GND``      ``off``         ``st`` ``y2``   ``GND``   ¬\ ``yf``
   ``sum``        ``ff_qn``    ``GND``      ``on``          ``st`` ``ffqn`` ``GND``   ¬\ ``yf``
   ``sum``        ``ff_qn``    ``GND``      ``off``         ``st`` ``ffqn`` ``GND``   ¬\ ``yf``
   ``VCC_pt2``    ``ff_qn``    ``sum``      ``on``          ``y2`` ``ffqn`` ``st``    ¬\ ``yf``
   ``VCC_pt2``    ``ff_qn``    ``sum``      ``off``         ``y2`` ``ffqn`` ``st``    ¬\ ``yf``
   ``VCC_pt2``    ``VCC_pt12`` ``sum``      ``on``          ``y2`` ``VCC``  ``st``    ¬\ ``yf``
   ``VCC_pt2``    ``VCC_pt12`` ``sum``      ``off``         ``y2`` ``y1``   ``st``    ``VCC``
   ============== ============ ============ =============== ====== ======== ========= =========

.. [1] Options :fuse:`xor_a_mux` and :fuse:`cas_mux` share a fuse.
.. [2] Options :fuse:`xor_invert` and :fuse:`reset` share a fuse.

.. _pt3_mux:
.. _gclr_mux:

PT3 routing group
-----------------

.. todo:: write this

.. table::
   :widths: auto

   ========== ========= ======= =====================
   Configuration        Routing
   -------------------- -----------------------------
   pt3_mux    gclr_mux  ST.I3   FF.AR
   ========== ========= ======= =====================
   ``ar``     ``GCLR``  ``GND`` ``pt3``\ ∨ \ ``GCLR``
   ``ar``     ``GND``   ``GND`` ``pt3``
   ``sum``    ``GCLR``  ``pt3`` ``GCLR``
   ``sum``    ``GND``   ``pt3`` ``GND``
   ========== ========= ======= =====================


.. _pt4_mux:
.. _pt4_func:
.. _gclk_mux:

PT4 routing group
-----------------

.. todo:: write this

.. table::
   :widths: auto

   ========== ========= ====================== ======= ====================== =======
   Configuration                               Routing
   ------------------------------------------- --------------------------------------
   pt4_mux    pt4_func  gclk_mux               ST.I4   FF.CLK                 FF.CE
   ========== ========= ====================== ======= ====================== =======
   ``clk_ce`` ``ce``    ``GCLK1``..\ ``GCLK3`` ``GND`` ``GCLK1``..\ ``GCLK3`` ``pt4``
   ``clk_ce`` ``clk``   —                      ``GND`` ``pt4``                ``VCC``
   ``sum``    ``ce``    ``GCLK1``..\ ``GCLK3`` ``pt4`` ``GCLK1``..\ ``GCLK3`` ``VCC``
   ``sum``    ``clk``   —                      ``pt4`` ``VCC``                ``VCC``
   ========== ========= ====================== ======= ====================== =======


.. _pt5_mux:
.. _pt5_func:
.. _oe_mux:

PT5 routing group
-----------------

.. todo:: write this

.. table::
   :widths: auto

   ========= ========= ==================== ======= ======= ==================
   Configuration                            Routing
   ---------------------------------------- ----------------------------------
   pt5_mux   pt5_func  oe_mux               ST.I5   FF.AS   IO.EN
   ========= ========= ==================== ======= ======= ==================
   —         —         ``GND``              —       —       ``GND``
   —         —         ``GOE1``..\ ``GOE6`` —       —       ``GOE1``..\ ``GOE6``
   ``as_oe`` ``oe``    ``VCC_pt5``          ``GND`` ``GND`` ``pt5``
   ``as_oe`` ``as``    —                    ``GND`` ``pt5`` —
   ``sum``   ``oe``    —                    ``pt5`` ``GND`` —
   ``sum``   ``as``    —                    ``pt5`` ?       —
   —         —         ``VCC_pt5``          —       —       ``VCC``
   ========= ========= ==================== ======= ======= ==================


.. _d_mux:
.. _dfast_mux:
.. _o_mux:

D/Q routing group
-----------------

.. todo:: write this

.. table::
   :widths: auto

   ========= ========== ============== ======== =======
   Configuration                       Routing
   ----------------------------------- ----------------
   d_mux     o_mux [3]_ dfast_mux [3]_ FF.D     IO.A
   ========= ========== ============== ======== =======
   ``comb``  ``sync``   ``pad``        ``xt``   ``ffq``
   ``fast``  ``sync``   ``pad``        ``ioq``  ``ffq``
   ``comb``  ``comb``   ``pt2``        ``xt``   ``xt``
   ``fast``  ``comb``   ``pt2``        ``pt2``  ``xt``
   ========= ========== ============== ======== =======

.. [3] Options :fuse:`o_mux` and :fuse:`dfast_mux` share a fuse.

.. note::

   The routing of ``PT2`` through :fuse:`dfast_mux` violates rule (1) because it happens regardless of the state of other fuses that affect ``PT2`` (:fuse:`pt2_mux`, etc).

.. _fb_mux:

FB routing group
----------------

.. todo:: write this

.. table::
   :widths: auto

   ============= =======
   Configuration Routing
   ------------- -------
   fb_mux        MC.FB
   ============= =======
   ``comb``      ``xt``
   ``sync``      ``ffq``
   ============= =======


.. _storage:
.. _reset:

FF/latch configuration
----------------------

.. todo:: write this
