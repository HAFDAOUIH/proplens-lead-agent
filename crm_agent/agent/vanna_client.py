from typing import Dict, Any, Optional
import os
from dotenv import load_dotenv
import logging

# CRITICAL: Import patch module FIRST to apply OpenAI proxies fix
# This MUST happen before any Vanna or OpenAI imports
from crm_agent.agent.openai_patch import apply_openai_proxies_patch
apply_openai_proxies_patch()

# NOW import Vanna classes (after patching OpenAI)
from openai import OpenAI
from vanna.chromadb.chromadb_vector import ChromaDB_VectorStore
from vanna.openai.openai_chat import OpenAI_Chat

logger = logging.getLogger(__name__)
load_dotenv()


class VannaClient(ChromaDB_VectorStore, OpenAI_Chat):
    """
    Vanna T2SQL client using Groq (OpenAI-compatible) + ChromaDB.
    
    Uses mixin pattern: inherits from ChromaDB_VectorStore and OpenAI_Chat.
    Groq API is OpenAI-compatible, so we configure it to use Groq's endpoint.
    
    Based on Medium article approach
    """
    
    def __init__(self, chroma_dir: str, groq_api_key: Optional[str] = None, model: str = "llama-3.3-70b-versatile"):
        """
        Initialize Vanna with ChromaDB backend and Groq LLM.
        
        Args:
            chroma_dir: Directory for ChromaDB persistence
            groq_api_key: Groq API key (defaults to GROQ_API_KEY env var)
            model: Groq model name
        """
        self.chroma_dir = chroma_dir
        self.groq_api_key = groq_api_key or os.getenv("GROQ_API_KEY")
        self.model = model or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY must be provided or set in environment")
        
        # Configure for ChromaDB (following Medium article pattern)
        chroma_config = {'path': chroma_dir}
        ChromaDB_VectorStore.__init__(self, config=chroma_config)
        
        # Create OpenAI client configured for Groq (following Medium article pattern)
        # The monkey-patch ensures proxies is ignored if Vanna tries to pass it
        openai_client = OpenAI(
            api_key=self.groq_api_key,
            base_url="https://api.groq.com/openai/v1"
        )
        
        # Initialize OpenAI_Chat following Medium article pattern
        # Pass client directly, config separately
        openai_config = {'model': self.model}
        OpenAI_Chat.__init__(self, client=openai_client, config=openai_config)
        
        logger.info(f"VannaClient initialized with model: {self.model}, ChromaDB: {chroma_dir}")
    
    def ask(self, question: str) -> Dict[str, Any]:
        """
        Generate SQL from natural language question.
        
        Args:
            question: Natural language question (e.g., "How many leads total?")
            
        Returns:
            {
                "sql": str,
                "summary": str,
                "confidence": float,
                "error": Optional[str]
            }
        """
        try:
            # Generate SQL using Vanna (self is the Vanna instance)
            sql = self.generate_sql(question=question)
            
            if not sql or not sql.strip():
                return {
                    "sql": "",
                    "summary": "No SQL generated",
                    "confidence": 0.0,
                    "error": "Vanna could not generate SQL for this question"
                }
            
            # Validate SQL
            is_valid = self.is_sql_valid(sql=sql)
            if not is_valid:
                logger.warning(f"Generated SQL failed validation: {sql}")
            
            # Generate summary using available method
            # Vanna 0.x doesn't have explain_sql, so we create a simple summary
            try:
                # Try generate_summary if available (takes sql as input)
                summary = self.generate_summary(sql=sql)
            except (AttributeError, TypeError):
                # Fallback: create a simple summary from the SQL
                summary = f"Generated SQL query: {sql[:100]}..." if len(sql) > 100 else f"Generated SQL query: {sql}"
            
            # Get confidence (if available)
            confidence = getattr(self, 'confidence', None) or 0.8
            
            logger.info(f"Generated SQL for question: {question[:50]}...")
            logger.debug(f"SQL: {sql}")
            
            return {
                "sql": sql,
                "summary": summary,
                "confidence": confidence,
                "error": None
            }
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Vanna SQL generation error: {error_msg}")
            return {
                "sql": "",
                "summary": "",
                "confidence": 0.0,
                "error": error_msg
            }
    
    def add_training_item(self, item_type: str, content: str, question: Optional[str] = None):
        """
        Add training item to Vanna corpus.
        
        Args:
            item_type: Type of training item ("ddl", "sql", "documentation")
            content: Content to add
            question: Optional question for SQL examples
        """
        try:
            if item_type == "ddl":
                self.train(ddl=content)
            elif item_type == "sql":
                if not question:
                    raise ValueError("Question required for SQL training items")
                self.train(question=question, sql=content)
            elif item_type == "documentation":
                self.train(documentation=content)
            else:
                raise ValueError(f"Unknown training item type: {item_type}")
            
            logger.info(f"Added {item_type} training item to Vanna corpus")
            
        except Exception as e:
            logger.error(f"Error adding training item: {str(e)}")
            raise

