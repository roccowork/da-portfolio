"""
Generate simulated SaaS dataset for retention analysis.
Run once to create CSV files in data/ folder.
"""

import csv
import random
from datetime import datetime, timedelta

random.seed(42)

PLANS = ['Basic', 'Pro', 'Enterprise']
PLAN_PRICES = {'Basic': 29, 'Pro': 79, 'Enterprise': 199}
PLAN_WEIGHTS = [0.50, 0.35, 0.15]
COMPANY_SIZES = ['1-10', '11-50', '51-200', '201-500', '500+']
SIZE_WEIGHTS = [0.30, 0.30, 0.20, 0.12, 0.08]
INDUSTRIES = ['Technology', 'Healthcare', 'Finance', 'Retail', 'Education', 'Manufacturing']

START_DATE = datetime(2025, 1, 1)
END_DATE = datetime(2025, 12, 31)

# --- Customers ---
customers = []
for i in range(1, 2001):
    signup = START_DATE + timedelta(days=random.randint(0, 334))
    plan = random.choices(PLANS, PLAN_WEIGHTS)[0]
    size = random.choices(COMPANY_SIZES, SIZE_WEIGHTS)[0]
    industry = random.choice(INDUSTRIES)
    customers.append({
        'customer_id': i,
        'company_name': f'Company_{i:04d}',
        'signup_date': signup.strftime('%Y-%m-%d'),
        'plan': plan,
        'company_size': size,
        'industry': industry,
    })

with open('data/customers.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=customers[0].keys())
    w.writeheader()
    w.writerows(customers)

# --- Subscriptions ---
subscriptions = []
sub_id = 1
for c in customers:
    signup = datetime.strptime(c['signup_date'], '%Y-%m-%d')
    plan = c['plan']

    # Initial subscription
    subscriptions.append({
        'subscription_id': sub_id,
        'customer_id': c['customer_id'],
        'event_type': 'new',
        'event_date': c['signup_date'],
        'plan': plan,
        'mrr': PLAN_PRICES[plan],
    })
    sub_id += 1

    days_active = (END_DATE - signup).days

    # Churn probability based on plan
    churn_prob = {'Basic': 0.15, 'Pro': 0.08, 'Enterprise': 0.05}[plan]

    if random.random() < churn_prob and days_active > 30:
        cancel_day = random.randint(30, min(days_active, 300))
        cancel_date = signup + timedelta(days=cancel_day)
        subscriptions.append({
            'subscription_id': sub_id,
            'customer_id': c['customer_id'],
            'event_type': 'cancel',
            'event_date': cancel_date.strftime('%Y-%m-%d'),
            'plan': plan,
            'mrr': 0,
        })
        sub_id += 1
    else:
        # Some upgrades / downgrades
        if random.random() < 0.12 and plan != 'Enterprise':
            upgrade_day = random.randint(30, min(days_active, 250))
            new_plan = 'Pro' if plan == 'Basic' else 'Enterprise'
            subscriptions.append({
                'subscription_id': sub_id,
                'customer_id': c['customer_id'],
                'event_type': 'upgrade',
                'event_date': (signup + timedelta(days=upgrade_day)).strftime('%Y-%m-%d'),
                'plan': new_plan,
                'mrr': PLAN_PRICES[new_plan],
            })
            sub_id += 1

with open('data/subscriptions.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=subscriptions[0].keys())
    w.writeheader()
    w.writerows(subscriptions)

# --- Usage Logs ---
usage_logs = []
log_id = 1
for c in customers:
    signup = datetime.strptime(c['signup_date'], '%Y-%m-%d')
    # Check if customer churned
    cancel_date = None
    for s in subscriptions:
        if s['customer_id'] == c['customer_id'] and s['event_type'] == 'cancel':
            cancel_date = datetime.strptime(s['event_date'], '%Y-%m-%d')
            break

    end = cancel_date if cancel_date else END_DATE
    days_active = (end - signup).days

    # Generate weekly usage (sample ~2 days/week to keep data manageable)
    current = signup
    is_engaged = random.random() > 0.2  # 20% are low-engagement users

    while current <= end:
        if random.random() < (0.6 if is_engaged else 0.15):
            logins = random.randint(1, 8) if is_engaged else random.randint(0, 2)
            features = random.randint(1, 5) if is_engaged else random.randint(0, 1)
            sessions = random.randint(1, logins + 1)
            usage_logs.append({
                'log_id': log_id,
                'customer_id': c['customer_id'],
                'log_date': current.strftime('%Y-%m-%d'),
                'logins': logins,
                'features_used': features,
                'session_minutes': sessions * random.randint(5, 45),
            })
            log_id += 1
        current += timedelta(days=1)

with open('data/usage_logs.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=usage_logs[0].keys())
    w.writeheader()
    w.writerows(usage_logs)

print(f"Generated: {len(customers)} customers, {len(subscriptions)} subscriptions, {len(usage_logs)} usage logs")
