"""Unit tests for the ``coax`` CLI's default LM construction."""

from __future__ import annotations


def describe_build_default_lm():
    def it_constrains_optimizer_rollouts_to_single_turn_no_tools():
        """Every GEPA rollout spawns an AgentLM subprocess. Without these
        constraints the bundled ``claude`` runs a full agentic session per
        rollout -- filesystem tools, unbounded multi-turn loops -- which
        makes ``coax --optimizer gepa`` take orders of magnitude longer
        than a classification call should. The optimizer asks the LM to
        produce a single structured response; one turn, no tools, is the
        correct envelope.
        """
        from coaxer.cli import _build_default_lm

        lm = _build_default_lm()

        assert lm.kwargs.get("tools") == [], (
            f"expected tools=[] to disable filesystem/agentic tools, got {lm.kwargs.get('tools')!r}"
        )
        assert lm.kwargs.get("max_turns") == 1, (
            f"expected max_turns=1 for single-shot classification, got {lm.kwargs.get('max_turns')!r}"
        )
