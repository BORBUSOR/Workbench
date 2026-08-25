import sqlite3
import os
import sys
import glob

# --- BULLETPROOF PATH LOGIC ---
# sys.path[0] always points to the exact folder containing the script that was executed (main.py)
ROOT_DIR = sys.path[0] 
DB_DIR = os.path.join(ROOT_DIR, 'databases')
# ------------------------------

def get_db_path(guild_name, user_name):
    """Generates a safe path and filename for a specific user."""
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR)
        
    safe_guild = "".join([c for c in guild_name if c.isalnum() or c in (' ', '_', '-')]).strip().replace(' ', '_')
    safe_user = "".join([c for c in user_name if c.isalnum() or c in (' ', '_', '-')]).strip().replace(' ', '_')
    
    filename = f"{safe_guild}_{safe_user}.db"
    return os.path.join(DB_DIR, filename)

def get_shared_db_path(guild_name):
    """Generates a path for a server-wide shared database."""
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR)
        
    safe_guild = "".join([c for c in guild_name if c.isalnum() or c in (' ', '_', '-')]).strip().replace(' ', '_')
    return os.path.join(DB_DIR, f"{safe_guild}_Shared.db")

def add_funds(guild_name, user_name, fund_name, amount):
    """Adds money to a specific user's dedicated database file."""
    db_path = get_db_path(guild_name, user_name)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create the table if it doesn't exist in this user's file
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS balances (
            fund_name TEXT PRIMARY KEY,
            balance REAL
        )
    ''')
    
    # Insert or update the fund balance
    cursor.execute('''
        INSERT INTO balances (fund_name, balance)
        VALUES (?, ?)
        ON CONFLICT(fund_name) 
        DO UPDATE SET balance = balance + excluded.balance
    ''', (fund_name, amount))
    
    conn.commit()
    conn.close()

def get_balance(guild_name, user_name, fund_name):
    """Fetches the current balance of a specific fund."""
    db_path = get_db_path(guild_name, user_name)
    if not os.path.exists(db_path):
        return 0.0

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT balance FROM balances WHERE fund_name = ?", (fund_name,))
    result = cursor.fetchone()
    conn.close()
    
    # Return the balance if it exists, otherwise return 0
    return result[0] if result else 0.0

def deduct_funds(guild_name, user_name, fund_name, amount):
    """Subtracts money from a specific fund."""
    db_path = get_db_path(guild_name, user_name)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE balances 
        SET balance = balance - ? 
        WHERE fund_name = ?
    ''', (amount, fund_name))
    
    conn.commit()
    conn.close()

def get_all_balances(guild_name, user_name):
    """Fetches all funds and their balances for a specific user."""
    db_path = get_db_path(guild_name, user_name)
    
    # If they haven't run !paycheck yet, they won't have a file
    if not os.path.exists(db_path):
        return {}

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Grab every single row in the balances table
    cursor.execute("SELECT fund_name, balance FROM balances")
    results = cursor.fetchall()
    conn.close()
    
    # Package it up nicely into a Python dictionary
    return {row[0]: row[1] for row in results}

