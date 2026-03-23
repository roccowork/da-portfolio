-- ============================================================
-- 06: Executive Summary Dashboard Queries
-- One-stop queries for leadership reporting
-- ============================================================

-- -----------------------------------------------
-- 6.1 Key business metrics at a glance
-- -----------------------------------------------
WITH metrics AS (
    SELECT
        -- Total customers
        (SELECT COUNT(*) FROM customers) AS total_customers,

        -- Active customers (never canceled)
        (SELECT COUNT(DISTINCT customer_id) FROM customers
         WHERE customer_id NOT IN (
             SELECT customer_id FROM subscriptions WHERE event_type = 'cancel'
         )) AS active_customers,

        -- Churned customers
        (SELECT COUNT(DISTINCT customer_id) FROM subscriptions
         WHERE event_type = 'cancel') AS churned_customers,

        -- Current MRR (latest active subscription per customer)
        (SELECT SUM(mrr) FROM (
            SELECT DISTINCT ON (customer_id) customer_id, mrr
            FROM subscriptions
            WHERE event_type != 'cancel'
            ORDER BY customer_id, event_date DESC
        ) latest
        WHERE customer_id NOT IN (
            SELECT customer_id FROM subscriptions WHERE event_type = 'cancel'
        )) AS current_mrr,

        -- Upgrades
        (SELECT COUNT(*) FROM subscriptions WHERE event_type = 'upgrade') AS total_upgrades
)
SELECT
    total_customers,
    active_customers,
    churned_customers,
    ROUND(100.0 * churned_customers / total_customers, 1) AS overall_churn_rate,
    current_mrr,
    ROUND(current_mrr / active_customers, 2) AS arpu,
    total_upgrades,
    ROUND(100.0 * total_upgrades / active_customers, 1) AS upgrade_rate
FROM metrics;


-- -----------------------------------------------
-- 6.2 Recommendations summary
-- Actionable insights tied to the analysis
-- -----------------------------------------------

/*
FINDINGS & RECOMMENDATIONS
===========================

1. CHURN IS PLAN-DEPENDENT
   - Basic plan churn (~15%) is 3x Enterprise (~5%)
   - Recommendation: Introduce onboarding program for Basic tier
     to drive feature adoption and reduce early churn

2. FIRST WEEK IS CRITICAL
   - Users with zero activity in week 1 have 4x higher churn
   - Recommendation: Implement automated activation emails
     triggered if no login within 3 days of signup

3. MONTH 3 IS THE DROP-OFF CLIFF
   - Cohort analysis shows the steepest retention drop at month 3
   - Recommendation: Schedule proactive Customer Success check-in
     at day 60 to reinforce value before the critical period

4. USAGE DECLINES PREDICT CHURN
   - Churners show 50%+ drop in logins 30 days before canceling
   - Recommendation: Build usage-drop alert dashboard for CS team
     to intervene before customers reach the cancellation decision

5. SMALL COMPANIES CHURN MORE
   - Company size 1-10 has the highest churn rate
   - Recommendation: Consider self-serve resources and community
     support to improve retention for SMB segment
*/
