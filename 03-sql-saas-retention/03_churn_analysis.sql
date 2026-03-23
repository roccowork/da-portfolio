-- ============================================================
-- 03: Churn Analysis
-- Question: What is our churn rate and who is churning?
-- ============================================================

-- -----------------------------------------------
-- 3.1 Overall and plan-level churn rate
-- Business goal: Quantify the churn problem
-- -----------------------------------------------
WITH customer_status AS (
    SELECT
        c.customer_id,
        c.plan,
        c.company_size,
        MAX(CASE WHEN s.event_type = 'cancel' THEN 1 ELSE 0 END) AS is_churned,
        MIN(CASE WHEN s.event_type = 'cancel' THEN s.event_date END) AS churn_date
    FROM customers c
    JOIN subscriptions s ON c.customer_id = s.customer_id
    GROUP BY c.customer_id, c.plan, c.company_size
)
SELECT
    plan,
    COUNT(*)                        AS total_customers,
    SUM(is_churned)                 AS churned_customers,
    ROUND(100.0 * SUM(is_churned) / COUNT(*), 1) AS churn_rate_pct
FROM customer_status
GROUP BY ROLLUP(plan)
ORDER BY plan NULLS LAST;


-- -----------------------------------------------
-- 3.2 Monthly churn trend
-- Business goal: Is churn getting worse over time?
-- -----------------------------------------------
WITH monthly_base AS (
    SELECT
        DATE_TRUNC('month', event_date) AS month,
        COUNT(DISTINCT customer_id) AS total_active
    FROM subscriptions
    WHERE event_type = 'new'
    GROUP BY DATE_TRUNC('month', event_date)
),
monthly_churn AS (
    SELECT
        DATE_TRUNC('month', event_date) AS month,
        COUNT(DISTINCT customer_id) AS churned
    FROM subscriptions
    WHERE event_type = 'cancel'
    GROUP BY DATE_TRUNC('month', event_date)
)
SELECT
    b.month,
    b.total_active   AS new_signups,
    COALESCE(ch.churned, 0) AS cancellations,
    b.total_active - COALESCE(ch.churned, 0) AS net_growth,
    ROUND(100.0 * COALESCE(ch.churned, 0) / NULLIF(b.total_active, 0), 1) AS churn_rate_pct
FROM monthly_base b
LEFT JOIN monthly_churn ch ON b.month = ch.month
ORDER BY b.month;


-- -----------------------------------------------
-- 3.3 Time-to-churn distribution
-- Business goal: How quickly do customers leave?
-- -----------------------------------------------
WITH churn_timing AS (
    SELECT
        c.customer_id,
        c.plan,
        c.signup_date,
        s.event_date AS churn_date,
        s.event_date - c.signup_date AS days_to_churn,
        CASE
            WHEN s.event_date - c.signup_date <= 30  THEN '0-30 days'
            WHEN s.event_date - c.signup_date <= 90  THEN '31-90 days'
            WHEN s.event_date - c.signup_date <= 180 THEN '91-180 days'
            ELSE '180+ days'
        END AS churn_bucket
    FROM customers c
    JOIN subscriptions s ON c.customer_id = s.customer_id
    WHERE s.event_type = 'cancel'
)
SELECT
    churn_bucket,
    COUNT(*)                          AS customers,
    ROUND(AVG(days_to_churn), 0)      AS avg_days,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct_of_churned
FROM churn_timing
GROUP BY churn_bucket
ORDER BY MIN(days_to_churn);


-- -----------------------------------------------
-- 3.4 Churn by company size
-- Business goal: Are smaller companies more at risk?
-- -----------------------------------------------
SELECT
    c.company_size,
    COUNT(DISTINCT c.customer_id) AS total_customers,
    COUNT(DISTINCT CASE WHEN s.event_type = 'cancel' THEN s.customer_id END) AS churned,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN s.event_type = 'cancel' THEN s.customer_id END)
        / COUNT(DISTINCT c.customer_id), 1) AS churn_rate_pct
FROM customers c
JOIN subscriptions s ON c.customer_id = s.customer_id
GROUP BY c.company_size
ORDER BY churn_rate_pct DESC;