def set_goal(guild_name, goal_name, target_amount):
    """Creates a new shared goal or updates the target of an existing one."""
    db_path = get_shared_db_path(guild_name)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS goals (
            goal_name TEXT PRIMARY KEY,
            target REAL,
            current REAL
        )
    ''')
    
    # Insert the goal with 0 current balance, OR update the target if it already exists
    cursor.execute('''
        INSERT INTO goals (goal_name, target, current)
        VALUES (?, ?, 0.0)
        ON CONFLICT(goal_name) 
        DO UPDATE SET target = excluded.target
    ''', (goal_name, target_amount))
    
    conn.commit()
    conn.close()

def add_to_goal(guild_name, goal_name, amount):
    """Adds money to a shared goal."""
    db_path = get_shared_db_path(guild_name)
    if not os.path.exists(db_path): return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("UPDATE goals SET current = current + ? WHERE goal_name = ?", (amount, goal_name))
    success = cursor.rowcount > 0 # Returns True if it successfully found and updated the goal
    
    conn.commit()
    conn.close()
    return success

def get_all_goals(guild_name):
    """Fetches all shared goals for the visualizer."""
    db_path = get_shared_db_path(guild_name)
    if not os.path.exists(db_path): return []
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if the table exists yet
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='goals'")
    if not cursor.fetchone():
        conn.close()
        return []
        
    cursor.execute("SELECT goal_name, target, current FROM goals")
    results = cursor.fetchall()
    conn.close()
    return results

def set_debt(guild_name, user_name, card_name, amount, apr=24.99):
    """Logs or updates the total balance and APR of a specific credit card."""
    db_path = get_db_path(guild_name, user_name)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create the debts table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS debts (
            card_name TEXT PRIMARY KEY,
            balance REAL,
            apr REAL DEFAULT 24.99
        )
    ''')
    
    # Safe migration: add APR column if an older database file is missing it
    try:
        cursor.execute("ALTER TABLE debts ADD COLUMN apr REAL DEFAULT 24.99")
    except sqlite3.OperationalError:
        pass # Column already exists
    
    # Insert the new debt or overwrite it if it already exists
    cursor.execute('''
        INSERT INTO debts (card_name, balance, apr)
        VALUES (?, ?, ?)
        ON CONFLICT(card_name) 
        DO UPDATE SET balance = excluded.balance, apr = excluded.apr
    ''', (card_name, amount, apr))
    
    conn.commit()
    conn.close()

def pay_debt(guild_name, user_name, card_name, amount):
    """Subtracts a payment amount from a specific credit card."""
    db_path = get_db_path(guild_name, user_name)
    if not os.path.exists(db_path): return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("UPDATE debts SET balance = balance - ? WHERE card_name = ?", (amount, card_name))
    success = cursor.rowcount > 0  # Returns True if the card was found
    
    conn.commit()
    conn.close()
    return success

