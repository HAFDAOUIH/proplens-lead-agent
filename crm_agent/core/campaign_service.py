"""
Campaign Service - Generates personalized outreach messages using RAG + Lead profiles.
"""
from typing import List, Dict, Any, Optional
import os
from openai import OpenAI
from crm_agent.core.vector_store import ChromaStore


class CampaignService:
    """Generates hyper-personalized campaign messages using lead data and RAG."""

    def __init__(
        self,
        chroma_dir: str,
        groq_api_key: Optional[str] = None,
        model: str = "llama-3.3-70b-versatile"
    ):
        self.store = ChromaStore(
            persist_dir=chroma_dir,
            collection="brochures",
            embed_model="all-MiniLM-L6-v2"
        )
        self.groq_api_key = groq_api_key or os.getenv("GROQ_API_KEY")
        self.model = model or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY required for campaign generation")

        self.client = OpenAI(
            api_key=self.groq_api_key,
            base_url="https://api.groq.com/openai/v1"
        )

    def generate_email(
        self,
        lead: Dict[str, Any],
        project: str,
        offer_text: str = "",
        k: int = 3
    ) -> Dict[str, str]:
        """
        Generate a personalized email for a lead.

        Args:
            lead: Dictionary with lead info (name, email, budget_min, budget_max, unit_type, etc.)
            project: Project name to search in brochures
            offer_text: Optional campaign offer text
            k: Number of brochure chunks to retrieve

        Returns:
            Dict with 'subject' and 'body' keys
        """
        # 1. Build personalization context from lead profile
        lead_context = self._build_lead_context(lead)

        # 2. Retrieve relevant brochure content for the project
        query = f"{project} amenities features pricing {lead.get('unit_type', '')}"
        matches = self.store.search(query=query, k=k, project_name=project)
        brochure_context = "\n\n".join([
            f"[Page {m.get('metadata', {}).get('page', '?')}] {m.get('text', '')}"
            for m in matches
        ])

        # 3. Generate personalized email
        return self._generate_with_llm(lead_context, brochure_context, project, offer_text)

    def _build_lead_context(self, lead: Dict[str, Any]) -> str:
        """Build a concise context string from lead profile."""
        parts = [f"Lead: {lead.get('name', 'Customer')}"]

        if lead.get('unit_type'):
            parts.append(f"Interested in: {lead['unit_type']}")

        if lead.get('budget_min') and lead.get('budget_max'):
            parts.append(
                f"Budget: AED {lead['budget_min']:,.0f} - {lead['budget_max']:,.0f}"
            )

        if lead.get('last_conversation_summary'):
            parts.append(f"Previous context: {lead['last_conversation_summary']}")

        return " | ".join(parts)

    def _generate_with_llm(
        self,
        lead_context: str,
        brochure_context: str,
        project: str,
        offer_text: str
    ) -> Dict[str, str]:
        """Use Groq LLM to generate personalized email."""
        system_prompt = (
            "You are a professional real estate agent writing personalized emails to potential buyers. "
            "Your emails should be:\n"
            "- Warm and professional\n"
            "- Highlight features matching the lead's preferences\n"
            "- Include specific details from the brochure\n"
            "- Keep the email concise (200-250 words)\n"
            "- End with a clear call-to-action\n"
            "- Use a natural, conversational tone"
        )

        user_prompt = f"""Write a personalized email for this lead:

{lead_context}

About this project: {project}

Relevant project information:
{brochure_context}

{f'Special offer: {offer_text}' if offer_text else ''}

Generate:
1. A compelling subject line (max 60 characters)
2. A personalized email body (200-250 words)

Format your response as:
SUBJECT: [subject line]
BODY:
[email body]
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=400
            )

            content = response.choices[0].message.content.strip()
            return self._parse_email_response(content)

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Email generation error: {str(e)}")

            # Fallback to template
            return {
                "subject": f"Exclusive opportunity at {project}",
                "body": f"Dear {lead_context.split(':')[1].split('|')[0].strip()},\n\n"
                        f"I wanted to reach out about {project}. "
                        f"Based on your interest, I believe this property would be perfect for you.\n\n"
                        f"{offer_text if offer_text else 'Let me know if you would like to schedule a visit.'}\n\n"
                        f"Best regards"
            }

    @staticmethod
    def _parse_email_response(content: str) -> Dict[str, str]:
        """Parse LLM response into subject and body."""
        lines = content.split('\n')
        subject = ""
        body_lines = []
        in_body = False

        for line in lines:
            if line.startswith("SUBJECT:"):
                subject = line.replace("SUBJECT:", "").strip()
            elif line.startswith("BODY:"):
                in_body = True
            elif in_body:
                body_lines.append(line)

        body = '\n'.join(body_lines).strip()

        # Fallback if parsing fails
        if not subject:
            subject = lines[0][:60] if lines else "Your perfect property awaits"
        if not body:
            body = content

        return {
            "subject": subject,
            "body": body
        }
