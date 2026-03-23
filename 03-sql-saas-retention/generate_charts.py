"""
Generate result charts for the SaaS Retention Analysis project.
Produces PNG images for README display.
"""

import sqlite3
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import os

matplotlib.rcParams['font.size'] = 11
matplotlib.rcParams['figure.facecolor'] = 'white'

DB_FILE = 'saas_analysis.db'
IMG_DIR = 'screenshots'
os.makedirs(IMG_DIR, exist_ok=True)

# Rebuild DB if not exists
if not os.path.exists(DB_FILE):
    print("Database not found. Run 'python run_all.py' first.")
    exit(1)

conn = sqlite3.connect(DB_FILE)
cur = conn.cursor()

# ============================================================
# Chart 1: MRR Trend (Bar + Line)
# ============================================================
cur.execute("""
    WITH monthly_events AS (
        SELECT
            strftime('%Y-%m', event_date) AS month,
            SUM(CASE WHEN event_type = 'new' THEN mrr ELSE 0 END) AS new_mrr,
            SUM(CASE WHEN event_type = 'upgrade' THEN mrr ELSE 0 END) AS upgrade_mrr
        FROM subscriptions
        GROUP BY strftime('%Y-%m', event_date)
    )
    SELECT month, new_mrr, upgrade_mrr,
           SUM(new_mrr + upgrade_mrr) OVER (ORDER BY month) AS cumulative_mrr
    FROM monthly_events ORDER BY month
""")
rows = cur.fetchall()
months = [r[0][5:] for r in rows]  # "01", "02", ...
new_mrr = [r[1] for r in rows]
upgrade_mrr = [r[2] for r in rows]
cumulative = [r[3] for r in rows]

fig, ax1 = plt.subplots(figsize=(10, 5))
x = np.arange(len(months))
w = 0.35
ax1.bar(x - w/2, new_mrr, w, label='New MRR', color='#2196F3')
ax1.bar(x + w/2, upgrade_mrr, w, label='Upgrade MRR', color='#4CAF50')
ax1.set_xlabel('Month (2025)')
ax1.set_ylabel('Monthly MRR ($)')
ax1.set_xticks(x)
ax1.set_xticklabels(months)
ax1.legend(loc='upper left')

ax2 = ax1.twinx()
ax2.plot(x, cumulative, color='#FF5722', marker='o', linewidth=2, label='Cumulative MRR')
ax2.set_ylabel('Cumulative MRR ($)')
ax2.legend(loc='center right')

