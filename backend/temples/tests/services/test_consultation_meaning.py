# backend/temples/tests/services/test_consultation_meaning.py
"""Consultation Meaning v1 extraction contract tests.

Covers all 10 SignalTypes' positive cases plus the shared guards
(negation, double negation, third-person, reported speech, topic-only,
homonym/ambiguity, delegated desire) and cross-cutting behavior (same-type
evidence aggregation, empty input, need_tag independence).
"""

from temples.services.consultation_meaning import (
    StructuredConsultationContextV1,
    extract_consultation_meaning,
)


def _types(signals):
    return {s.type for s in signals}


def _evidence_texts(signals, sig_type):
    for s in signals:
        if s.type == sig_type:
            return [e.text for e in s.evidence]
    return None


class TestSituationSignalsPositive:
    def test_depleted(self):
        ctx = extract_consultation_meaning("最近ずっと疲れている")
        assert "depleted" in _types(ctx.situation_signals)
        assert _evidence_texts(ctx.situation_signals, "depleted") == ["疲れている"]

    def test_undecided(self):
        ctx = extract_consultation_meaning("転職するか迷っている")
        assert "undecided" in _types(ctx.situation_signals)
        assert _evidence_texts(ctx.situation_signals, "undecided") == ["迷っている"]

    def test_stalled(self):
        ctx = extract_consultation_meaning("何も進まなくて詰まっている")
        assert "stalled" in _types(ctx.situation_signals)
        assert _evidence_texts(ctx.situation_signals, "stalled") == ["詰まっている"]


class TestDesiredOutcomeSignalsPositive:
    def test_decide(self):
        ctx = extract_consultation_meaning("そろそろ決めたい")
        assert "decide" in _types(ctx.desired_outcome_signals)
        assert _evidence_texts(ctx.desired_outcome_signals, "decide") == ["決めたい"]

    def test_clarify(self):
        ctx = extract_consultation_meaning("気持ちを整理したい")
        assert "clarify" in _types(ctx.desired_outcome_signals)
        assert _evidence_texts(ctx.desired_outcome_signals, "clarify") == ["整理したい"]

    def test_progress(self):
        ctx = extract_consultation_meaning("一歩踏み出したい")
        assert "progress" in _types(ctx.desired_outcome_signals)

    def test_calm(self):
        ctx = extract_consultation_meaning("落ち着きたい")
        assert "calm" in _types(ctx.desired_outcome_signals)
        assert _evidence_texts(ctx.desired_outcome_signals, "calm") == ["落ち着きたい"]


class TestExplicitConstraintSignalsPositive:
    def test_time(self):
        ctx = extract_consultation_meaning("忙しくて余裕がない")
        assert "time" in _types(ctx.explicit_constraint_signals)
        assert _evidence_texts(ctx.explicit_constraint_signals, "time") == ["余裕がない"]

    def test_money(self):
        ctx = extract_consultation_meaning("お金が足りなくて動けない")
        assert "money" in _types(ctx.explicit_constraint_signals)
        assert _evidence_texts(ctx.explicit_constraint_signals, "money") == ["お金が足りなくて"]

    def test_other_person_availability(self):
        ctx = extract_consultation_meaning("相手の都合で決められない")
        assert "other_person_availability" in _types(ctx.explicit_constraint_signals)


class TestNegation:
    def test_depleted_negated(self):
        ctx = extract_consultation_meaning("疲れてはいない")
        assert "depleted" not in _types(ctx.situation_signals)

    def test_undecided_negated(self):
        ctx = extract_consultation_meaning("迷っているわけではない")
        assert "undecided" not in _types(ctx.situation_signals)

    def test_stalled_negated(self):
        ctx = extract_consultation_meaning("動けないわけではない")
        assert "stalled" not in _types(ctx.situation_signals)

    def test_decide_negated(self):
        ctx = extract_consultation_meaning("決めたいわけではない")
        assert "decide" not in _types(ctx.desired_outcome_signals)

    def test_negation_does_not_leak_across_clauses(self):
        """疲れてはいないが、迷っている -- negation on one clause must not
        suppress an independent signal in a different clause."""
        ctx = extract_consultation_meaning("疲れてはいないが、迷っている")
        types = _types(ctx.situation_signals)
        assert "depleted" not in types
        assert "undecided" in types


class TestDoubleNegation:
    def test_money_double_negation_is_no_signal(self):
        """お金がないわけではない must not be resolved back to an
        affirmative reading -- fail-safe No-signal per the contract."""
        ctx = extract_consultation_meaning("お金がないわけではない")
        assert "money" not in _types(ctx.explicit_constraint_signals)


class TestThirdPerson:
    def test_depleted_third_person(self):
        ctx = extract_consultation_meaning("友人が疲れている")
        assert "depleted" not in _types(ctx.situation_signals)

    def test_undecided_third_person(self):
        ctx = extract_consultation_meaning("彼女が迷っている")
        assert "undecided" not in _types(ctx.situation_signals)

    def test_other_person_availability_still_fires_with_possessive_form(self):
        """「家族の事情で」uses の(possessive), not が(subject marker) --
        must not be caught by the third-person-subject guard."""
        ctx = extract_consultation_meaning("家族の事情で決められない")
        assert "other_person_availability" in _types(ctx.explicit_constraint_signals)


class TestReportedSpeech:
    def test_depleted_reported_speech(self):
        ctx = extract_consultation_meaning("疲れているらしい")
        assert "depleted" not in _types(ctx.situation_signals)

    def test_decide_reported_speech(self):
        ctx = extract_consultation_meaning("決めたいと言っていた")
        assert "decide" not in _types(ctx.desired_outcome_signals)


