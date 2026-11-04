# AI Usage and Collaboration Disclosure

Throughout Phase 1 of the NYC Yellow Taxi Hourly Demand Forecasting project, generative AI tools—specifically **Gemini 3 models**—were utilized collaboratively as an interactive technical assistant. Below is a detailed record of the AI utilization workflow, methodologies, and contributions across different phases of the project.

## 1. Task Definition and Project Structuring
- **Initial Planning:** Following the initial upload of the project description and requirements, the AI was prompted to assist in defining formal project phases. This established a structured roadmap spanning data auditing, exploratory data analysis (EDA), spatial mapping, and LaTeX technical report generation.
- **Problem Formulation:** Collaborative prompts helped formalize the operational decision problem for fleet dispatchers and structure the spatio-temporal aggregation unit $(z,t) \in \text{Zone} \times \text{Hour}$.

## 2. Code Generation and Data Pipeline Assistance
- **DuckDB Optimization:** To handle high-volume data constraints across the 12 monthly Parquet files (48.7 million raw records) without triggering Out-Of-Memory (OOM) exceptions on standard local hardware, the AI generated memory-efficient SQL and Python scripts utilizing DuckDB's in-memory execution engine, Bernoulli sampling (`USING SAMPLE`), and approximate quantile calculations (`approx_quantile`).
- **Geospatial & Visual Processing:** Developed modular Python scripts leveraging `geopandas`, `matplotlib`, and `seaborn` libraries to parse shapefiles (`taxi_zones.shp`), join spatial lookup tables (`taxi_zone_lookup.csv`), and render probability density distributions with Kernel Density Estimations (KDE).
- **Visualization Customization:** Assisted in designing and tuning custom plots, including transitioning from linear colormaps to logarithmic normalizations (`LogNorm`) and capped quantile scales to accurately capture both core Manhattan density hotspots and subtle outer-borough variations.

## 3. Collaborative Interpretation, Inspection, and Justification
- **Iterative Inspection:** For each analytical module, notebook cell outputs, statistical summaries, and generated figures were shared with the AI for inspection.
- **Joint Justification & Consensus:** Through iterative critique and discussion—combining empirical results with human perspective—rigorous economic and operational rationales were established. This included justifying the retention of out-of-jurisdiction long-distance trips (up to 200 miles), airport flat-rate structural clusters, policy-driven discrete fee structures, and safety/telemetry filtering thresholds (e.g., capping speeds at $80\text{ mph}$ and durations at $240\text{ minutes}$).

## 4. LaTeX Report Generation and Structuring
- **Modular Report Assembly:** The technical report was constructed section-by-section and borough-by-borough. The AI generated clean, professional LaTeX code utilizing `booktabs`, `multirow`, and nested `subfigure` environments.
- **Iterative Refinement:** Ensured precise integration of custom multi-row descriptive statistics tables, top-10 busiest zone rankings, and multi-panel distribution/boxplot figures across all administrative boroughs (Manhattan, Queens, Brooklyn, Bronx, Staten Island, and EWR).

## 5. Technical Debugging
- **SQL Parser Resolution:** Debugged and resolved DuckDB syntax errors encountered when applying sampling clauses directly alongside `LEFT JOIN` operations by refactoring queries into structured Common Table Expressions (CTEs).
- **LaTeX Compilation & Formatting:** Resolved figure placement floats, table column width overflows, and package compatibility issues during document compilation.