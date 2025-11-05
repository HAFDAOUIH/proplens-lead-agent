from typing import Dict, Any, List, Optional
import os
from openai import OpenAI
from crm_agent.core.vector_store import ChromaStore


class RagTool:
    def __init__(
        self,
        chroma_dir: str,
        collection: str = "brochures",
        summarize: bool = True,
        groq_api_key: Optional[str] = None,
        model: str = "llama-3.3-70b-versatile"
    ):
        self.store = ChromaStore(persist_dir=chroma_dir, collection=collection, embed_model="all-MiniLM-L6-v2")
        self.summarize = summarize

        # Initialize Groq client for summarization
        if summarize:
            self.groq_api_key = groq_api_key or os.getenv("GROQ_API_KEY")
            self.model = model or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
            self.client = OpenAI(
                api_key=self.groq_api_key,
                base_url="https://api.groq.com/openai/v1"
            ) if self.groq_api_key else None

    def _summarize_text(self, query: str, context: str) -> str:
        """Summarize RAG context using Groq LLM, targeting ~150 words."""
        if not self.client:
            # Fallback to truncation if no API key (~150 words ≈ 750 chars)
            return self._truncate_to_words(context, 150)

        try:
            system = (
                "You are a helpful assistant that answers questions about real estate properties "
                "based on provided context. Be VERY concise - aim for approximately 150 words maximum. "
                "Focus only on directly answering the question with the most relevant information."
            )
            user = (
                f"Question: {query}\n\n"
                f"Context:\n{context}\n\n"
                "Provide a clear, concise answer in approximately 150 words or less. "
                "Use bullet points if listing multiple items."
            )

            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user}
                ],
                temperature=0.3,
                max_tokens=200  # ~150 words = ~200 tokens
            )

            answer = resp.choices[0].message.content.strip()

            # Ensure answer doesn't exceed 150 words
            return self._truncate_to_words(answer, 150)

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"RAG summarization error: {str(e)}")
            # Fallback to truncation on error
            return self._truncate_to_words(context, 150)

    @staticmethod
    def _truncate_to_words(text: str, max_words: int = 150) -> str:
        """Truncate text to maximum number of words."""
        words = text.split()
        if len(words) <= max_words:
            return text
        truncated = " ".join(words[:max_words])
        return truncated + "..."

    def answer(self, query: str, k: int = 4, project: Optional[str] = None) -> Dict[str, Any]:
        matches = self.store.search(query=query, k=k, project_name=project)
        combined = " ".join([m.get("text", "") for m in matches])

        # Summarize the answer if enabled
        if self.summarize and combined:
            answer = self._summarize_text(query, combined)
        else:
            answer = self._truncate_to_words(combined, 150)

        # Normalize distances and compute similarity scores
        sources = []
        for m in matches:
            distance = m.get("distance", 0)
            # Convert distance to similarity (0-1 scale, where 1 is most similar)
            # Cosine distance ranges from 0 (identical) to 2 (opposite)
            # Normalize to 0-1 where 1 is best match
            similarity = max(0.0, min(1.0, 1.0 - (distance / 2.0)))

            project_name = m.get("metadata", {}).get("project_name")

            sources.append({
                "project": project_name or "Unknown",  # Ensure project is never None
                "page": m.get("metadata", {}).get("page"),
                "source": m.get("metadata", {}).get("source"),
                "distance": round(distance, 3),
                "similarity": round(similarity, 3)
            })

        return {
            "answer": answer,
            "sources": sources,
        }


