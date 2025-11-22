"""Tiny SQL Expert interactive CLI."""

import json
import sqlite3
from runner import answer_question, DB_PATH


def run_sql(sql: str):
    """Execute the validated SQL and return rows as dicts."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(sql).fetchall()
    return [dict(row) for row in rows]


def main():
    question = input("Enter your natural-language question:\n> ").strip()
    if not question:
        print("No question provided. Exiting.")
        return

    print(f"\n[question] {question}")
    sql, attempts = answer_question(question)
    print(f"[sql] {sql}")
    print(f"[attempts] {attempts}")

    results = run_sql(sql)
    print(f"[rows] {json.dumps(results, indent=2)}")


if __name__ == "__main__":
    main()