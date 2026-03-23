-- ============================================================
-- 04: Cohort Retention Analysis
-- Question: How does retention look across signup cohorts?
-- ============================================================

-- -----------------------------------------------
-- 4.1 Monthly signup cohort retention matrix
-- Business goal: Visualize when customers drop off
-- -----------------------------------------------
WITH cohort_base AS (
    -- Assign each customer to their signup month cohort
    SELECT
        customer_id,
        DATE_TRUNC('month', signup_date) AS cohort_month
    FROM customers
),
customer_activity AS (
    -- Get each customer's active months from usage logs
    SELECT DISTINCT
        customer_id,
        DATE_TRUNC('month', log_date) AS active_month
    FROM usage_logs
),
cohort_activity AS (
    SELECT
        cb.cohort_month,
        ca.active_month,
        -- Calculate months since signup (cohort month number)
        EXTRACT(YEAR FROM ca.active_month)  * 12 + EXTRACT(MONTH FROM ca.active_month)
      - EXTRACT(YEAR FROM cb.cohort_month) * 12 - EXTRACT(MONTH FROM cb.cohort_month)
            AS month_number,
        COUNT(DISTINCT cb.customer_id) AS active_customers
    FROM cohort_base cb
    JOIN customer_activity ca ON cb.customer_id = ca.customer_id
    GROUP BY cb.cohort_month, ca.active_month
),
cohort_sizes AS (
    SELECT
        cohort_month,
        COUNT(DISTINCT customer_id) AS cohort_size
    FROM cohort_base
    GROUP BY cohort_month
)
SELECT
    ca.cohort_month,
    cs.cohort_size,
    ca.month_number,
    ca.active_customers,
    ROUND(100.0 * ca.active_customers / cs.cohort_size, 1) AS retention_pct
FROM cohort_activity ca
JOIN cohort_sizes cs ON ca.cohort_month = cs.cohort_month
WHERE ca.month_number >= 0 AND ca.month_number <= 11
ORDER BY ca.cohort_month, ca.month_number;


-- -----------------------------------------------
-- 4.2 Retention pivot table (first 6 months)
-- Business goal: Quick-glance cohort comparison
-- -----------------------------------------------
WITH cohort_base AS (
    SELECT customer_id, DATE_TRUNC('month', signup_date) AS cohort_month
    FROM customers
),
customer_activity AS (
    SELECT DISTINCT customer_id, DATE_TRUNC('month', log_date) AS active_month
    FROM usage_logs
),
cohort_data AS (
    SELECT
        cb.cohort_month,
        EXTRACT(YEAR FROM ca.active_month)  * 12 + EXTRACT(MONTH FROM ca.active_month)
      - EXTRACT(YEAR FROM cb.cohort_month) * 12 - EXTRACT(MONTH FROM cb.cohort_month)
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
    -- Pivot: retention % for months 0-5
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
ORDER BY cd.cohort_month;


-- -----------------------------------------------
-- 4.3 Average retention curve across all cohorts
-- Business goal: Where is the biggest drop-off?
-- -----------------------------------------------
WITH cohort_base AS (
    SELECT customer_id, DATE_TRUNC('month', signup_date) AS cohort_month
    FROM customers
),
customer_activity AS (
    SELECT DISTINCT customer_id, DATE_TRUNC('month', log_date) AS active_month
    FROM usage_logs
),
cohort_data AS (
    SELECT
        cb.cohort_month,
        EXTRACT(YEAR FROM ca.active_month)  * 12 + EXTRACT(MONTH FROM ca.active_month)
      - EXTRACT(YEAR FROM cb.cohort_month) * 12 - EXTRACT(MONTH FROM cb.cohort_month)
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
    month_number,
    ROUND(AVG(100.0 * active_users / cs.size), 1) AS avg_retention_pct,
    COUNT(*) AS cohorts_with_data
FROM cohort_data cd
JOIN cohort_sizes cs ON cd.cohort_month = cs.cohort_month
WHERE month_number BETWEEN 0 AND 11
GROUP BY month_number
ORDER BY month_number;
