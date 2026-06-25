from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from typing import List, Optional
from pydantic import BaseModel, Field

from src.domain.repositories.interfaces import IAICacheRepository, IMetricsRepository
from src.infrastructure.config import settings

# Setup google-genai runtime check
try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

logger = logging.getLogger("deadlock_app")


class DeadlockExplanation(BaseModel):
    why_occurred: str = Field(
        description="Detailed explanation of why deadlock occurred."
    )
    coffman_conditions: List[str] = Field(
        description="Coffman conditions satisfied with explanations."
    )
    processes_involved: List[str] = Field(
        description="Processes involved in the deadlock."
    )
    resources_blocking: List[str] = Field(
        description="Resources involved in the deadlock."
    )
    resolution_strategies: List[str] = Field(
        description="Remedies to resolve the current deadlock state."
    )
    prevention_techniques: List[str] = Field(
        description="Techniques to prevent this type of deadlock."
    )
    banker_recommendation: str = Field(
        description="How/when the Banker's Algorithm should be used to avoid this."
    )


class AIExplainerService:

    def __init__(
        self,
        cache_repo: IAICacheRepository,
        metrics_repo: IMetricsRepository,
    ) -> None:
        self.cache_repo = cache_repo
        self.metrics_repo = metrics_repo
        self.api_key = settings.GEMINI_API_KEY
        self.model = settings.GEMINI_MODEL

    async def explain_deadlock(
        self,
        deadlock_cycle: List[str],
        processes: List[str],
        resources: List[str],
        banker_summary: Optional[str] = None,
    ) -> DeadlockExplanation:
        prompt = self._build_prompt(
            deadlock_cycle, processes, resources, banker_summary
        )
        prompt_hash = self._get_hash(
            deadlock_cycle, processes, resources, banker_summary
        )

        # Check Cache
        cached = await self.cache_repo.get(prompt_hash)
        if cached:
            try:
                data = json.loads(cached["response_json"])
                logger.info(f"AI cache hit for hash: {prompt_hash}")
                return DeadlockExplanation(**data)
            except Exception as e:
                logger.error(f"Failed to parse cached response: {e}")

        # If cache miss or parse error, invoke Gemini API
        if not self.api_key or genai is None:
            logger.info("API Key missing or google-genai package not found. Using local fallback.")
            fallback = self._fallback_explanation(
                deadlock_cycle, processes, resources, banker_summary
            )
            return fallback

        # API Call with Retries
        try:
            client = genai.Client(api_key=self.api_key)

            def make_call():
                return client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=DeadlockExplanation,
                        temperature=0.2,
                    ),
                )

            # Retry logic
            response = await self._retry_async(make_call, retries=3, delay=1.0)
            text = getattr(response, "text", "")

            if text:
                data = json.loads(text)
                explanation = DeadlockExplanation(**data)

                # Track tokens
                usage = getattr(response, "usage_metadata", None)
                p_tokens = getattr(usage, "prompt_token_count", 0) or 0
                c_tokens = getattr(usage, "candidates_token_count", 0) or 0

                # Save cache
                await self.cache_repo.save(
                    prompt_hash=prompt_hash,
                    prompt=prompt,
                    response_json=text,
                    prompt_tokens=p_tokens,
                    completion_tokens=c_tokens,
                )

                # Record metrics
                await self.metrics_repo.add(
                    metric_type="token_count",
                    name="gemini_prompt_tokens",
                    value=float(p_tokens),
                    labels=json.dumps({"model": self.model}),
                )
                await self.metrics_repo.add(
                    metric_type="token_count",
                    name="gemini_completion_tokens",
                    value=float(c_tokens),
                    labels=json.dumps({"model": self.model}),
                )

                return explanation

        except Exception as exc:
            logger.error(f"Gemini API execution failed: {exc}")
            await self.metrics_repo.add(
                metric_type="error",
                name="gemini_api_error",
                value=1.0,
                labels=json.dumps({"error": str(exc)}),
            )

        # Fallback if API fails
        return self._fallback_explanation(
            deadlock_cycle, processes, resources, banker_summary
        )

    def _get_hash(
        self,
        cycle: List[str],
        processes: List[str],
        resources: List[str],
        banker_summary: Optional[str],
    ) -> str:
        key = f"{sorted(cycle)}-{sorted(processes)}-{sorted(resources)}-{banker_summary or ''}"
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    def _build_prompt(
        self,
        cycle: List[str],
        processes: List[str],
        resources: List[str],
        banker_summary: Optional[str],
    ) -> str:
        cycle_text = " -> ".join(cycle) if cycle else "No cycle detected"
        return f"""
You are an Operating Systems tutor. Explain the following deadlock scenario in structured JSON.

Deadlock cycle: {cycle_text}
Processes involved: {", ".join(processes) if processes else "None"}
Resources involved: {", ".join(resources) if resources else "None"}
Banker's Safety details: {banker_summary or "Not evaluated or unsafe"}

Please fill in all details for why the deadlock occurred, Coffman conditions, processes, resources, short-term resolution strategies, long-term prevention techniques, and recommendation regarding Banker's Safety algorithm.
"""

    def _fallback_explanation(
        self,
        cycle: List[str],
        processes: List[str],
        resources: List[str],
        banker_summary: Optional[str],
    ) -> DeadlockExplanation:
        cycle_text = " -> ".join(cycle) if cycle else "No cycle detected"
        return DeadlockExplanation(
            why_occurred=f"A circular dependency was detected: {cycle_text}. Processes are blocked waiting for resources held by one another.",
            coffman_conditions=[
                "Mutual Exclusion: Resources are non-shareable.",
                "Hold and Wait: Processes are holding allocated resources while waiting for new requests.",
                "No Preemption: Resources cannot be forcibly taken from processes.",
                "Circular Wait: A closed loop of requests and allocations exists.",
            ],
            processes_involved=processes or ["P1", "P2"],
            resources_blocking=resources or ["R1", "R2"],
            resolution_strategies=[
                "Kill one or more processes in the circular wait loop to break the dependency.",
                "Preempt resources from one process and allocate them to another.",
                "Force-release resources from blocked processes.",
            ],
            prevention_techniques=[
                "Resource Ordering: Enforce a global index ordering on all resource acquisitions.",
                "Hold and Wait prevention: Require processes to request all resources at startup.",
                "Preemption: Allow resource allocation requests to preempt existing holdings if priority permits.",
            ],
            banker_recommendation=banker_summary
            or "Always execute the Banker's safety check prior to resource allocations to ensure the system remains in a safe state.",
        )

    async def _retry_async(self, func, retries: int = 3, delay: float = 1.0) -> Any:
        last_exc = None
        for i in range(retries):
            try:
                # Execute in threadpool to avoid blocking event loop since google-genai is synchronous
                loop = asyncio.get_running_loop()
                return await loop.run_in_executor(None, func)
            except Exception as e:
                last_exc = e
                logger.warning(
                    f"Gemini API temporary failure on attempt {i+1}: {e}"
                )
                if i < retries - 1:
                    await asyncio.sleep(delay)
                    delay *= 2
        raise last_exc
