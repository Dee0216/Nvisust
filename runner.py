import sqlite3
from pathlib import Path
import ollama
import textwrap
import re
from nl2sql import generate_sql

DB_PATH = Path("data/sql_expert.db")
FORBIDDEN = {"drop", "delete", "alter"}


def is_safe(sql: str) -> bool:
    """Check if SQL contains forbidden keywords."""
    return not any(word in sql.lower() for word in FORBIDDEN)

def try_execute(sql: str) -> tuple[bool, str]:
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("EXPLAIN " + sql)  
        return True, ""
    except sqlite3.Error as exc:
        return False, str(exc)

def _extract_sql(text: str) -> str:
    """Extract SQL from model response, removing code fences."""
    # Remove markdown code fences
    text = re.sub(r'```sql\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'```\s*', '', text)
    
    # Find SQL statement
    sql_match = re.search(r'(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP)\s+.*?;', text, re.DOTALL | re.IGNORECASE)
    if sql_match:
        return sql_match.group(0).strip()
    
    return text.strip()


def self_correct(question: str, error_msg: str, previous_sql: str) -> str:
    """Ask model to fix invalid SQL."""
    schema = """
Schema:
Table customers(customer_id PK, full_name, email, loyalty_tier)
Table products(product_id PK, product_name, category, list_price)
Table orders(order_id PK, customer_id FK→customers, order_date, status, total_amount)
Table order_items(order_item_id PK, order_id FK→orders, product_id FK→products, quantity, unit_price)
"""
    prompt = textwrap.dedent(f"""
    System:
    Fix this invalid SQL. Error: {error_msg}
    
    {schema}
    
    Question: {question}
    Invalid SQL: {previous_sql}
    
    Return ONLY the corrected SQL query. No explanations, no code fences.
    """)
    response = ollama.chat(model="phi3", messages=[{"role": "user", "content": prompt}])
    return _extract_sql(response["message"]["content"])

def answer_question(question: str, max_retries: int = 4) -> tuple[str, int]:
    """Generate SQL with self-correction loop."""
    sql = _extract_sql(generate_sql(question))
    attempts = 1
    
    while attempts <= max_retries + 1:
        print(f"[attempt {attempts}] Testing SQL: {sql[:100]}..." if len(sql) > 100 else f"[attempt {attempts}] Testing SQL: {sql}")
        
        if not is_safe(sql):
            error = "Forbidden keyword detected."
            print(f"[validator] {error}")
        else:
            ok, error = try_execute(sql)
            if ok:
                print(f"[validator] ✓ Success after {attempts} attempt(s)")
                return sql, attempts
            print(f"[validator] ✗ Execution failed: {error}")

        if attempts > max_retries:
            raise RuntimeError(f"Could not produce valid SQL after {max_retries} retries.")
        
        print(f"[retry {attempts}] Requesting correction...")
        sql = self_correct(question, error, sql)
        attempts += 1

if __name__ == "__main__":
    question = "Which Gold customers placed delivered orders?"
    sql, attempt_count = answer_question(question)
    print(sql)