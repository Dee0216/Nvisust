# Tiny SQL Expert - NL2SQL with Small Language Models

## Task Chosen: Option 3 - The "Tiny" SQL Expert (SLM Optimization)

This project implements a Natural Language to SQL (NL2SQL) translator using a Small Language Model (< 4B parameters) with self-correction capabilities.

## Overview

The system converts English questions into SQL queries using **Phi-3 (3.8B parameters)** via Ollama. It includes:
- Schema-aware SQL generation
- Automatic self-correction loop for syntax errors
- Support for complex JOIN operations across multiple tables

## Quick Start

**  Important**: You must run `setup_db.py` first to create the database before using the application!

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up Ollama and pull Phi-3 model
ollama pull phi3

# 3. Create database (MUST RUN THIS FIRST!)
python setup_db.py

# 4. Run the application
python app.py
```

## Project Structure

```
nvisust/
├── setup_db.py          # Database schema creation and seeding
├── nl2sql.py            # SQL generation using Phi-3 model
├── runner.py            # Self-correction loop and validation
├── app.py               # Main CLI application
├── data/
│   └── sql_expert.db    # SQLite database
└── requirements.txt     # Python dependencies
```

## Setup Instructions

### Prerequisites

1. **Install Ollama**: Download from [ollama.com](https://ollama.com/download)
2. **Pull Phi-3 model**:
   ```bash
   ollama pull phi3
   ```
3. **Python 3.8+** installed

### Installation

1. Clone this repository:
   ```bash
   git clone <your-repo-url>
   cd nvisust
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. **IMPORTANT: Set up the database FIRST** (must be done before running the application):
   ```bash
   python setup_db.py
   ```
   
   This creates a SQLite database with 4 related tables:
- `customers` (customer_id, full_name, email, loyalty_tier)
- `products` (product_id, product_name, category, list_price)
- `orders` (order_id, customer_id, order_date, status, total_amount)
- `order_items` (order_item_id, order_id, product_id, quantity, unit_price)

## Usage

**Note**: Make sure you've run `setup_db.py` first to create the database!

Run the interactive CLI:
```bash
python app.py
```

Enter a natural language question when prompted, for example:
- "List all customers with their total purchase amount in a column called total_purchase_amount"
- "Show each product category with the total revenue generated from orders"
- "Which Gold-tier customers placed delivered orders?"

The system will:
1. Generate SQL using Phi-3
2. Validate syntax and check for forbidden keywords
3. Automatically correct errors if validation fails
4. Execute the query and display results

## Why These Libraries/Models?

### Ollama + Phi-3 (3.8B parameters)

**Why Ollama:**
- Easy local deployment (no API keys needed)
- Fast inference on CPU/GPU
- Simple Python API
- Supports multiple small models

**Why Phi-3:**
- **Size**: 3.8B parameters (meets < 4B requirement)
- **Performance**: Strong reasoning for its size, good instruction following
- **Efficiency**: Runs well on consumer hardware
- **Accuracy**: Better SQL generation than TinyLlama, competitive with larger models

**Alternatives Considered:**
- **TinyLlama (1.1B)**: Too small, poor SQL accuracy
- **Qwen-1.5-1.8B**: Good but Phi-3 performed better in testing
- **IBM Granite 4.0**: Not easily available via Ollama

### Python Standard Library
- `sqlite3`: Built-in, no external dependencies for database operations
- `pathlib`: Modern file path handling
- `textwrap`: Clean prompt formatting

## Prompting Strategy

### Approach: **Few-Shot Instruction Prompting**

**Why Few-Shot over Chain of Thought (CoT)?**

1. **Model Size Constraint**: Small models (3.8B) struggle with long CoT reasoning chains. Few-shot examples are more efficient.

2. **SQL Structure**: SQL has clear patterns. Showing 2-3 examples teaches the model:
   - How to structure JOINs
   - How to use aggregation (SUM, COUNT)
   - How to format output

3. **Token Efficiency**: Few-shot uses fewer tokens than CoT, reducing latency and cost.

4. **Direct Learning**: Examples directly show the input-output mapping without requiring the model to "think through" steps.

### Prompt Design Elements:

1. **Explicit Schema**: Full table structure with primary/foreign keys clearly listed
2. **Few-Shot Examples**: 2-3 examples showing different JOIN patterns
3. **Strict Instructions**: "Output ONLY SQL", "Never hallucinate columns"
4. **Error Context**: Correction prompts include full schema + error message + previous SQL

