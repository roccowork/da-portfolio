-- ============================================================
-- 01: Schema Definition & Data Import
-- SaaS Subscription & Retention Analysis
-- ============================================================

-- Create tables for CloudMetrics SaaS data

DROP TABLE IF EXISTS usage_logs;
DROP TABLE IF EXISTS subscriptions;
DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
    customer_id     INT PRIMARY KEY,
    company_name    VARCHAR(50),
    signup_date     DATE NOT NULL,
    plan            VARCHAR(20) NOT NULL,
    company_size    VARCHAR(20),
    industry        VARCHAR(50)
);

CREATE TABLE subscriptions (
    subscription_id INT PRIMARY KEY,
    customer_id     INT REFERENCES customers(customer_id),
    event_type      VARCHAR(20) NOT NULL,  -- new, cancel, upgrade, downgrade
    event_date      DATE NOT NULL,
    plan            VARCHAR(20) NOT NULL,
    mrr             DECIMAL(10,2)          -- Monthly Recurring Revenue at event time
);

CREATE TABLE usage_logs (
    log_id          INT PRIMARY KEY,
    customer_id     INT REFERENCES customers(customer_id),
    log_date        DATE NOT NULL,
    logins          INT,
    features_used   INT,
    session_minutes INT
);

-- Import data (PostgreSQL syntax - adjust for your database)
-- COPY customers FROM '/path/to/data/customers.csv' CSV HEADER;
-- COPY subscriptions FROM '/path/to/data/subscriptions.csv' CSV HEADER;
-- COPY usage_logs FROM '/path/to/data/usage_logs.csv' CSV HEADER;

-- Quick data validation
SELECT 'customers' AS table_name, COUNT(*) AS row_count FROM customers
UNION ALL
SELECT 'subscriptions', COUNT(*) FROM subscriptions
UNION ALL
SELECT 'usage_logs', COUNT(*) FROM usage_logs;
