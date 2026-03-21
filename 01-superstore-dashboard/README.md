# Superstore Sales Dashboard

## Overview
An interactive Power BI dashboard analyzing sales performance of a US retail superstore. The dashboard helps executives quickly identify top-performing regions, categories, and time-based trends.

## Dataset
- **Source:** [Kaggle - Superstore Dataset](https://www.kaggle.com/datasets/vivek468/superstore-dataset-final)
- **Records:** 9,994 orders (5,009 unique)
- **Fields:** Order Date, Ship Date, Segment, Country, City, State, Region, Category, Sub-Category, Sales, Quantity, Discount, Profit

## Dashboard Pages

### Page 1: Sales Overview
- Total Sales ($2.30M), Total Profit ($286.40K), Total Orders (5,009), Profit Margin (12.47%) — KPI cards
- Sales & Profit trend by year (line chart)
- Sales by Region (donut chart — West 31.58%, East 29.55%, Central 21.82%, South 17.05%)
- Sales by Category & Sub-Category (bar chart — Technology > Furniture > Office Supplies)

### Page 2: Profitability Analysis
- Profit by State (bar chart — California & New York lead)
- Discount vs Profit correlation (scatter plot — higher discount = lower profit)
- Top 10 most profitable products (treemap)
- Bottom 10 least profitable products (funnel chart — Cubify CubeX 3D Printer is biggest loss at -$8.88K)

## Key Insights
1. **Revenue Growth:** Sales grew steadily from 2014 ($0.48M) to 2017 ($0.73M), a 52% increase
2. **Regional Leader:** West region accounts for 31.58% of total sales
3. **Discount Trap:** Products with discounts above 40% almost always result in negative profit
4. **Top Category:** Technology leads in sales, followed by Furniture and Office Supplies
5. **Loss Leaders:** 3D printers and high-end conference tables are the biggest money losers

## Screenshots
![Sales Overview](screenshots/overview.png)
![Profitability Analysis](screenshots/profitability.png)

## How to Open
1. Download [Power BI Desktop](https://powerbi.microsoft.com/desktop/) (free)
2. Download the `.pbix` file from this folder
3. Open it in Power BI Desktop