### Example Prompt Structure:
```
System: [Role definition + rules]
Schema: [All tables with columns]
Examples: [2-3 few-shot examples]
User: [Question]
SQL: [Expected format]
```

## Self-Correction Loop

The system implements a 3-step validation loop:

1. **Generate SQL**: Phi-3 produces initial SQL query
2. **Validate**: 
   - Check for forbidden keywords (DROP, DELETE, ALTER)
   - Execute `EXPLAIN` to validate syntax
3. **Correct**: If validation fails, feed error back to model with:
   - Original question
   - Error message
   - Previous (invalid) SQL
   - Full schema context

**Max Retries**: 4 attempts (initial + 3 retries)

## Success Criteria Evidence

###  JOIN Queries Working on Tiny Model

**Example Query:**
```
Question: "List each product category with the total revenue generated from orders."
```

**Generated SQL:**
```sql
SELECT p.category, SUM(oi.quantity * oi.unit_price) AS revenue
FROM products p
JOIN order_items oi ON oi.product_id = p.product_id
GROUP BY p.category;
```

**Execution Result:**
```
[attempt 1] Testing SQL: SELECT p.category, SUM(oi.quantity * oi.unit_price) AS revenue...
[validator] ✓ Success after 1 attempt(s)
[rows] [
  {
    "category": "Electronics",
    "revenue": 488.98
  },
  {
    "category": "Home",
    "revenue": 289.01
  },
  {
    "category": "Sports",
    "revenue": 149.0
  }
]
```

**Analysis**: Successfully joins `products` and `order_items` tables, demonstrating multi-table JOIN capability. The tiny model (Phi-3, 3.8B) correctly generates complex JOIN queries with aggregation.

###  Self-Correction Loop Evidence

**Example Query:**
```
Question: "List all customers with their total purchase amount in a column called total_purchase_amount and show only those who bought products in the 'Electronics' category."
```

**Complete Log Showing Self-Correction:**
```
[question] List all customers with their total purchase amount in a column called total_purchase_amount and show only those who bought products in the 'Electronics' category.

[attempt 1] Testing SQL: SELECT c.customer_id, c.full_name, SUM(oi.unit_price * oi.quantity) AS total_purchase_amount...
[validator] ✗ Execution failed: no such column: o.customerner_id
[retry 1] Requesting correction...

[attempt 2] Testing SQL: SELECT c.customer_id, c.full_name, SUM(oi.unit_price * oi.quantity) AS total_purchase_amount...
[validator] ✓ Success after 2 attempt(s)

[sql] SELECT c.customer_id, c.full_name, SUM(oi.unit_price * oi.quantity) AS total_purchase_amount
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
JOIN order_items oi ON oi.order_id = o.order_id
JOIN products p ON oi.product_id = p.product_id AND p.category = 'Electronics'
GROUP BY c.customer_id, c.full_name;

[attempts] 2
[rows] [
  {
    "customer_id": 1,
    "full_name": "Alice Johnson",
    "total_purchase_amount": 239.98
  },
  {
    "customer_id": 2,
    "full_name": "Brian Patel",
    "total_purchase_amount": 249.0
  }
]
```

**Analysis**: 
- **Attempt 1**: Failed due to typo (`o.customerner_id` instead of `o.customer_id`)
- **Retry 1**: System automatically requested correction from the model
- **Attempt 2**: Model fixed the error and generated correct SQL
- **Result**: Successfully executed with correct results

This demonstrates the self-correction loop working: **Initial failure → Automatic retry → Success**

###  Prompting Strategy Explanation

See "Prompting Strategy" section above. Using **Few-Shot Instruction Prompting** with:
- Explicit schema injection
- 2-3 example patterns
- Strict output formatting rules

## Demo

Demo videos are available in youtube
- https://youtu.be/UZP-NMw__MA - Shows JOIN queries working
- https://youtu.be/ZBYXpnTXZVc - Demonstrates self-correction in action

## Limitations

- Small models may occasionally produce semantically incorrect SQL (syntactically valid but doesn't match question intent)
- Complex nested queries may require multiple retries
- Performance depends on hardware (CPU inference can be slow)

## Future Improvements

- Add semantic validation to check if SQL matches question intent
- Fine-tune Phi-3 on SQL datasets for better accuracy
- Support for more complex SQL operations (subqueries, CTEs)
- Add query result validation

## License

This project was created for the AI/ML & Automation Internship Selection Challenge.