class TestTopicOnly:
    def test_depleted_topic_only(self):
        ctx = extract_consultation_meaning("疲労回復の方法を知りたい")
        assert "depleted" not in _types(ctx.situation_signals)

    def test_decide_topic_only(self):
        ctx = extract_consultation_meaning("決断力について本で読んだ")
        assert "decide" not in _types(ctx.desired_outcome_signals)

    def test_time_bare_domain_word_is_topic_only(self):
        ctx = extract_consultation_meaning("時間について相談したい")
        assert "time" not in _types(ctx.explicit_constraint_signals)

    def test_money_bare_domain_word_is_topic_only(self):
        ctx = extract_consultation_meaning("収入について聞きたい")
        assert "money" not in _types(ctx.explicit_constraint_signals)

    def test_busy_alone_must_not_produce_time(self):
        """忙しい単独(不足マーカーなし)はtimeを生成しない -- explicit
        Extraction Contract requirement."""
        ctx = extract_consultation_meaning("最近忙しい")
        assert "time" not in _types(ctx.explicit_constraint_signals)


class TestAmbiguityHomonym:
    def test_clarify_physical_tidying_homonym_suppressed(self):
        ctx = extract_consultation_meaning("部屋を整理したい")
        assert "clarify" not in _types(ctx.desired_outcome_signals)

    def test_clarify_thought_organizing_still_fires(self):
        ctx = extract_consultation_meaning("気持ちを整理したい")
        assert "clarify" in _types(ctx.desired_outcome_signals)

    def test_calm_aesthetic_homonym_does_not_match(self):
        """落ち着いた色が好き uses the attributive form (落ち着いた), not
        the desiderative form (落ち着きたい) -- must not match calm."""
        ctx = extract_consultation_meaning("落ち着いた色が好き")
        assert "calm" not in _types(ctx.desired_outcome_signals)


class TestDelegatedDesire:
    def test_decide_delegated_to_third_party_does_not_fire(self):
        ctx = extract_consultation_meaning("彼に決めてほしい")
        assert "decide" not in _types(ctx.desired_outcome_signals)


class TestSameTypeEvidenceAggregation:
    def test_multiple_evidence_spans_aggregate_into_one_signal(self):
        ctx = extract_consultation_meaning("本当に疲れている。もう疲労がたまっている。")
        depleted_evidence = _evidence_texts(ctx.situation_signals, "depleted")
        assert depleted_evidence is not None
        assert len(depleted_evidence) == 2
        assert "疲れている" in depleted_evidence
        assert "疲労がたまっている" in depleted_evidence
        # exactly one SituationSignal entry for depleted, not two
        assert len([s for s in ctx.situation_signals if s.type == "depleted"]) == 1

    def test_duplicate_identical_spans_are_not_repeated(self):
        ctx = extract_consultation_meaning("疲れている。本当に疲れている。")
        depleted_evidence = _evidence_texts(ctx.situation_signals, "depleted")
        assert depleted_evidence == ["疲れている"]


class TestCrossSignalCooccurrence:
    def test_different_families_from_different_spans_both_fire(self):
        """迷っていて、整理したい -- situation:undecided + desiredOutcome:
        clarify from distinct evidence spans, per the approved contract
        example."""
        ctx = extract_consultation_meaning("迷っていて、整理したい")
        assert "undecided" in _types(ctx.situation_signals)
        assert "clarify" in _types(ctx.desired_outcome_signals)
        assert _evidence_texts(ctx.situation_signals, "undecided") == ["迷っていて"]

    def test_same_family_different_spans_both_fire(self):
        ctx = extract_consultation_meaning("疲れて動けない")
        assert "depleted" in _types(ctx.situation_signals)
        assert "stalled" in _types(ctx.situation_signals)


class TestEmptyAndNoSignalInput:
    def test_empty_string_returns_all_empty_arrays(self):
        ctx = extract_consultation_meaning("")
        assert ctx.situation_signals == []
        assert ctx.desired_outcome_signals == []
        assert ctx.explicit_constraint_signals == []

    def test_none_input_returns_all_empty_arrays(self):
        ctx = extract_consultation_meaning(None)
        assert ctx.situation_signals == []
        assert ctx.desired_outcome_signals == []
        assert ctx.explicit_constraint_signals == []

    def test_unrelated_text_returns_all_empty_arrays(self):
        ctx = extract_consultation_meaning("今日はいい天気ですね")
        assert ctx.situation_signals == []
        assert ctx.desired_outcome_signals == []
        assert ctx.explicit_constraint_signals == []


class TestNeedTagIndependence:
    def test_function_accepts_only_free_text(self):
        """extract_consultation_meaning must accept only free_text -- no
        need_tags/Recommendation-derived parameter exists to pass."""
        import inspect

        sig = inspect.signature(extract_consultation_meaning)
        assert list(sig.parameters.keys()) == ["free_text"]


class TestSerialization:
    def test_as_dict_empty_context_has_all_three_empty_arrays(self):
        ctx = StructuredConsultationContextV1()
        assert ctx.as_dict() == {
            "situation_signals": [],
            "desired_outcome_signals": [],
            "explicit_constraint_signals": [],
        }

    def test_as_dict_shape_matches_stable_contract(self):
        ctx = extract_consultation_meaning("疲れていて、整理したい")
        d = ctx.as_dict()
        assert set(d.keys()) == {
            "situation_signals",
            "desired_outcome_signals",
            "explicit_constraint_signals",
        }
        for sig in d["situation_signals"]:
            assert set(sig.keys()) == {"type", "evidence"}
            for ev in sig["evidence"]:
                assert set(ev.keys()) == {"text"}
