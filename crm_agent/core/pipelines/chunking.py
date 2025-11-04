from typing import List, Dict
import tiktoken


class TextChunker:
    def __init__(self, target_tokens: int = 500, overlap_tokens: int = 50):
        """More granular chunks (500 tokens) for better RAG retrieval on image-heavy brochures.
        
        Uses tiktoken (GPT-2 tokenizer) for accurate token counting.
        """
        self.target = target_tokens
        self.overlap = overlap_tokens
        # Use GPT-2 tokenizer as reasonable approximation for English text
        # (closest to what many LLMs use, though embeddings use different tokenization)
        self.encoder = tiktoken.get_encoding("gpt2")

    def _count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken."""
        return len(self.encoder.encode(text))

    def chunk(self, pages: List[Dict], project_name: str, source: str) -> List[Dict]:
        chunks: List[Dict] = []
        buf_text = ""
        buf_tokens = 0
        start_page = None

        def flush(end_page):
            nonlocal buf_text, buf_tokens, start_page
            if not buf_text.strip():
                return
            chunks.append({
                "text": buf_text.strip(),
                "metadata": {
                    "project_name": project_name,
                    "page": start_page,
                    "source": source,
                    "char_count": len(buf_text.strip()),
                    "token_count": buf_tokens
                }
            })
            # Keep overlap: preserve last N tokens for continuity
            if self.overlap > 0 and buf_tokens > self.overlap:
                tokens = self.encoder.encode(buf_text)
                overlap_tokens_list = tokens[-self.overlap:]
                buf_text = self.encoder.decode(overlap_tokens_list)
                buf_tokens = len(overlap_tokens_list)
                start_page = end_page
            else:
                buf_text = ""
                buf_tokens = 0
                start_page = None

        for p in pages:
            page_text = p["text"]
            if start_page is None:
                start_page = p["page"]
            
            # Add page text with space separator
            if buf_text:
                buf_text += " "
            buf_text += page_text
            buf_tokens = self._count_tokens(buf_text)
            
            # Flush when we hit target token count, continue if more remains
            while buf_tokens >= self.target:
                tokens = self.encoder.encode(buf_text)
                split_idx = min(self.target, len(tokens))
                
                # Extract chunk and remaining text
                chunk_tokens = tokens[:split_idx]
                remaining_tokens = tokens[split_idx:]
                
                # Set buffer to chunk for flushing
                buf_text = self.encoder.decode(chunk_tokens)
                buf_tokens = len(chunk_tokens)
                
                # Flush the chunk
                flush(p["page"])
                
                # Restore remaining text as new buffer
                buf_text = self.encoder.decode(remaining_tokens) if remaining_tokens else ""
                buf_tokens = len(remaining_tokens)
                
                # If nothing left, break
                if not buf_text.strip():
                    break
        
        # Flush remaining buffer
        if buf_text.strip():
            flush(pages[-1]["page"] if pages else start_page)
        
        return chunks


