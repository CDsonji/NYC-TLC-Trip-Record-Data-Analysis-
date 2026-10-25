# PROJECT_CARD.md

- **Track Selection:** Track A (NYC TLC - Structured / Time-Series)
- **Working Project Title:** Hourly Taxi Demand Forecasting and Congestion Pricing Impact Analysis in NYC (2025)
- **Problem Statement & Decision Context:** Predicting hourly trip demand per taxi zone and analyzing fare structures (including the new 2025 CBD congestion fee) to optimize fleet positioning and operational efficiency.
- **Dataset Subset:** NYC Yellow Taxi Trip Records (Full Year 2025)
- **Unit of Analysis:** `(Taxi Zone ID, Hour Time-Window)` for demand forecasting; individual trip level for fare/duration analysis.
- **Unit of Prediction:** Total number of trip originations (count) per zone and hour.
- **Target Variables & Metrics:** 
  - Primary Target: Hourly trip count per zone.
  - Evaluation Metrics: Root Mean Squared Error (RMSE) and Mean Absolute Error (MAE).
- **Initial Split Logic:** Strict temporal split (e.g., training on January–September 2025, validating/testing on October–December 2025) to prevent time-based data leakage[cite: 1].
- **Planned Baseline Models:** 
  - Simple Baseline: Historical rolling mean (same hour, same zone, same day-of-week).
  - Non-Linear Baseline: LightGBM / XGBoost with cyclical time features, spatial lags, and CBD congestion fee indicators.
- **Data Leakage Risks:** Using global temporal aggregates or random train-test splitting that mixes past and future traffic patterns.