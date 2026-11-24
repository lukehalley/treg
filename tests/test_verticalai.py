"""Vertical AI placed calls: each paid route runs on treg's key, priced at US$0.12 per answered
minute (one verticalai credit) and settled from the finished call's billableMinutes. See
src/treg/catalog/verticalai.yaml."""
from __future__ import annotations

from treg.domain.capacity import signatures as S
from treg.domain.catalog import store as cs


def test_every_paid_verticalai_route_is_platform_priced():
    cat = cs.load()
    eps = [e for e in cat.endpoints if e["provider"] == "verticalai"]
    assert eps
    for ep in eps:
        if ep["cost"]["type"] == "free" or ep.get("scope") == "own_account":
            continue
        assert cat.platform_eligible(ep), ep["id"]
        assert cat.cost_view(ep["cost"], "verticalai")["usd"] > 0, ep["id"]


def test_an_answered_minute_costs_twelve_cents():
    cat = cs.load()
    place = cat.by_id["verticalai.phone.call.place"]
    assert cat.cost_view(place["cost"], "verticalai")["usd"] == 0.12


def test_the_hold_never_falls_short_of_the_settle():
    cat = cs.load()
    assert cat.by_id["verticalai.phone.call.place"]["cost"]["worst_case"] == 10
    assert cat.by_id["verticalai.people.contact.verify"]["cost"]["worst_case"] == 1


def test_a_workspace_that_cannot_pay_is_out_of_credits_and_a_plan_gate_is_not():
    for code in ("spend_cap_reached", "card_required", "account_past_due", "subscription_canceled",
                 "plan_required", "trial_used", "billing_blocked"):
        body = ('{"type":"about:blank","title":"Payment Required","status":402,"code":"%s",'
                '"detail":"This workspace can\'t place calls until its billing is sorted. Check Plan and usage."}' % code)
        sig = S.classify("verticalai", 402, {}, body.encode())
        assert sig is not None and S.is_exhausting(sig), code
    locked = b'{"title":"Payment Required","status":402,"code":"plan_feature_locked","detail":"Outbound calling is on the Scale plan."}'
    sig = S.classify("verticalai", 402, {}, locked)
    assert sig is None or not S.is_exhausting(sig)
