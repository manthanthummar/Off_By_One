from __future__ import annotations

import json
import logging
from typing import Optional
import httpx
from app.config import settings, SEVERITY_RANK
from app.models.schemas import Farm, Risk, Action

log = logging.getLogger("farmsense.advisor")


class LLMAdvisor:
    name = "LLMAdvisor"

    def advise(
        self, farm: Farm, risks: list[Risk], actions: list[Action]
    ) -> tuple[str, str, int]:
        """Return (text, source, output_tokens). Never raises; falls back to offline template."""
        if settings.anthropic_key:
            try:
                text, toks = self._llm(farm, risks, actions)
                if text:
                    return text, "llm", toks
            except Exception as exc:  # network, auth, rate-limit, parsing...
                log.warning("LLM advisor failed, using offline template: %s", exc)
        text = self.template(farm, risks, actions)
        return text, "offline", max(1, len(text) // 4)

    @staticmethod
    def template(farm: Farm, risks: list[Risk], actions: list[Action]) -> str:
        open_risks = sorted(
            (r for r in risks if r.status == "open"), key=lambda r: -SEVERITY_RANK[r.severity]
        )
        if not open_risks:
            return f"All plots on {farm.name} look healthy. Keep monitoring; nothing urgent today."
        tips = {
            "water_stress": "Irrigate early morning; check pump and channels.",
            "nutrient_deficiency": "Apply urea in two split doses (now and after 14 days).",
            "fungal_disease": "Scout first; any fungicide needs agronomist approval.",
            "vegetation_decline": "Inspect the plot for pests, waterlogging or nutrient issues.",
        }
        lines = [f"{r.severity.upper()} - {r.summary} {tips[r.kind]}" for r in open_risks[:4]]
        held = [
            a
            for a in actions
            if a.status in ("deferred", "skipped") and a.hold_reason == "weather"
        ]
        if held:
            lines.append(f"{len(held)} action(s) are on hold because of the weather forecast.")
        return "\n".join(lines)

    def _llm(self, farm: Farm, risks: list[Risk], actions: list[Action]) -> tuple[str, int]:
        payload = {
            "farm": farm.name,
            "risks": [
                {
                    "plot": r.plot_id,
                    "kind": r.kind,
                    "severity": r.severity,
                    "evidence": r.evidence,
                }
                for r in risks
                if r.status == "open"
            ],
            "actions": [
                {
                    "title": a.title,
                    "kind": a.kind,
                    "status": a.status,
                    "when": a.when.isoformat(),
                    "cost_inr": a.cost_inr,
                    "rationale": a.rationale,
                }
                for a in actions
            ],
        }
        system = (
            "You are an agronomy advisor for smallholder farmers. In under 120 words, plain language, "
            "explain the situation and priorities. Never recommend chemical spraying without "
            "agronomist approval. Output plain text only."
        )
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": settings.anthropic_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": settings.anthropic_model,
                    "max_tokens": 400,
                    "system": system,
                    "messages": [{"role": "user", "content": json.dumps(payload, default=str)}],
                },
            )
            resp.raise_for_status()
            data = resp.json()
        text = "".join(
            b.get("text", "") for b in data.get("content", []) if b.get("type") == "text"
        ).strip()
        return text, int(data.get("usage", {}).get("output_tokens", len(text) // 4))
