from typing import Optional, Union, List
from pydantic import BaseModel, Field, field_validator
import os
from openai import OpenAI


class RouteDecision(BaseModel):
    route: str = Field(pattern="^(rag|t2sql|clarify)$")
    confidence: float
    reasons: str

    @field_validator('reasons', mode='before')
    @classmethod
    def convert_reasons_to_string(cls, v):
        """Convert reasons from list to string if needed."""
        if isinstance(v, list):
            return " ".join(v)
        return v


class RouterLLM:
    def __init__(self, model: Optional[str] = None, api_key: Optional[str] = None, base_url: str = "https://api.groq.com/openai/v1"):
        self.model = model or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        self.client = OpenAI(api_key=api_key or os.getenv("GROQ_API_KEY"), base_url=base_url)

    def classify(self, question: str, history: Optional[List[str]] = None) -> RouteDecision:
        system = (
            "You classify user questions for a real estate CRM into {rag|t2sql|clarify}. "
            "rag = brochure/docs semantic questions (amenities, floor plans, features). "
            "t2sql = database analytics (counts, filters, aggregations over leads). "
            "clarify = cannot decide confidently."
        )

        # Build user message with optional conversation history
        user_parts = []
        if history and len(history) > 0:
            user_parts.append(f"Previous questions: {', '.join(history[-3:])}")
        user_parts.append(f"Current question: {question}")
        user_parts.append("Return strict JSON with keys route, confidence (0..1), reasons.")
        user = "\n".join(user_parts)

        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                temperature=0.0,
            )

            import json
            import logging
            logger = logging.getLogger(__name__)

            content = resp.choices[0].message.content.strip()

            # Debug log the raw response
            logger.debug(f"Router LLM raw response: {content}")

            if not content:
                logger.error("Empty response from Groq API")
                # Fallback to RAG for empty responses
                return RouteDecision(route="rag", confidence=0.5, reasons="Empty LLM response, defaulting to RAG")

            # Extract JSON from markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            # Try to parse JSON
            try:
                data = json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response as JSON: {content}")
                # Fallback to RAG
                return RouteDecision(route="rag", confidence=0.5, reasons=f"JSON parse error: {str(e)}")

            return RouteDecision(**data)

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Router classification error: {str(e)}")
            # Fallback to RAG on any error
            return RouteDecision(route="rag", confidence=0.5, reasons=f"Router error: {str(e)}")


