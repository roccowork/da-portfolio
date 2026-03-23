-- ============================================================
-- 02: Revenue Analysis
-- Question: What is our MRR trend and how does it break down?
-- ============================================================

-- -----------------------------------------------
-- 2.1 Monthly MRR trend with running total
-- Business goal: Track overall revenue health
-- -----------------------------------------------
WITH monthly_events AS (
    SELECT
        DATE_TRUNC('month', event_date) AS month,
        SUM(CASE WHEN event_type = 'new' THEN mrr ELSE 0 END)     AS new_mrr,
        SUM(CASE WHEN event_type = 'upgrade' THEN mrr ELSE 0 END) AS upgrade_mrr,
        SUM(CASE WHEN event_type = 'cancel' THEN -mrr ELSE 0 END) AS churned_mrr
    FROM subscriptions
    GROUP BY DATE_TRUNC('month', event_date)
)
SELECT
    month,
    new_mrr,
    upgrade_mrr,
    churned_mrr,
    new_mrr + upgrade_mrr + churned_mrr AS net_mrr_change,
    SUM(new_mrr + upgrade_mrr + churned_mrr) OVER (ORDER BY month) AS cumulative_mrr
FROM monthly_events
ORDER BY month;


-- -----------------------------------------------
-- 2.2 MRR breakdown by plan
-- Business goal: Which plan drives the most revenue?
-- -----------------------------------------------
SELECT
    s.plan,
    COUNT(DISTINCT s.customer_id) AS active_customers,
    SUM(s.mrr)                    AS total_mrr,
    ROUND(AVG(s.mrr), 2)         AS avg_mrr_per_customer,
    ROUND(100.0 * SUM(s.mrr) / SUM(SUM(s.mrr)) OVER (), 1) AS pct_of_total_mrr
FROM subscriptions s
WHERE s.event_type IN ('new', 'upgrade')
GROUP BY s.plan
ORDER BY total_mrr DESC;


-- -----------------------------------------------
-- 2.3 Revenue by industry segment
-- Business goal: Which verticals are most valuable?
-- -----------------------------------------------
SELECT
    c.industry,
    COUNT(DISTINCT c.customer_id)   AS customers,
    SUM(s.mrr)                       AS total_mrr,
    ROUND(AVG(s.mrr), 2)            AS avg_mrr,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN s.event_type = 'cancel' THEN s.customer_id END)
        / COUNT(DISTINCT c.customer_id), 1) AS churn_pct
FROM customers c
JOIN subscriptions s ON c.customer_id = s.customer_id
GROUP BY c.industry
ORDER BY total_mrr DESC;
