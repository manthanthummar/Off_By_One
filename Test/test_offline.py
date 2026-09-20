from __future__ import annotations

import httpx
from app.models.schemas import Farm, Risk, Action, now
from app.agents.advisor import LLMAdvisor
from app.config import settings


def test_offline_mode_without_anthropic_key():
    advisor = LLMAdvisor()
    farm = Farm(id="f1", name="Offline Farm")
    risks = [
        Risk(
            farm_id="f1",
            plot_id="p1",
            kind="water_stress",
            severity="critical",
            score=95,
            summary="Soil moisture 10%",
        )
    ]
    actions = [
        Action(
            farm_id="f1",
            plot_id="p1",
            risk_id=risks[0].id,
            kind="irrigate",
            title="Irrigate",
            what="Irrigate",
            when=now(),
            where="p1",
            status="planned",
        )
    ]

    # Without API key
    settings.anthropic_api_key = ""
    text, source, toks = advisor.advise(farm, risks, actions)
    assert source == "offline"
    assert "CRITICAL" in text
    assert "Irrigate early morning" in text
    assert toks > 0


def test_offline_fallback_on_llm_exception(mocker):
    advisor = LLMAdvisor()
    farm = Farm(id="f1", name="Error Farm")
    risks = [
        Risk(
            farm_id="f1",
            plot_id="p1",
            kind="fungal_disease",
            severity="high",
            score=75,
            summary="High fungal risk",
        )
    ]

    # Temporarily pretend an API key is set
    mocker.patch.object(settings, "anthropic_api_key", "sk-mock-key")

    # Mock httpx.Client.post to raise an HTTP error
    mock_post = mocker.patch("httpx.Client.post", side_effect=httpx.ConnectError("Network unreachable"))

    text, source, toks = advisor.advise(farm, risks, [])
    assert source == "offline"
    assert "HIGH" in text
    assert "Scout first" in text
    assert mock_post.called
