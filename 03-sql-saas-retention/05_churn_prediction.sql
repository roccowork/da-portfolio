-- ============================================================
-- 05: Churn Early Warning Signals
-- Question: Can we predict who will churn based on behavior?
-- ============================================================

-- -----------------------------------------------
-- 5.1 First-week engagement vs churn
-- Hypothesis: Users inactive in week 1 churn more
-- -----------------------------------------------
WITH first_week AS (
    SELECT
        c.customer_id,
        c.plan,
        COALESCE(SUM(u.logins), 0) AS week1_logins,
        COALESCE(SUM(u.features_used), 0) AS week1_features,
        COUNT(u.log_id) AS week1_active_days,
        CASE WHEN COALESCE(SUM(u.logins), 0) = 0 THEN 'No activity'
             WHEN COALESCE(SUM(u.logins), 0) <= 3 THEN 'Low activity'
             ELSE 'Engaged'
        END AS engagement_level
    FROM customers c
    LEFT JOIN usage_logs u
        ON c.customer_id = u.customer_id
        AND u.log_date BETWEEN c.signup_date AND c.signup_date + INTERVAL '7 days'
    GROUP BY c.customer_id, c.plan
),
churn_status AS (
    SELECT
        customer_id,
        MAX(CASE WHEN event_type = 'cancel' THEN 1 ELSE 0 END) AS is_churned
    FROM subscriptions
    GROUP BY customer_id
)
SELECT
    fw.engagement_level,
    COUNT(*) AS customers,
    SUM(cs.is_churned) AS churned,
    ROUND(100.0 * SUM(cs.is_churned) / COUNT(*), 1) AS churn_rate_pct
FROM first_week fw
JOIN churn_status cs ON fw.customer_id = cs.customer_id
GROUP BY fw.engagement_level
ORDER BY churn_rate_pct DESC;


-- -----------------------------------------------
-- 5.2 Usage drop-off before churn
-- Hypothesis: Churners reduce usage before canceling
-- -----------------------------------------------
WITH churned_customers AS (
    SELECT
        s.customer_id,
        s.event_date AS churn_date
    FROM subscriptions s
    WHERE s.event_type = 'cancel'
),
usage_before_churn AS (
    SELECT
        cc.customer_id,
        CASE
            WHEN u.log_date BETWEEN cc.churn_date - INTERVAL '30 days' AND cc.churn_date
                THEN 'Last 30 days'
            WHEN u.log_date BETWEEN cc.churn_date - INTERVAL '60 days' AND cc.churn_date - INTERVAL '31 days'
                THEN '31-60 days before'
            WHEN u.log_date BETWEEN cc.churn_date - INTERVAL '90 days' AND cc.churn_date - INTERVAL '61 days'
                THEN '61-90 days before'
        END AS period,
        u.logins,
        u.features_used,
        u.session_minutes
    FROM churned_customers cc
    JOIN usage_logs u ON cc.customer_id = u.customer_id
    WHERE u.log_date BETWEEN cc.churn_date - INTERVAL '90 days' AND cc.churn_date
)
SELECT
    period,
    COUNT(DISTINCT customer_id) AS customers,
    ROUND(AVG(logins), 1)          AS avg_logins,
    ROUND(AVG(features_used), 1)   AS avg_features,
    ROUND(AVG(session_minutes), 0) AS avg_session_min
FROM usage_before_churn
WHERE period IS NOT NULL
GROUP BY period
ORDER BY
    CASE period
        WHEN '61-90 days before' THEN 1
        WHEN '31-60 days before' THEN 2
        WHEN 'Last 30 days' THEN 3
    END;


-- -----------------------------------------------
-- 5.3 At-risk customer identification
-- Business goal: Flag customers likely to churn
-- -----------------------------------------------
WITH recent_usage AS (
    -- Usage in the last 30 days for active customers
    SELECT
        c.customer_id,
        c.company_name,
        c.plan,
        COUNT(u.log_id)              AS days_active_last30,
        COALESCE(SUM(u.logins), 0)   AS total_logins_last30,
        COALESCE(AVG(u.features_used), 0) AS avg_features_last30
    FROM customers c
    LEFT JOIN usage_logs u
        ON c.customer_id = u.customer_id
        AND u.log_date >= CURRENT_DATE - INTERVAL '30 days'
    WHERE c.customer_id NOT IN (
        SELECT customer_id FROM subscriptions WHERE event_type = 'cancel'
    )
    GROUP BY c.customer_id, c.company_name, c.plan
),
risk_scored AS (
    SELECT
        *,
        CASE
            WHEN days_active_last30 = 0                THEN 'Critical'
            WHEN days_active_last30 <= 3               THEN 'High'
            WHEN total_logins_last30 <= 5              THEN 'Medium'
            ELSE 'Low'
        END AS risk_level
    FROM recent_usage
)
SELECT
    risk_level,
    COUNT(*)          AS customers,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct_of_active
FROM risk_scored
GROUP BY risk_level
ORDER BY
    CASE risk_level
        WHEN 'Critical' THEN 1
        WHEN 'High'     THEN 2
        WHEN 'Medium'   THEN 3
        WHEN 'Low'      THEN 4
    END;


-- -----------------------------------------------
-- 5.4 Top 20 at-risk customers (for CS team action)
-- Business goal: Actionable intervention list
-- -----------------------------------------------
WITH recent_usage AS (
    SELECT
        c.customer_id,
        c.company_name,
        c.plan,
        c.signup_date,
        COUNT(u.log_id)              AS days_active_last30,
        COALESCE(SUM(u.logins), 0)   AS total_logins_last30
    FROM customers c
    LEFT JOIN usage_logs u
        ON c.customer_id = u.customer_id
        AND u.log_date >= CURRENT_DATE - INTERVAL '30 days'
    WHERE c.customer_id NOT IN (
        SELECT customer_id FROM subscriptions WHERE event_type = 'cancel'
    )
    GROUP BY c.customer_id, c.company_name, c.plan, c.signup_date
)
SELECT
    customer_id,
    company_name,
    plan,
    signup_date,
    days_active_last30,
    total_logins_last30,
    CURRENT_DATE - signup_date AS days_since_signup
FROM recent_usage
WHERE days_active_last30 <= 2
ORDER BY total_logins_last30 ASC, days_active_last30 ASC
LIMIT 20;
