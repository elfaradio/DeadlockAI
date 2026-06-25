from __future__ import annotations

import json
import pytest
from unittest.mock import MagicMock, patch
from src.application.services.ai_explainer import AIExplainerService, DeadlockExplanation
from src.infrastructure.di.container import container


@pytest.mark.asyncio
async def test_ai_explainer_cache_hit() -> None:
    service = AIExplainerService(
        cache_repo=container.cache_repo,
        metrics_repo=container.metrics_repo,
    )

    cycle = ["P1", "R1", "P2", "R2", "P1"]
    procs = ["P1", "P2"]
    res = ["R1", "R2"]
    banker_summary = "Unsafe state."

    # Compute expected hash
    expected_hash = service._get_hash(cycle, procs, res, banker_summary)

    payload = {
        "why_occurred": "Cached occurrence rationale.",
        "coffman_conditions": ["Mutual Exclusion", "Circular Wait"],
        "processes_involved": ["P1"],
        "resources_blocking": ["R1"],
        "resolution_strategies": ["Strategy 1"],
        "prevention_techniques": ["Technique 1"],
        "banker_recommendation": "Banker recommendation.",
    }

    # Save cache
    await container.cache_repo.save(
        prompt_hash=expected_hash,
        prompt="Prompt text",
        response_json=json.dumps(payload),
        prompt_tokens=15,
        completion_tokens=25,
    )

    result = await service.explain_deadlock(
        deadlock_cycle=cycle,
        processes=procs,
        resources=res,
        banker_summary=banker_summary,
    )

    assert result.why_occurred == "Cached occurrence rationale."
    assert "Mutual Exclusion" in result.coffman_conditions


@pytest.mark.asyncio
async def test_ai_explainer_fallback_when_api_key_missing() -> None:
    # Temporarily unset API key in settings
    with patch("src.application.services.ai_explainer.settings.GEMINI_API_KEY", ""):
        service = AIExplainerService(
            cache_repo=container.cache_repo,
            metrics_repo=container.metrics_repo,
        )
        result = await service.explain_deadlock(
            deadlock_cycle=["P1", "R1", "P1"],
            processes=["P1"],
            resources=["R1"],
        )
        # Should return local fallback explanation
        assert "A circular dependency was detected" in result.why_occurred
        assert len(result.coffman_conditions) == 4


@pytest.mark.asyncio
async def test_ai_explainer_api_success_with_tokens_tracking() -> None:
    # Setup mock response
    mock_response = MagicMock()
    payload = {
        "why_occurred": "API success rationale.",
        "coffman_conditions": ["Circular Wait"],
        "processes_involved": ["P1"],
        "resources_blocking": ["R1"],
        "resolution_strategies": ["Kill process"],
        "prevention_techniques": ["Strict ordering"],
        "banker_recommendation": "Use Banker's Algorithm.",
    }
    mock_response.text = json.dumps(payload)
    mock_response.usage_metadata.prompt_token_count = 100
    mock_response.usage_metadata.candidates_token_count = 150

    # Mock genai.Client
    with patch("src.application.services.ai_explainer.genai") as mock_genai, \
         patch("src.application.services.ai_explainer.settings.GEMINI_API_KEY", "test-key"):
        
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        mock_client.models.generate_content.return_value = mock_response

        service = AIExplainerService(
            cache_repo=container.cache_repo,
            metrics_repo=container.metrics_repo,
        )

        result = await service.explain_deadlock(
            deadlock_cycle=["P1", "R1", "P1"],
            processes=["P1"],
            resources=["R1"],
            banker_summary="Unsafe",
        )

        assert result.why_occurred == "API success rationale."

        # Verify token metrics in database
        metrics = await container.metrics_repo.get_all()
        assert any(m["name"] == "gemini_prompt_tokens" and m["value"] == 100.0 for m in metrics)
        assert any(m["name"] == "gemini_completion_tokens" and m["value"] == 150.0 for m in metrics)


@pytest.mark.asyncio
async def test_ai_explainer_api_retry_behavior() -> None:
    # Setup a mock function that fails twice and then succeeds
    mock_calls = []

    def failing_then_succeeding_call(*args, **kwargs):
        mock_calls.append(1)
        if len(mock_calls) < 3:
            raise Exception("API Rate Limit Exceeded")
        mock_resp = MagicMock()
        payload = {
            "why_occurred": "Success after retries.",
            "coffman_conditions": [],
            "processes_involved": [],
            "resources_blocking": [],
            "resolution_strategies": [],
            "prevention_techniques": [],
            "banker_recommendation": "",
        }
        mock_resp.text = json.dumps(payload)
        mock_resp.usage_metadata.prompt_token_count = 50
        mock_resp.usage_metadata.candidates_token_count = 80
        return mock_resp

    with patch("src.application.services.ai_explainer.genai") as mock_genai, \
         patch("src.application.services.ai_explainer.settings.GEMINI_API_KEY", "test-key"):
        
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        mock_client.models.generate_content.side_effect = failing_then_succeeding_call

        service = AIExplainerService(
            cache_repo=container.cache_repo,
            metrics_repo=container.metrics_repo,
        )

        result = await service.explain_deadlock(
            deadlock_cycle=["P1", "R1", "P1"],
            processes=["P1"],
            resources=["R1"],
            banker_summary="Unsafe",
        )

        # Verify result and call counts
        assert result.why_occurred == "Success after retries."
        assert len(mock_calls) == 3
