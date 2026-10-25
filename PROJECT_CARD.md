# PROJECT_CARD.md

- **1. Track Selection & Data Subset:** 
  - Track: Track A (NYC TLC - Structured / Time-Series)
  - Dataset Subset: NYC Yellow Taxi Trip Records (Full Calendar Year 2025: January 1 – December 31, 2025, stored locally as Parquet files queried via DuckDB)

- **2. Working Project Title:** 
  Hourly Taxi Demand Forecasting and Congestion Pricing Impact Analysis in NYC (2025)

- **3. Problem Statement & Real-World Decision Context:** 
  Assisting fleet managers and operators in pre-positioning vehicles across NYC taxi zones to minimize passenger wait times, optimize driver resource allocation, and analyze the operational and financial impact of the newly introduced 2025 Central Business District (CBD) congestion fee.

- **4. Unit of Analysis & Unit of Prediction:** 
  - Unit of Analysis: `(Taxi Zone ID, Hour Time-Window)`
  - Unit of Prediction: Total number of trip originations (integer count) in a given taxi zone and hour window.

- **5. Target Population & Scope:** 
  All valid Yellow Taxi trip records originating across official NYC TLC taxi zones during the year 2025, excluding corrupted records (e.g., negative/zero trip distances, invalid timestamps, or negative fares identified during the data quality audit).

- **6. Main Analytical / Prediction Question:** 
  How accurately can we forecast hourly taxi demand per zone using cyclical temporal encodings, spatial features, and CBD congestion pricing indicators under a strict temporal split, and how do simple baselines compare against non-linear gradient-boosted ensemble models?

- **7. Target Variables, Metrics & Validation Design:** 
  - Primary Target Variable: Hourly trip count (`trip_count`) per zone and hour.
  - Evaluation Metrics: Root Mean Squared Error (RMSE) and Mean Absolute Error (MAE).
  - Validation / Split Logic: Strict temporal split (e.g., training on January–September 2025, validating/testing on October–December 2025) to prevent future data leakage and realistically simulate production forecasting.
  - Planned Baseline Models: Historical rolling mean (same hour, same zone, same day-of-week) vs. Non-Linear Models (LightGBM / XGBoost).
  - Data Leakage Risks: Avoiding global temporal aggregations and random train-test splitting that mixes past and future traffic patterns.