plt.title('Monthly Recurring Revenue (MRR) Trend', fontsize=14, fontweight='bold', pad=15)
plt.tight_layout()
plt.savefig(os.path.join(IMG_DIR, 'mrr_trend.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  Generated: mrr_trend.png")

# ============================================================
# Chart 2: Churn Rate by Plan (Horizontal Bar)
# ============================================================
cur.execute("""
    WITH customer_status AS (
        SELECT c.plan,
               MAX(CASE WHEN s.event_type = 'cancel' THEN 1 ELSE 0 END) AS is_churned
        FROM customers c
        JOIN subscriptions s ON c.customer_id = s.customer_id
        GROUP BY c.customer_id, c.plan
    )
    SELECT plan, COUNT(*) AS total, SUM(is_churned) AS churned,
           ROUND(100.0 * SUM(is_churned) / COUNT(*), 1) AS churn_rate
    FROM customer_status GROUP BY plan ORDER BY churn_rate DESC
""")
rows = cur.fetchall()
plans = [r[0] for r in rows]
totals = [r[1] for r in rows]
churned = [r[2] for r in rows]
rates = [r[3] for r in rows]

fig, ax = plt.subplots(figsize=(8, 4))
colors = ['#f44336', '#FF9800', '#4CAF50']
bars = ax.barh(plans, rates, color=colors, height=0.5)
for bar, rate, ch, tot in zip(bars, rates, churned, totals):
    ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2,
            f'{rate}%  ({ch}/{tot})', va='center', fontsize=11)
ax.set_xlabel('Churn Rate (%)')
ax.set_xlim(0, max(rates) * 1.4)
plt.title('Churn Rate by Subscription Plan', fontsize=14, fontweight='bold', pad=15)
plt.tight_layout()
plt.savefig(os.path.join(IMG_DIR, 'churn_by_plan.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  Generated: churn_by_plan.png")

# ============================================================
# Chart 3: Time-to-Churn Distribution (Pie)
# ============================================================
cur.execute("""
    SELECT
        CASE
            WHEN julianday(s.event_date) - julianday(c.signup_date) <= 30  THEN '0-30 days'
            WHEN julianday(s.event_date) - julianday(c.signup_date) <= 90  THEN '31-90 days'
            WHEN julianday(s.event_date) - julianday(c.signup_date) <= 180 THEN '91-180 days'
            ELSE '180+ days'
        END AS bucket,
        COUNT(*) AS cnt
    FROM customers c
    JOIN subscriptions s ON c.customer_id = s.customer_id
    WHERE s.event_type = 'cancel'
    GROUP BY bucket
    ORDER BY MIN(julianday(s.event_date) - julianday(c.signup_date))
""")
rows = cur.fetchall()
labels = [r[0] for r in rows]
sizes = [r[1] for r in rows]
colors_pie = ['#ffcdd2', '#f44336', '#FF9800', '#FFC107']
explode = [0, 0.08, 0, 0]

fig, ax = plt.subplots(figsize=(7, 5))
wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%',
                                   colors=colors_pie, explode=explode,
                                   startangle=90, textprops={'fontsize': 11})
for t in autotexts:
    t.set_fontweight('bold')
plt.title('Time-to-Churn Distribution', fontsize=14, fontweight='bold', pad=15)
plt.tight_layout()
plt.savefig(os.path.join(IMG_DIR, 'time_to_churn.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  Generated: time_to_churn.png")

# ============================================================
# Chart 4: Cohort Retention Heatmap
# ============================================================
cur.execute("""
    WITH cohort_base AS (
        SELECT customer_id, strftime('%Y-%m', signup_date) AS cohort_month FROM customers
    ),
    customer_activity AS (
        SELECT DISTINCT customer_id, strftime('%Y-%m', log_date) AS active_month FROM usage_logs
    ),
    cohort_data AS (
        SELECT cb.cohort_month,
            (CAST(strftime('%Y', ca.active_month || '-01') AS INT)*12 + CAST(strftime('%m', ca.active_month || '-01') AS INT))
          - (CAST(strftime('%Y', cb.cohort_month || '-01') AS INT)*12 + CAST(strftime('%m', cb.cohort_month || '-01') AS INT))
                AS month_number,
            COUNT(DISTINCT cb.customer_id) AS active_users
        FROM cohort_base cb
        JOIN customer_activity ca ON cb.customer_id = ca.customer_id
        GROUP BY cb.cohort_month, month_number
    ),
    cohort_sizes AS (
        SELECT cohort_month, COUNT(*) AS size FROM cohort_base GROUP BY cohort_month
    )
    SELECT cd.cohort_month, cd.month_number,
           ROUND(100.0 * cd.active_users / cs.size, 1) AS retention_pct
    FROM cohort_data cd
    JOIN cohort_sizes cs ON cd.cohort_month = cs.cohort_month
    WHERE cd.month_number BETWEEN 0 AND 8
    ORDER BY cd.cohort_month, cd.month_number
""")
rows = cur.fetchall()

# Build matrix
cohorts = sorted(set(r[0] for r in rows))
max_month = 8
matrix = np.full((len(cohorts), max_month + 1), np.nan)
for cohort_m, month_n, pct in rows:
    i = cohorts.index(cohort_m)
    if month_n <= max_month:
        matrix[i][int(month_n)] = pct

fig, ax = plt.subplots(figsize=(11, 6))
im = ax.imshow(matrix, cmap='RdYlGn', aspect='auto', vmin=70, vmax=100)

ax.set_xticks(range(max_month + 1))
ax.set_xticklabels([f'M{i}' for i in range(max_month + 1)])
ax.set_yticks(range(len(cohorts)))
ax.set_yticklabels(cohorts)
ax.set_xlabel('Months Since Signup')
ax.set_ylabel('Signup Cohort')

# Add text annotations
for i in range(len(cohorts)):
    for j in range(max_month + 1):
        val = matrix[i][j]
        if not np.isnan(val):
            color = 'white' if val < 85 else 'black'
            ax.text(j, i, f'{val:.0f}%', ha='center', va='center', fontsize=9, color=color)

plt.colorbar(im, label='Retention %', shrink=0.8)
plt.title('Cohort Retention Heatmap', fontsize=14, fontweight='bold', pad=15)
plt.tight_layout()
plt.savefig(os.path.join(IMG_DIR, 'cohort_retention.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  Generated: cohort_retention.png")

# ============================================================
# Chart 5: First-Week Engagement vs Churn
# ============================================================
cur.execute("""
    WITH first_week AS (
        SELECT c.customer_id,
            COALESCE(SUM(u.logins), 0) AS week1_logins,
            CASE WHEN COALESCE(SUM(u.logins), 0) = 0 THEN 'No activity'
                 WHEN COALESCE(SUM(u.logins), 0) <= 3 THEN 'Low activity'
                 ELSE 'Engaged'
            END AS engagement_level
        FROM customers c
        LEFT JOIN usage_logs u ON c.customer_id = u.customer_id
            AND u.log_date BETWEEN c.signup_date AND date(c.signup_date, '+7 days')
        GROUP BY c.customer_id
    ),
    churn_status AS (
        SELECT customer_id, MAX(CASE WHEN event_type='cancel' THEN 1 ELSE 0 END) AS is_churned
        FROM subscriptions GROUP BY customer_id
    )
    SELECT fw.engagement_level, COUNT(*) AS total,
           SUM(cs.is_churned) AS churned,
           ROUND(100.0 * SUM(cs.is_churned) / COUNT(*), 1) AS churn_rate
    FROM first_week fw
    JOIN churn_status cs ON fw.customer_id = cs.customer_id
    GROUP BY fw.engagement_level
    ORDER BY churn_rate DESC
""")
rows = cur.fetchall()
labels = [r[0] for r in rows]
rates = [r[3] for r in rows]
totals = [r[1] for r in rows]

fig, ax = plt.subplots(figsize=(8, 4))
colors = ['#f44336', '#FF9800', '#4CAF50']
bars = ax.bar(labels, rates, color=colors, width=0.5)
for bar, rate, tot in zip(bars, rates, totals):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2,
            f'{rate}%\n(n={tot})', ha='center', va='bottom', fontsize=11)
ax.set_ylabel('Churn Rate (%)')
ax.set_ylim(0, max(rates) * 1.4)
plt.title('First-Week Engagement vs Churn Rate', fontsize=14, fontweight='bold', pad=15)
plt.tight_layout()
plt.savefig(os.path.join(IMG_DIR, 'engagement_vs_churn.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  Generated: engagement_vs_churn.png")

conn.close()
print(f"\nAll charts saved to {IMG_DIR}/")
