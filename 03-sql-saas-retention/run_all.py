"""
One-click runner: loads CSV into SQLite and executes all SQL queries.
Usage: python run_all.py
"""

import sqlite3
import csv
import os

DB_FILE = 'saas_analysis.db'
DATA_DIR = 'data'

# Remove old database if exists
if os.path.exists(DB_FILE):
    os.remove(DB_FILE)

conn = sqlite3.connect(DB_FILE)
cur = conn.cursor()

# ---- 1. Create tables ----
cur.executescript("""
    CREATE TABLE customers (
        customer_id     INTEGER PRIMARY KEY,
        company_name    TEXT,
        signup_date     TEXT NOT NULL,
        plan            TEXT NOT NULL,
        company_size    TEXT,
        industry        TEXT
    );
    CREATE TABLE subscriptions (
        subscription_id INTEGER PRIMARY KEY,
        customer_id     INTEGER REFERENCES customers(customer_id),
        event_type      TEXT NOT NULL,
        event_date      TEXT NOT NULL,
        plan            TEXT NOT NULL,
        mrr             REAL
    );
    CREATE TABLE usage_logs (
        log_id          INTEGER PRIMARY KEY,
        customer_id     INTEGER REFERENCES customers(customer_id),
        log_date        TEXT NOT NULL,
        logins          INTEGER,
        features_used   INTEGER,
        session_minutes INTEGER
    );
""")

# ---- 2. Load CSV data ----
def load_csv(table, filename):
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, 'r') as f:
        reader = csv.reader(f)
        headers = next(reader)
        placeholders = ','.join(['?'] * len(headers))
        for row in reader:
            cur.execute(f"INSERT INTO {table} VALUES ({placeholders})", row)

load_csv('customers', 'customers.csv')
load_csv('subscriptions', 'subscriptions.csv')
load_csv('usage_logs', 'usage_logs.csv')
conn.commit()

# Verify
for t in ['customers', 'subscriptions', 'usage_logs']:
    cur.execute(f"SELECT COUNT(*) FROM {t}")
    print(f"  {t}: {cur.fetchone()[0]} rows")

# ---- 3. Run analysis queries (SQLite-compatible) ----

