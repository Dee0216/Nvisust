import ollama
import textwrap

PROMPT_TEMPLATE = textwrap.dedent("""
System:
You are an expert SQL translator. Convert English questions into valid SQL for the following SQLite schema. 
CRITICAL RULES:
- Never hallucinate tables or columns. Use JOINs when necessary.
- Follow the question EXACTLY. Do NOT add extra conditions (like loyalty_tier filters, HAVING clauses, or thresholds) unless explicitly mentioned in the question.
- Do not invent placeholder values like 'start_date' or fake column names—use only real columns and literal values deducible from the question.
- Output ONLY the SQL query with no commentary.

Schema:
Table customers(customer_id PK, full_name, email, loyalty_tier)
Table products(product_id PK, product_name, category, list_price)
Table orders(order_id PK, customer_id FK→customers, order_date, status, total_amount)
Table order_items(order_item_id PK, order_id FK→orders, product_id FK→products, quantity, unit_price)

Few-shot examples (do not reuse literal values, just follow the pattern):

User: Which Gold customers placed delivered orders?
SQL: SELECT DISTINCT c.full_name
     FROM customers c
     JOIN orders o ON o.customer_id = c.customer_id
     WHERE c.loyalty_tier = 'Gold' AND o.status = 'delivered';

User: Total revenue per product category?
SQL: SELECT p.category, SUM(oi.quantity * oi.unit_price) AS revenue
     FROM products p
     JOIN order_items oi ON oi.product_id = p.product_id
     GROUP BY p.category;



User: {{question}}
SQL:
""")

def build_prompt(question: str) -> str:
    return PROMPT_TEMPLATE.replace("{{question}}", question.strip())

def generate_sql(question: str) -> str:
    prompt = build_prompt(question)
    response = ollama.chat(
        model="phi3",
        messages=[{"role": "user", "content": prompt}],
    )
    return response["message"]["content"].strip()

# if __name__ == "__main__":
#     sql = generate_sql("List delivered orders for Gold customers")
#     print(sql)