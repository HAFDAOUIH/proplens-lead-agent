from typing import Dict, Any, Optional, Tuple
from django.db import connection
import logging
import re

logger = logging.getLogger(__name__)


class SQLExecutor:
    """Safe SQL executor with validation - only SELECT queries allowed."""
    
    # Dangerous SQL keywords to block
    DANGEROUS_KEYWORDS = [
        'DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE',
        'TRUNCATE', 'EXEC', 'EXECUTE', 'GRANT', 'REVOKE'
    ]
    
    def validate_sql(self, sql: str) -> Tuple[bool, Optional[str]]:
        """
        Validate SQL query - only SELECT statements allowed.
        
        Returns:
            (is_valid, error_message)
        """
        sql_upper = sql.upper().strip()
        
        # Must start with SELECT
        if not sql_upper.startswith('SELECT'):
            return False, "Only SELECT queries are allowed"
        
        # Check for dangerous keywords
        for keyword in self.DANGEROUS_KEYWORDS:
            if keyword in sql_upper:
                return False, f"Dangerous keyword '{keyword}' is not allowed"
        
        # Check for multiple statements (semicolon injection)
        if sql_upper.count(';') > 1 or (sql_upper.count(';') == 1 and not sql_upper.rstrip().endswith(';')):
            return False, "Multiple statements are not allowed"
        
        return True, None
    
    def execute(self, sql: str) -> Dict[str, Any]:
        """
        Execute validated SQL query safely.
        
        Returns:
            {
                "rows": List[Dict],
                "row_count": int,
                "columns": List[str],
                "error": Optional[str]
            }
        """
        # Validate SQL
        is_valid, error = self.validate_sql(sql)
        if not is_valid:
            logger.warning(f"SQL validation failed: {error}")
            return {
                "rows": [],
                "row_count": 0,
                "columns": [],
                "error": error
            }
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql)
                
                # Get column names
                columns = [col[0] for col in cursor.description] if cursor.description else []
                
                # Fetch all rows
                rows_data = cursor.fetchall()
                
                # Convert to list of dicts
                rows = [dict(zip(columns, row)) for row in rows_data]
                
                logger.info(f"SQL executed successfully: {len(rows)} rows returned")
                
                return {
                    "rows": rows,
                    "row_count": len(rows),
                    "columns": columns,
                    "error": None
                }
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"SQL execution error: {error_msg}")
            return {
                "rows": [],
                "row_count": 0,
                "columns": [],
                "error": error_msg
            }