queries = {
    # --- 02 Revenue Analysis ---
    "2.1 Monthly MRR Trend": """
        WITH monthly_events AS (
            SELECT
                strftime('%Y-%m', event_date) AS month,
                SUM(CASE WHEN event_type = 'new' THEN mrr ELSE 0 END)     AS new_mrr,
                SUM(CASE WHEN event_type = 'upgrade' THEN mrr ELSE 0 END) AS upgrade_mrr,
                SUM(CASE WHEN event_type = 'cancel' THEN -mrr ELSE 0 END) AS churned_mrr
            FROM subscriptions
            GROUP BY strftime('%Y-%m', event_date)
        )
        SELECT
            month,
            new_mrr,
            upgrade_mrr,
            churned_mrr,
            new_mrr + upgrade_mrr + churned_mrr AS net_mrr_change,
            SUM(new_mrr + upgrade_mrr + churned_mrr) OVER (ORDER BY month) AS cumulative_mrr
        FROM monthly_events
        ORDER BY month
    """,

    "2.2 MRR by Plan": """
        SELECT
            plan,
            COUNT(DISTINCT customer_id) AS active_customers,
            SUM(mrr) AS total_mrr,
            ROUND(AVG(mrr), 2) AS avg_mrr
        FROM subscriptions
        WHERE event_type IN ('new', 'upgrade')
        GROUP BY plan
        ORDER BY total_mrr DESC
    """,

    # --- 03 Churn Analysis ---
    "3.1 Churn Rate by Plan": """
        WITH customer_status AS (
            SELECT
                c.customer_id,
                c.plan,
                MAX(CASE WHEN s.event_type = 'cancel' THEN 1 ELSE 0 END) AS is_churned
            FROM customers c
            JOIN subscriptions s ON c.customer_id = s.customer_id
            GROUP BY c.customer_id, c.plan
        )
        SELECT
            plan,
            COUNT(*) AS total_customers,
            SUM(is_churned) AS churned,
            ROUND(100.0 * SUM(is_churned) / COUNT(*), 1) AS churn_rate_pct
        FROM customer_status
        GROUP BY plan
        ORDER BY churn_rate_pct DESC
    """,

    "3.2 Time-to-Churn Distribution": """
        SELECT
            CASE
                WHEN julianday(s.event_date) - julianday(c.signup_date) <= 30  THEN '0-30 days'
                WHEN julianday(s.event_date) - julianday(c.signup_date) <= 90  THEN '31-90 days'
                WHEN julianday(s.event_date) - julianday(c.signup_date) <= 180 THEN '91-180 days'
                ELSE '180+ days'
            END AS churn_bucket,
            COUNT(*) AS customers,
            ROUND(AVG(julianday(s.event_date) - julianday(c.signup_date)), 0) AS avg_days
        FROM customers c
        JOIN subscriptions s ON c.customer_id = s.customer_id
        WHERE s.event_type = 'cancel'
        GROUP BY churn_bucket
        ORDER BY MIN(julianday(s.event_date) - julianday(c.signup_date))
    """,

    "3.3 Churn by Company Size": """
        SELECT
            c.company_size,
            COUNT(DISTINCT c.customer_id) AS total_customers,
            COUNT(DISTINCT CASE WHEN s.event_type = 'cancel' THEN s.customer_id END) AS churned,
            ROUND(100.0 * COUNT(DISTINCT CASE WHEN s.event_type = 'cancel' THEN s.customer_id END)
                / COUNT(DISTINCT c.customer_id), 1) AS churn_rate_pct
        FROM customers c
        JOIN subscriptions s ON c.customer_id = s.customer_id
        GROUP BY c.company_size
        ORDER BY churn_rate_pct DESC
    """,

    # --- 04 Cohort Retention ---
    "4.1 Cohort Retention Matrix": """
        WITH cohort_base AS (
            SELECT customer_id, strftime('%Y-%m', signup_date) AS cohort_month
            FROM customers
        ),
        customer_activity AS (
            SELECT DISTINCT customer_id, strftime('%Y-%m', log_date) AS active_month
            FROM usage_logs
        ),
        cohort_data AS (
            SELECT
                cb.cohort_month,
                (CAST(strftime('%Y', ca.active_month || '-01') AS INT) * 12 + CAST(strftime('%m', ca.active_month || '-01') AS INT))
              - (CAST(strftime('%Y', cb.cohort_month || '-01') AS INT) * 12 + CAST(strftime('%m', cb.cohort_month || '-01') AS INT))
                    AS month_number,
                COUNT(DISTINCT cb.customer_id) AS active_users
            FROM cohort_base cb
            JOIN customer_activity ca ON cb.customer_id = ca.customer_id
            GROUP BY cb.cohort_month, month_number
        ),
        cohort_sizes AS (
            SELECT cohort_month, COUNT(*) AS size FROM cohort_base GROUP BY cohort_month
        )
        SELECT
            cd.cohort_month,
            cs.size AS cohort_size,
            MAX(CASE WHEN month_number = 0 THEN ROUND(100.0 * active_users / cs.size, 1) END) AS m0,
            MAX(CASE WHEN month_number = 1 THEN ROUND(100.0 * active_users / cs.size, 1) END) AS m1,
            MAX(CASE WHEN month_number = 2 THEN ROUND(100.0 * active_users / cs.size, 1) END) AS m2,
            MAX(CASE WHEN month_number = 3 THEN ROUND(100.0 * active_users / cs.size, 1) END) AS m3,
            MAX(CASE WHEN month_number = 4 THEN ROUND(100.0 * active_users / cs.size, 1) END) AS m4,
            MAX(CASE WHEN month_number = 5 THEN ROUND(100.0 * active_users / cs.size, 1) END) AS m5
        FROM cohort_data cd
        JOIN cohort_sizes cs ON cd.cohort_month = cs.cohort_month
        WHERE month_number BETWEEN 0 AND 5
        GROUP BY cd.cohort_month, cs.size
        ORDER BY cd.cohort_month
    """,

    # --- 05 Churn Prediction ---
    "5.1 First-Week Engagement vs Churn": """
        WITH first_week AS (
            SELECT
                c.customer_id,
                COALESCE(SUM(u.logins), 0) AS week1_logins,
                CASE WHEN COALESCE(SUM(u.logins), 0) = 0 THEN 'No activity'
                     WHEN COALESCE(SUM(u.logins), 0) <= 3 THEN 'Low activity'
                     ELSE 'Engaged'
                END AS engagement_level
            FROM customers c
            LEFT JOIN usage_logs u
                ON c.customer_id = u.customer_id
                AND u.log_date BETWEEN c.signup_date AND date(c.signup_date, '+7 days')
            GROUP BY c.customer_id
        ),
        churn_status AS (
            SELECT customer_id,
                   MAX(CASE WHEN event_type = 'cancel' THEN 1 ELSE 0 END) AS is_churned
            FROM subscriptions GROUP BY customer_id
        )
        SELECT
            fw.engagement_level,
            COUNT(*) AS customers,
            SUM(cs.is_churned) AS churned,
            ROUND(100.0 * SUM(cs.is_churned) / COUNT(*), 1) AS churn_rate_pct
        FROM first_week fw
        JOIN churn_status cs ON fw.customer_id = cs.customer_id
        GROUP BY fw.engagement_level
        ORDER BY churn_rate_pct DESC
    """,

    # --- 06 Executive Summary ---
    "6.1 Key Business Metrics": """
        SELECT
            (SELECT COUNT(*) FROM customers) AS total_customers,
            (SELECT COUNT(DISTINCT customer_id) FROM customers
             WHERE customer_id NOT IN (
                 SELECT customer_id FROM subscriptions WHERE event_type = 'cancel'
             )) AS active_customers,
            (SELECT COUNT(DISTINCT customer_id) FROM subscriptions
             WHERE event_type = 'cancel') AS churned_customers,
            (SELECT ROUND(100.0 *
                (SELECT COUNT(DISTINCT customer_id) FROM subscriptions WHERE event_type = 'cancel')
                / (SELECT COUNT(*) FROM customers), 1)
            ) AS overall_churn_rate_pct,
            (SELECT COUNT(*) FROM subscriptions WHERE event_type = 'upgrade') AS total_upgrades
    """,
}

print("\n" + "=" * 60)
print("  SaaS Subscription & Retention Analysis")
print("=" * 60)

for title, sql in queries.items():
    print(f"\n{'─' * 50}")
    print(f"  {title}")
    print(f"{'─' * 50}")
    cur.execute(sql)
    columns = [desc[0] for desc in cur.description]

    # Calculate column widths
    rows = cur.fetchall()
    widths = [len(str(c)) for c in columns]
    for row in rows:
        for i, val in enumerate(row):
            widths[i] = max(widths[i], len(str(val if val is not None else '')))

    # Print header
    header = ' | '.join(str(c).ljust(widths[i]) for i, c in enumerate(columns))
    print(f"  {header}")
    print(f"  {'-+-'.join('-' * w for w in widths)}")

    # Print rows
    for row in rows:
        line = ' | '.join(str(v if v is not None else '').ljust(widths[i]) for i, v in enumerate(row))
        print(f"  {line}")

conn.close()
print(f"\n{'=' * 60}")
print(f"  Analysis complete. Database saved to: {DB_FILE}")
print(f"{'=' * 60}")