def get_all_debts(guild_name, user_name):
    """Fetches all credit cards, their balances, and their custom APRs."""
    db_path = get_db_path(guild_name, user_name)
    if not os.path.exists(db_path): return []
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if the debts table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='debts'")
    if not cursor.fetchone():
        conn.close()
        return []
        
    # Check if the 'apr' column exists in this user's table
    cursor.execute("PRAGMA table_info(debts)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'apr' not in columns:
        cursor.execute("SELECT card_name, balance FROM debts WHERE balance > 0")
        results = cursor.fetchall()
        conn.close()
        return [(row[0], row[1], 24.99) for row in results]
        
    # Only grab cards that still have a balance greater than 0, including their APR
    cursor.execute("SELECT card_name, balance, apr FROM debts WHERE balance > 0")
    results = cursor.fetchall()
    conn.close()
    return results

def add_subscription(guild_name, sub_name, cost, payer, date):
    """Adds a new subscription to the shared household database."""
    db_path = get_shared_db_path(guild_name)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            sub_name TEXT PRIMARY KEY,
            cost REAL,
            payer TEXT,
            date TEXT
        )
    ''')
    
    cursor.execute('''
        INSERT INTO subscriptions (sub_name, cost, payer, date)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(sub_name) 
        DO UPDATE SET cost = excluded.cost, payer = excluded.payer, date = excluded.date
    ''', (sub_name, cost, payer, date))
    
    conn.commit()
    conn.close()

def cancel_subscription(guild_name, sub_name):
    """Removes a subscription from the shared database."""
    db_path = get_shared_db_path(guild_name)
    if not os.path.exists(db_path): return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM subscriptions WHERE sub_name = ?", (sub_name,))
    success = cursor.rowcount > 0
    
    conn.commit()
    conn.close()
    return success

def get_all_subscriptions(guild_name):
    """Fetches all shared subscriptions."""
    db_path = get_shared_db_path(guild_name)
    if not os.path.exists(db_path): return []
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='subscriptions'")
    if not cursor.fetchone():
        conn.close()
        return []
        
    cursor.execute("SELECT sub_name, cost, payer, date FROM subscriptions")
    results = cursor.fetchall()
    conn.close()
    return results

def get_household_summary(guild_name):
    """Calculates total household wealth and debt by scanning all user databases."""
    if not os.path.exists(DB_DIR):
        return 0.0, 0.0
        
    safe_guild = "".join([c for c in guild_name if c.isalnum() or c in (' ', '_', '-')]).strip().replace(' ', '_')
    
    # Find all databases for this server, EXCLUDING the Shared one
    db_pattern = os.path.join(DB_DIR, f"{safe_guild}_*.db")
    all_dbs = glob.glob(db_pattern)
    
    total_wealth = 0.0
    total_debt = 0.0
    
    for db_file in all_dbs:
        if "Shared.db" in db_file:
            continue
            
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Sum up wealth
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='balances'")
        if cursor.fetchone():
            cursor.execute("SELECT SUM(balance) FROM balances")
            result = cursor.fetchone()
            if result and result[0]: total_wealth += result[0]
            
        # Sum up debts
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='debts'")
        if cursor.fetchone():
            cursor.execute("SELECT SUM(balance) FROM debts")
            result = cursor.fetchone()
            if result and result[0]: total_debt += result[0]
            
        conn.close()
        
    return total_wealth, total_debt

# ==========================================
# MULTI-BANK PLAID DATABASE FUNCTIONS
# ==========================================

def add_plaid_token(guild_name, user_name, access_token):
    """Appends a new Plaid access token to a user's personal database."""
    db_path = get_db_path(guild_name, user_name)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # We no longer limit this to 1 row
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS plaid_auth (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            access_token TEXT
        )
    ''')
    
    # Check if this exact token is already saved so we don't duplicate
    cursor.execute("SELECT * FROM plaid_auth WHERE access_token = ?", (access_token,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO plaid_auth (access_token) VALUES (?)", (access_token,))
        
    conn.commit()
    conn.close()

def get_plaid_tokens(guild_name, user_name):
    """Retrieves ALL of a specific user's Plaid access tokens as a list."""
    db_path = get_db_path(guild_name, user_name)
    if not os.path.exists(db_path): return []
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='plaid_auth'")
    if not cursor.fetchone():
        conn.close()
        return []
        
    cursor.execute("SELECT access_token FROM plaid_auth")
    results = cursor.fetchall()
    conn.close()
    
    return [row[0] for row in results]

def get_all_plaid_tokens(guild_name):
    """Fetches every saved Plaid token across the entire household."""
    if not os.path.exists(DB_DIR): return []
    
    safe_guild = "".join([c for c in guild_name if c.isalnum() or c in (' ', '_', '-')]).strip().replace(' ', '_')
    import glob
    db_pattern = os.path.join(DB_DIR, f"{safe_guild}_*.db")
    all_dbs = glob.glob(db_pattern)
    
    tokens = []
    for db_file in all_dbs:
        if "Shared.db" in db_file: continue
        
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='plaid_auth'")
        if cursor.fetchone():
            cursor.execute("SELECT access_token FROM plaid_auth")
            results = cursor.fetchall()
            for row in results:
                if row[0]: tokens.append(row[0])
                
        conn.close()
        
    return tokens

def set_category_budget(guild_name, user_name, category, limit_amount):
    """Sets a monthly spending limit for a specific category."""
    db_path = get_db_path(guild_name, user_name)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS category_budgets (
            category TEXT PRIMARY KEY,
            limit_amount REAL
        )
    ''')
    
    cursor.execute('''
        INSERT INTO category_budgets (category, limit_amount)
        VALUES (?, ?)
        ON CONFLICT(category) 
        DO UPDATE SET limit_amount = excluded.limit_amount
    ''', (category.upper(), limit_amount))
    
    conn.commit()
    conn.close()

def get_category_budgets(guild_name, user_name):
    """Retrieves all category budget limits for a user."""
    db_path = get_db_path(guild_name, user_name)
    if not os.path.exists(db_path): return {}
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='category_budgets'")
    if not cursor.fetchone():
        conn.close()
        return {}
        
    cursor.execute("SELECT category, limit_amount FROM category_budgets")
    results = cursor.fetchall()
    conn.close()
    return {row[0]: row[1] for row in results}

