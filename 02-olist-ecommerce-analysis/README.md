# E-Commerce Customer & Delivery Analysis

## Overview
Exploratory data analysis of 100K+ orders from Olist, a Brazilian e-commerce marketplace. This project investigates customer satisfaction drivers and delivery performance to provide actionable business recommendations.

## Dataset
- **Source:** [Kaggle - Brazilian E-Commerce (Olist)](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
- **Records:** 100K+ orders (2016-2018)
- **Tables:** Orders, Order Items, Products, Customers, Sellers, Reviews, Payments, Geolocation

## Analysis Structure

### 1. Data Cleaning & Preparation
- Handle missing values and duplicates
- Parse dates and create time features
- Merge multiple tables into analysis-ready dataset

### 2. Sales & Revenue Analysis
- Monthly order volume and revenue trends
- Top product categories by sales
- Average order value over time

### 3. Delivery Performance
- Average delivery time by state
- On-time vs late delivery rates
- Impact of late delivery on customer reviews

### 4. Customer Satisfaction
- Review score distribution
- Correlation between delivery time and review score
- Factors affecting low ratings

## Key Insights
- [To be filled after running the analysis]

## Tools Used
- Python 3.11
- Pandas, NumPy
- Matplotlib, Seaborn
- Jupyter Notebook

## How to Run
```bash
conda activate da
jupyter notebook analysis.ipynb
```

## Data
Download the dataset from [Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) and place CSV files in the `data/` folder.
