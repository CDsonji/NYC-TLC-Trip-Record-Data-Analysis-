# PROJECT_CARD.md

- **1. Track Selection & Data Subset:** 
  - Track: Track A (NYC TLC - Structured / Time-Series)
  - Dataset Subset: Official NYC Yellow Taxi Trip Records for the full calendar year 2025 (January 1 – December 31, 2025), partitioned into 12 monthly Parquet files stored locally in `data/raw/` and queried via DuckDB (~48.7M raw records audited). Spatial files: `taxi_zone_lookup.csv` and `taxi_zones.shp` (EPSG:2263).

- **2. Working Project Title:** 
  Hourly Taxi Demand Forecasting in NYC (2025)

- **3. Problem Statement & Real-World Decision Context:** 
  Assisting fleet managers and operators in dynamically pre-positioning taxicabs across official NYC TLC zones to minimize idle cruising time, reduce passenger wait times, and optimize fleet resource allocation.

- **4. Unit of Analysis & Unit of Prediction:** 
  - Unit of Analysis: `(Taxi Zone ID, Hour Time-Window)` where $z \in \{1, 2, \dots, 263\}$ and $t$ represents discrete 1-hour time indices.
  - Unit of Prediction: Total number of trip originations ($y_{z,t} \in \mathbb{N}_0$) in a given taxi zone and hour window.

- **5. Target Population & Scope:** 
  Pristine baseline population of **$44,015,208$ valid trips** after filtering out $4,707,394$ anomalous records ($\sim 9.66\%$ noise rate), including unmapped locations, invalid durations, extreme telemetry/speed errors ($v > 80$ mph), negative fares, and zero-distance runs, while retaining valid long-distance airport/interstate flows.

- **6. Main Analytical / Prediction Question:** 
  How accurately can we forecast hourly passenger trip originations per taxi zone $(z,t)$ using cyclical temporal encodings, spatial features, and gradient-boosted decision trees, and how do non-linear models compare against historical rolling-mean baselines?

- **7. Target Variables & Outputs:** 
  - Primary Target Variable: Hourly trip count (`trip_count`) per zone and hour.

- **8. Baseline Model:** 
  - Historical rolling mean baseline (same hour, same zone, same day-of-week).

- **9. Proposed Evaluation Metrics:** 
  - Root Mean Squared Error (RMSE) and Mean Absolute Error (MAE) evaluated across all spatial zones.

- **10. Initial Train, Validation, and Test Split Design:** 
  - Strict temporal split: Training on January 1 – September 30, 2025 ($\approx 75\%$); Validation/Test on October 1 – December 31, 2025 ($\approx 25\%$).

- **11. Key Data Leakage Risks:** 
  - Preventing look-ahead bias and accidental target leakage by prohibiting random train/test splitting and ensuring lag features strictly respect chronological order.

- **12. Unsupervised / Pattern Discovery Component:** 
  - Spatial density mapping and logarithmic scaling across NYC boroughs to uncover core commercial hubs vs. outer-borough/airport travel clusters.

- **13. Track-Specific Advanced Extension:** 
  - Incorporating external weather/environmental variables and evaluating spatio-temporal model residual shifts across core commercial districts versus outer-borough control zones.

- **14. Ethics, Privacy, and Bias Risks:** 
  - Dataset contains no PII, with spatial locations aggregated at the 263 official TLC zone polygon level; mitigating potential geographical or socioeconomic service availability biases across outer boroughs.