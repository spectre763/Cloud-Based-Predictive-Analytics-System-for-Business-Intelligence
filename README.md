# Cloud-Based Predictive Analytics System for Business Intelligence

A cloud-powered business intelligence platform designed to analyze, monitor, and forecast key business metrics using real-time cloud data.  
The system integrates **Python, Streamlit, and Firebase Firestore** to deliver interactive dashboards, predictive analytics, and anomaly detection for business decision-making.

---

## Project Overview

This project provides a **cloud-based analytics environment** where business data can be uploaded, processed, and visualized through an interactive dashboard.

The system supports:

• Real-time business KPI monitoring  
• Revenue forecasting with scenario modeling  
• Customer segmentation and churn risk analysis  
• Product performance analytics  
• Statistical anomaly detection  
• Cloud database integration using Firebase Firestore

All analytics modules are connected to a **cloud-hosted Firestore database**, enabling scalable and real-time data access.

---

## Key Features

### Executive Business Dashboard
Provides an overview of key business performance metrics including:

- Revenue
- Profit
- Profit Margin
- Customer Acquisition Cost (CAC)
- Customer Churn Rate
- Net Promoter Score (NPS)

---

### Revenue Forecasting
Machine learning–driven revenue forecasting using historical business data.

Features include:

- Historical revenue trend visualization
- Forecast projections
- Scenario analysis (Base, Optimistic, Pessimistic)
- Confidence interval bands
- Feature importance analysis

---

### Customer Analytics & Segmentation

Customer intelligence module powered by behavioral metrics.

Includes:

- RFM (Recency, Frequency, Monetary) segmentation
- Customer Lifetime Value (LTV) analysis
- Cohort retention heatmap
- Churn probability modeling
- Segment distribution visualization

Customer segments include:

- Champions
- Loyal
- Potential
- At Risk
- Lost

---

### Product Intelligence

Product performance analytics dashboard.

Includes:

- Revenue contribution treemap
- Growth-share matrix (BCG style analysis)
- Category-wise revenue distribution
- Product performance comparison

---

### Anomaly Detection

Automatically detects statistical outliers in business metrics.

Capabilities:

- Revenue anomaly identification
- Churn spikes
- Customer acquisition anomalies
- Alert system for abnormal business patterns

---

### Cloud Data Upload

Users can upload business datasets directly into the cloud database.

Features:

- CSV dataset upload
- Automatic synchronization with Firebase Firestore
- Real-time dashboard updates

---

## Cloud Architecture

The system follows a cloud-enabled analytics architecture:

User Interface (Streamlit Dashboard)  
↓  
Python Analytics Engine  
↓  
Firebase Admin SDK  
↓  
Google Cloud Firestore Database  
↓  
Real-time Data Retrieval & Visualization

This architecture enables scalable and real-time analytics processing.

---

## Technology Stack

| Category | Technologies |
|--------|--------|
| Programming | Python |
| Dashboard Framework | Streamlit |
| Data Processing | Pandas, NumPy |
| Visualization | Plotly |
| Cloud Database | Firebase Firestore |
| Backend Integration | Firebase Admin SDK |
| Machine Learning | Scikit-learn |
| Data Storage | Cloud Firestore |

---

## Project Structure
