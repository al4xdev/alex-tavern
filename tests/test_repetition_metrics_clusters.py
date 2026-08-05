"""The cluster scalars must be maxima, not whatever sorted first.

`cluster_span` was `clusters[0]["span"]` while the list is sorted by SIZE, so the
reported span belonged to the largest cluster instead of the widest one. A gate
had already been decided on that scalar (`.plan/tasks/68-...`), so it gets a test
that fails on the exact shape that hid the defect: the largest cluster is not the
widest, and the widest sits past the truncation point of the evidence listing.
"""

from __future__ import annotations

from tools.acceptance.repetition_metrics import (
    Stimulus,
    _cluster_stimuli,
    _cluster_summary,
)


def _cluster(size: int, span: int) -> dict:
    """A cluster of ``size`` turns whose first and last are ``span`` apart.

    ``span`` is ``turns[-1] - turns[0] + 1``, so it can never be smaller than the
    number of turns in the cluster; the fixtures respect that or they would be
    testing a shape the metric cannot produce.
    """
    assert span >= size
    turns = [1, *range(2, size), span]
    return {"turns": turns, "size": size, "span": span, "sample": f"size={size} span={span}"}


def test_span_is_the_maximum_not_the_largest_clusters_span():
    """The archive's shape: same-size clusters, and the widest sorts last.

    `base-P1-r2` has eight clusters of size 3 and reported a span of 5 while the
    true maximum is 15 — whichever size-3 cluster happened to sort first decided
    the number.
    """
    clusters = [
        _cluster(size=6, span=6),
        _cluster(size=3, span=5),
        _cluster(size=3, span=15),
        _cluster(size=2, span=30),
    ]

    summary = _cluster_summary(clusters)

    assert summary["cluster_max"] == 6
    assert summary["cluster_span"] == 30, "reported the first cluster's span, not the maximum"
    assert summary["cluster_count"] == 4
    assert summary["cluster_count_ge3"] == 3


def test_the_widest_cluster_survives_the_evidence_truncation():
    """`clusters[:5]` dropped the widest cluster out of the listing entirely."""
    clusters = [_cluster(size=6 - i, span=6) for i in range(5)]
    widest = _cluster(size=2, span=30)

    listed = _cluster_summary([*clusters, widest])["clusters"]

    assert widest in listed
    assert len(listed) == 6, "top five by size, plus the widest"


def test_no_clusters_reports_zero():
    summary = _cluster_summary([])
    assert summary["cluster_max"] == 0
    assert summary["cluster_span"] == 0
    assert summary["cluster_count"] == 0
    assert summary["clusters"] == []


def test_leader_clustering_finds_a_restaged_event_across_turns():
    """End to end on the shape this metric exists for: one situation, three turns.

    The three sentences are the ceiling collapse from `base-P1-r2` T33/T34/T35,
    verbatim. Their pairwise similarities (0.79 / 0.67 / 0.70) sit under the
    pairwise `DEFAULT_TAU` of 0.8 and above `CLUSTER_TAU` of 0.6 — which is the
    whole reason the cluster metric runs at a looser threshold.
    """
    stimuli = [
        Stimulus(
            turn_number=33,
            event_kind="physical_outcome",
            subject_id="C1",
            content=(
                "O teto da camara oculta desaba com um estrondo, abrindo um buraco de onde a "
                "nevoa verde jorra em jato direto para o patio, e a entrada fica soterrada."
            ),
        ),
        Stimulus(
            turn_number=34,
            event_kind="observation",
            subject_id="C1",
            content=(
                "O teto da camara oculta desaba com um rugido, abrindo um buraco por onde um "
                "jato espesso de nevoa verde dispara em direcao ao patio, enquanto a entrada "
                "fica soterrada por blocos."
            ),
        ),
        Stimulus(
            turn_number=35,
            event_kind="physical_outcome",
            subject_id="C1",
            content=(
                "O teto da camara oculta desaba com estrondo, e um jato espesso de nevoa verde "
                "dispara pelo buraco em direcao ao patio externo."
            ),
        ),
        Stimulus(
            turn_number=36,
            event_kind="speech",
            subject_id="C2",
            content="Bruna corre ate a escada e chama os alunos que ficaram no corredor leste.",
        ),
    ]

    clusters = _cluster_stimuli(stimuli)
    summary = _cluster_summary(clusters)

    assert summary["cluster_max"] == 3
    assert summary["cluster_span"] == 3
    assert summary["cluster_count_ge3"] == 1


def test_one_turn_recurrence_is_staging_not_repetition():
    """Several facets of one event inside a single turn must not cluster."""
    stimuli = [
        Stimulus(33, "physical_outcome", "C1", "O teto da camara desaba com um estrondo."),
        Stimulus(33, "observation", "C1", "O teto da camara desaba com um estrondo forte."),
    ]

    assert _cluster_stimuli(stimuli) == []
