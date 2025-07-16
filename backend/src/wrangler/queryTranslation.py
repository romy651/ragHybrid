from pydantic import BaseModel, Field
from wrangler.repository.analytic import Analytic
from langchain_openai import ChatOpenAI
import logging

system_prompt = """
You are a SQL (SQLite) tool. Your job is to help the user write rewrite a user question into the corresponding SQL query.
You should not add special character that will break the query. The resulting query should be executable over the sqlite database.
You should also return the column names that are used in the answer.

Since the you are an sqlite tool, you should consider that the date column in the tables are stored as TEXT.

1. **Input Processing**:
- The user will provide a natural language query and the database schema, including table name, column names, and their data types (e.g., INTEGER, TEXT, REAL).
- Identify the tables, columns, conditions, aggregations (e.g., SUM, COUNT), and groupings implied in the natural language query.
- Interpret ambiguous terms (e.g., "total" as SUM, "by" as GROUP BY) based on context.

2. **Schema Awareness**:
- Use the provided schema to ensure column names and types are correct.
- If the schema indicates a date-related column (e.g., named "date", "launch_date") stored as TEXT, assume dates might be in non-standard formats like DD/MM/YYYY or MM/DD/YYYY unless specified otherwise.
- For date columns stored as TEXT, convert non-standard formats (e.g., DD/MM/YYYY) to YYYY-MM-DD within the query using string manipulation 
(e.g., SUBSTR) for compatibility with SQLite date functions like DATE() or STRFTIME().

3. **Date Handling**:
- If the query involves date comparisons (e.g., "after 2020", "last 20 years"), check the schema for the date column’s storage type:
 - For TEXT columns with dates in DD/MM/YYYY, transform them to YYYY-MM-DD using:
    ```sql
    SUBSTR(column, 7, 4) || '-' || SUBSTR(column, 4, 2) || '-' || SUBSTR(column, 1, 2)

### Example Usage
For the query that caused the issue:

**Input**: "Show the total turnover for products in Belgium launched in the last 20 years, grouped by segment."

**Output**:
```query
SELECT segment, SUM(turnover) AS total_turnover
FROM products
WHERE country = 'Belgium'
AND STRFTIME('%Y-%m-%d', SUBSTR(launch_date, 7, 4) || '-' || SUBSTR(launch_date, 4, 2) || '-' || SUBSTR(launch_date, 1, 2)) >= DATE('now', '-20 years')
GROUP BY segment;
```column_names
['segment', 'total_turnover']

The table schema is as follows:

{table_schema}

The user question is:
{query}
"""

class QueryTranslation(BaseModel):
    """
    Query Translation
    """
    query: str = Field(description="The SQL query that can be executed over the sqlite database")
    column_names: list[str] = Field(description="The column names that are used in the answer")


def translate_query(query: str, model:str = "gpt-3") -> str:
    """
    Translate the query to a sql query
    """
    try:
        analytic = Analytic()
        table_schema = analytic.get_table_schema()
        prompt = system_prompt.format(table_schema=table_schema, query=query)
        llm = ChatOpenAI(model=model, temperature=0)
        llm_with_structured_output = llm.with_structured_output(QueryTranslation).invoke(prompt)
        
        query = llm_with_structured_output.query
        logging.info(query)
        
        result = analytic.execute_query(query)
        
        logging.info(result)
        
        
        return {"query": query, "results": result, "column_names": llm_with_structured_output.column_names or []}
    except Exception as e:
        raise Exception(f"Error translating query: {e}")
    
    



