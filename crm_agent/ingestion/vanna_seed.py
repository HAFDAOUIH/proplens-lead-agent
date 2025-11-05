from django.apps import apps
from django.db import connection
from typing import List, Tuple, Dict
import logging

from crm_agent.agent.vanna_client import VannaClient

logger = logging.getLogger(__name__)


class VannaSeeder:
    """Seed Vanna with DDL and NL→SQL examples."""
    
    def __init__(self, vanna_client: VannaClient):
        self.vanna = vanna_client
    
    def get_lead_ddl(self) -> str:
        """
        Extract CREATE TABLE DDL for Lead model.
        
        Returns:
            CREATE TABLE statement as string
        """
        model = apps.get_model('coreapp', 'Lead')
        table_name = model._meta.db_table
        
        # Build DDL from model fields
        fields = []
        for field in model._meta.get_fields():
            if field.name == 'id':
                fields.append('id INTEGER PRIMARY KEY AUTOINCREMENT')
            elif hasattr(field, 'db_type'):
                field_type = field.db_type(connection)
                nullable = 'NULL' if field.null else 'NOT NULL'
                
                if field.name == 'id':
                    continue  # Already handled
                elif field_type == 'integer':
                    fields.append(f"{field.name} INTEGER {nullable}")
                elif field_type == 'varchar' or field_type.startswith('varchar'):
                    max_length = getattr(field, 'max_length', 255)
                    fields.append(f"{field.name} VARCHAR({max_length}) {nullable}")
                elif field_type == 'text':
                    fields.append(f"{field.name} TEXT {nullable}")
                elif field_type == 'decimal':
                    max_digits = getattr(field, 'max_digits', 15)
                    decimal_places = getattr(field, 'decimal_places', 2)
                    fields.append(f"{field.name} DECIMAL({max_digits},{decimal_places}) {nullable}")
                elif field_type == 'date':
                    fields.append(f"{field.name} DATE {nullable}")
                elif field_type == 'datetime':
                    fields.append(f"{field.name} DATETIME {nullable}")
                else:
                    fields.append(f"{field.name} {field_type.upper()} {nullable}")
        
        ddl = f"CREATE TABLE {table_name} (\n    " + ",\n    ".join(fields) + "\n);"
        return ddl
    
    def get_training_examples(self) -> List[Tuple[str, str]]:
        """
        Get NL→SQL training examples.
        
        Returns:
            List of (question, sql) tuples
        """
        model = apps.get_model('coreapp', 'Lead')
        table_name = model._meta.db_table
        
        examples = [
            (
                "How many leads total?",
                f"SELECT COUNT(*) as total_leads FROM {table_name}"
            ),
            (
                "Show all Connected leads",
                f"SELECT * FROM {table_name} WHERE status = 'Connected'"
            ),
            (
                "Count leads by project",
                f"SELECT project_enquired, COUNT(*) as count FROM {table_name} GROUP BY project_enquired"
            ),
            (
                "Leads with budget over 1 million",
                f"SELECT * FROM {table_name} WHERE budget_min > 1000000"
            ),
            (
                "Leads contacted in March 2024",
                f"SELECT * FROM {table_name} WHERE last_conversation_date >= '2024-03-01' AND last_conversation_date < '2024-04-01'"
            ),
            (
                "How many leads by status?",
                f"SELECT status, COUNT(*) as count FROM {table_name} GROUP BY status"
            ),
            (
                "Show top 5 leads by budget_max",
                f"SELECT * FROM {table_name} WHERE budget_max IS NOT NULL ORDER BY budget_max DESC LIMIT 5"
            ),
            (
                "Leads enquired about Beachgate project",
                f"SELECT * FROM {table_name} WHERE project_enquired LIKE '%Beachgate%'"
            ),
            (
                "Count leads with email addresses",
                f"SELECT COUNT(*) as count FROM {table_name} WHERE email IS NOT NULL AND email != ''"
            ),
            (
                "Show leads created in the last 30 days",
                f"SELECT * FROM {table_name} WHERE created_at >= datetime('now', '-30 days')"
            )
        ]
        
        return examples
    
    def seed(self) -> Dict[str, int]:
        """
        Seed Vanna with DDL and examples.
        
        Returns:
            {"ddl_items": 1, "sql_examples": N}
        """
        ddl_count = 0
        sql_count = 0
        
        try:
            # Seed DDL
            ddl = self.get_lead_ddl()
            self.vanna.add_training_item("ddl", ddl)
            ddl_count = 1
            logger.info("Seeded DDL for Lead model")
            
            # Seed SQL examples
            examples = self.get_training_examples()
            for question, sql in examples:
                self.vanna.add_training_item("sql", sql, question=question)
                sql_count += 1
            
            logger.info(f"Seeded {sql_count} SQL examples")
            
            return {
                "ddl_items": ddl_count,
                "sql_examples": sql_count
            }
            
        except Exception as e:
            logger.error(f"Error seeding Vanna: {str(e)}")
            raise

