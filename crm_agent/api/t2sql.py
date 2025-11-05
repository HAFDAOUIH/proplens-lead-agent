from ninja import Router
from ninja.errors import HttpError
from dotenv import load_dotenv
import os
import logging

from crm_agent.core.schemas import T2SQLQuery
from crm_agent.agent.vanna_client import VannaClient
from crm_agent.agent.sql_executor import SQLExecutor

load_dotenv()

router = Router(tags=["t2sql"])

logger = logging.getLogger(__name__)

CHROMA_DIR = os.getenv("CHROMA_DIR", "/home/hafdaoui/Documents/Proplens/crm_agent/data/chroma")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")


@router.post("/t2sql/query")
def query_t2sql(request, payload: T2SQLQuery):
    """
    Execute natural language query → SQL → results.
    
    Example questions:
    - "How many leads total?"
    - "Show all Connected leads"
    - "Count leads by project"
    """
    if not payload.question or not payload.question.strip():
        raise HttpError(400, "Question is required")
    
    try:
        # Initialize Vanna client
        vanna_client = VannaClient(
            chroma_dir=CHROMA_DIR,
            groq_api_key=GROQ_API_KEY,
            model=GROQ_MODEL
        )
        
        # Generate SQL from question
        result = vanna_client.ask(payload.question)
        
        if result["error"]:
            return {
                "question": payload.question,
                "sql": "",
                "rows": [],
                "row_count": 0,
                "summary": "",
                "error": result["error"]
            }
        
        # Execute SQL safely
        executor = SQLExecutor()
        exec_result = executor.execute(result["sql"])
        
        if exec_result["error"]:
            return {
                "question": payload.question,
                "sql": result["sql"],
                "rows": [],
                "row_count": 0,
                "summary": result["summary"],
                "error": exec_result["error"]
            }
        
        return {
            "question": payload.question,
            "sql": result["sql"],
            "rows": exec_result["rows"],
            "row_count": exec_result["row_count"],
            "columns": exec_result["columns"],
            "summary": result["summary"],
            "error": None
        }
        
    except Exception as e:
        logger.error(f"T2SQL error: {str(e)}")
        raise HttpError(500, f"Internal error: {str(e)}")


@router.post("/t2sql/seed")
def seed_vanna(request):
    """
    Seed Vanna with DDL and training examples.
    Run this once after deployment or when schema changes.
    """
    try:
        vanna_client = VannaClient(
            chroma_dir=CHROMA_DIR,
            groq_api_key=GROQ_API_KEY,
            model=GROQ_MODEL
        )
        
        from crm_agent.ingestion.vanna_seed import VannaSeeder
        seeder = VannaSeeder(vanna_client)
        result = seeder.seed()
        
        return {
            "message": "Vanna seeded successfully",
            "ddl_items": result["ddl_items"],
            "sql_examples": result["sql_examples"]
        }
        
    except Exception as e:
        logger.error(f"Vanna seeding error: {str(e)}")
        raise HttpError(500, f"Seeding error: {str(e)}")

