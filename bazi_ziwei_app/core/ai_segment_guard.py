"""Validate cloud answer segments and repair conflicts from the local plan."""

from __future__ import annotations

from dataclasses import dataclass

from core.ai_answer_guard import validate_ai_answer, validate_ai_text
from core.ai_intent import (
    CURRENT_MARRIAGE_DISCLAIMER,
)
from core.ai_models import (
    AIRequestContext,
    AnalysisPlan,
    BaziAIAnswer,
    CloudGeneration,
)


_CODE_MAP = {
    "timing_fact_contradiction": "GUARD_YEAR_CONFLICT",
    "dayun_contradiction": "GUARD_DAYUN_CONFLICT",
    "strength_contradiction": "GUARD_STRENGTH_CONFLICT",
    "pattern_contradiction": "GUARD_PATTERN_CONFLICT",
    "ten_god_contradiction": "GUARD_TEN_GOD_CONFLICT",
    "ten_god_count_contradiction": "GUARD_TEN_GOD_CONFLICT",
    "deterministic_claim": "GUARD_SCOPE_EXPANSION",
    "current_marriage_status_claim": "GUARD_SCOPE_EXPANSION",
}


@dataclass(frozen=True)
class SegmentGuardResult:
    answer_text: str
    violation_codes: tuple[str, ...]
    replaced_claim_ids: tuple[str, ...]
    full_fallback: bool


def _marriage_violation(
    text: str,
    context: AIRequestContext,
) -> tuple[str, ...]:
    if not (
        context.category == "relationship"
        and context.current_marriage_status_requested
    ):
        return ()
    probe = CURRENT_MARRIAGE_DISCLAIMER + text
    result = validate_ai_answer(
        BaziAIAnswer(
            analysis_conclusion=probe,
            chart_evidence=[],
            rule_evidence=[],
            timing_conditions=[],
            practical_advice=[],
            uncertainty_limitations=[],
        ),
        context,
    )
    return tuple(
        violation
        for violation in result.violations
        if violation == "current_marriage_status_claim"
    )


def _stable_codes(violations: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            _CODE_MAP.get(violation, "GUARD_SCOPE_EXPANSION")
            for violation in violations
        )
    )


def validate_and_repair_segments(
    generation: CloudGeneration,
    plan: AnalysisPlan,
    context: AIRequestContext,
) -> SegmentGuardResult:
    """Keep valid cloud prose and replace only invalid or omitted plan claims."""
    claims = {claim.id: claim for claim in plan.claims}
    for segment in generation.analysis.segments:
        if any(claim_id not in claims for claim_id in segment.claim_ids):
            return SegmentGuardResult(
                answer_text="",
                violation_codes=("CLOUD_STRUCTURE_INVALID",),
                replaced_claim_ids=(),
                full_fallback=True,
            )

    plan_order = {claim.id: index for index, claim in enumerate(plan.claims)}
    covered: set[str] = set()
    replaced: set[str] = set()
    cloud_paragraphs: dict[str, str] = {}
    codes: list[str] = []

    for segment in generation.analysis.segments:
        fresh_claim_ids = [
            claim_id
            for claim_id in segment.claim_ids
            if claim_id not in covered
        ]
        if not fresh_claim_ids:
            continue

        guard = validate_ai_text(segment.text, context)
        violations = tuple(
            dict.fromkeys(
                (
                    *guard.violations,
                    *_marriage_violation(
                        segment.text,
                        context,
                    ),
                )
            )
        )
        if violations:
            replaced.update(fresh_claim_ids)
            codes.extend(_stable_codes(violations))
        else:
            anchor = min(fresh_claim_ids, key=plan_order.__getitem__)
            cloud_paragraphs[anchor] = segment.text
        covered.update(fresh_claim_ids)

    replaced.update(claim_id for claim_id in claims if claim_id not in covered)
    paragraphs: list[str] = []
    for claim in plan.claims:
        if claim.id in replaced:
            paragraphs.append(claim.local_text)
        elif claim.id in cloud_paragraphs:
            paragraphs.append(cloud_paragraphs[claim.id])

    answer_text = "\n\n".join(paragraphs)
    if (
        answer_text
        and context.category == "relationship"
        and context.current_marriage_status_requested
    ):
        without_duplicate_disclaimers = [
            paragraph.removeprefix(CURRENT_MARRIAGE_DISCLAIMER)
            for paragraph in paragraphs
        ]
        answer_text = CURRENT_MARRIAGE_DISCLAIMER + "\n\n".join(
            paragraph
            for paragraph in without_duplicate_disclaimers
            if paragraph
        )

    return SegmentGuardResult(
        answer_text=answer_text,
        violation_codes=tuple(dict.fromkeys(codes)),
        replaced_claim_ids=tuple(
            claim.id for claim in plan.claims if claim.id in replaced
        ),
        full_fallback=False,
    )
