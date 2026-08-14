from app.main import (
    OpportunityCreate,
    calculate_score,
    generate_outreach,
    policy_outcome,
    score_tier,
    select_offer,
)


def strong_opportunity() -> OpportunityCreate:
    return OpportunityCreate(
        company="National Electric Coil",
        industry="Electrical manufacturing",
        location="Texas",
        contact_name="Operations Leader",
        contact_email="leader@example.com",
        signal="The company needs a replacement workforce partner for winding operations.",
        estimated_value=250000,
        urgency=9,
        buyer_access=8,
        delivery_fit=9,
        payment_risk=2,
        staffing_difficulty=6,
        competition=4,
        evidence=["Direct executive request"],
    )


def test_score_and_tier_for_strong_opportunity() -> None:
    opportunity = strong_opportunity()
    score = calculate_score(opportunity)
    assert score >= 80
    assert score_tier(score) == "A"


def test_offer_selection_prefers_vendor_replacement() -> None:
    opportunity = strong_opportunity()
    assert select_offer(opportunity.industry, opportunity.signal) == "vendor_replacement"


def test_policy_routes_qualified_account_to_approval() -> None:
    opportunity = strong_opportunity()
    data = opportunity.model_dump()
    status, rationale = policy_outcome(data, calculate_score(data))
    assert status == "approval_required"
    assert "threshold" in rationale.lower()


def test_high_payment_risk_requires_human_review() -> None:
    opportunity = strong_opportunity()
    data = opportunity.model_dump()
    data["payment_risk"] = 9
    status, _ = policy_outcome(data, calculate_score(data))
    assert status == "human_review"


def test_outreach_uses_approved_facts() -> None:
    opportunity = strong_opportunity()
    data = opportunity.model_dump()
    subject, body = generate_outreach(data, "vendor_replacement")
    assert opportunity.company in subject
    assert opportunity.signal in body
    assert "GH Service Group" in body
