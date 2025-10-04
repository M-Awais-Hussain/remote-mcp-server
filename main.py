# run: fastmcp run main.py --transport http --host 0.0.0.0 --port 8000 
##### OR
# uv run main.py

from fastmcp import FastMCP
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "expenses.db")
CATEGORIES_PATH = os.path.join(os.path.dirname(__file__), "categories.json")

mcp = FastMCP("ExpenseTracker")

def init_db():
    with sqlite3.connect(DB_PATH) as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS expenses(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT DEFAULT '',
                note TEXT DEFAULT '' 
            )
        """)

init_db()

@mcp.tool()
def add_expense(date, amount, category, subcategory="", note=""):
    """Add a new expense entry to the database."""
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute(
            "INSERT INTO expenses(date, amount, category, subcategory, note) VALUES(?,?,?,?,?)",
            (date, amount, category, subcategory, note)
        )
        return {"status": "ok", "id": cur.lastrowid}
    
@mcp.tool()
def list_expenses(start_date: str = None, end_date: str = None):
    """
    List expense entries from the database.

    Args:
        start_date (str, optional): Start date in YYYY-MM-DD format. If not provided, returns all.
        end_date (str, optional): End date in YYYY-MM-DD format. If not provided, returns all.
    """
    with sqlite3.connect(DB_PATH) as c:
        if start_date and end_date:
            cur = c.execute(
                """
                SELECT id, date, amount, category, subcategory, note 
                FROM expenses 
                WHERE date BETWEEN ? AND ?
                ORDER BY id ASC
                """,
                (start_date, end_date)
            )
        else:
            cur = c.execute(
                """
                SELECT id, date, amount, category, subcategory, note 
                FROM expenses
                ORDER BY id ASC
                """
            )
        
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]
    
@mcp.tool()
def add_expenses_bulk(expenses: list):
    """
    Add multiple expense entries to the database at once.

    Args:
        expenses (list): A list of expense dicts, each containing:
            - date (str)
            - amount (float)
            - category (str)
            - subcategory (str, optional)
            - note (str, optional)
    """
    with sqlite3.connect(DB_PATH) as c:
        cur = c.executemany(
            "INSERT INTO expenses(date, amount, category, subcategory, note) VALUES(?,?,?,?,?)",
            [(e["date"], e["amount"], e["category"], e.get("subcategory", ""), e.get("note", "")) for e in expenses]
        )
        return {"status": "ok", "count": len(expenses)}
    
@mcp.tool()
def summarize(start_date: str, end_date: str, category: str = None):
    """
    Summarize expenses by category within an inclusive date range.

    Args:
        start_date (str): Start date in YYYY-MM-DD format.
        end_date (str): End date in YYYY-MM-DD format.
        category (str, optional): If provided, only summarize this category.
    """
    with sqlite3.connect(DB_PATH) as c:
        query = """
            SELECT category, SUM(amount) AS total_amount
            FROM expenses
            WHERE date BETWEEN ? AND ?
        """
        params = [start_date, end_date]

        if category:
            query += " AND category = ?"
            params.append(category)

        query += " GROUP BY category ORDER BY category ASC"

        cur = c.execute(query, params)
        cols = [d[0] for d in cur.description]

        return [dict(zip(cols, r)) for r in cur.fetchall()]

@mcp.resource("expense://categories", mime_type= "application/json")
def categroies():
    # Read fresh each time so you can edit the file without restarting
    with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
        return f.read()

if __name__ == "__main__":
    mcp.run(transport= "http", host= "0.0.0.0", port= 8000)