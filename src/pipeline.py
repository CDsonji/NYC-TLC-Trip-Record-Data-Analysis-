from pathlib import Path
import duckdb
import geopandas as gpd
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler


class NYCTaxiPipeline(BaseEstimator, TransformerMixin):
    """
    Unified, reproducible, and leak-free preprocessing & feature engineering pipeline
    for NYC Yellow Taxi Hourly Zone-Level Demand Forecasting (Track A).
    """

    def __init__(
        self,
        raw_parquet_glob: str = "../data/raw/yellow_tripdata_2025-*.parquet",
        shp_path: str = "../data/spatial/taxi_zones.shp",
        lookup_path: str = "../data/spatial/taxi_zone_lookup.csv",
        processed_dir: str = "../data/processed",
        split_date: str = "2025-10-01 00:00:00",
        force_rebuild: bool = False,
    ):
        self.raw_parquet_glob = raw_parquet_glob
        self.shp_path = shp_path
        self.lookup_path = lookup_path
        self.processed_dir = Path(processed_dir)
        self.split_date = pd.Timestamp(split_date)
        self.force_rebuild = force_rebuild

        self.clean_trips_path = self.processed_dir / "yellow_tripdata_2025_clean.parquet"
        self.panel_path = self.processed_dir / "zone_hour_features_2025.parquet"

        self.num_cols = [
            "demand_lag_1h", "demand_lag_2h", "demand_lag_24h", "demand_lag_168h",
            "rolling_mean_3h", "rolling_mean_24h", "net_inflow_lag_1h",
            "avg_dist_lag_1h", "neighbor_demand_lag_1h",
            "Shape_Leng", "Shape_Area", "centroid_lon", "centroid_lat",
            "hour_sin", "hour_cos", "dow_sin", "dow_cos", "month_sin", "month_cos",
        ]
        self.cat_cols = ["Borough", "service_zone"]
        self.passthrough_cols = ["hour", "dayofweek", "month", "is_weekend"]
        self.preprocessor_ = None

    def _build_spatial_tables(self):
        """Extracts static zone metadata, WGS84 centroids, and touching neighbor edges."""
        gdf = gpd.read_file(self.shp_path)
        gdf = gdf[gdf["LocationID"].isin(range(1, 264))].copy()
        gdf_wgs84 = gdf.to_crs(epsg=4326)
        gdf["centroid_lon"] = gdf_wgs84.geometry.centroid.x
        gdf["centroid_lat"] = gdf_wgs84.geometry.centroid.y

        lookup = pd.read_csv(self.lookup_path)[["LocationID", "Borough", "service_zone"]]
        zone_meta = gdf[["LocationID", "Shape_Leng", "Shape_Area", "centroid_lon", "centroid_lat"]].merge(
            lookup, on="LocationID", how="left"
        )

        edges = []
        for _, row in gdf.iterrows():
            z_id = int(row["LocationID"])
            touching = gdf[gdf.geometry.touches(row.geometry)]["LocationID"].tolist()
            for n_id in touching:
                edges.append((z_id, int(n_id)))
        edges_df = pd.DataFrame(edges, columns=["zone_id", "neighbor_id"])
        return zone_meta, edges_df

    def build_base_datasets(self):
        """
        Stage 1 (Out-of-Core DuckDB):
        1. Filters ~48.7M raw records down to ~44.0M valid 2025 trips.
        2. Aggregates into a zero-filled (263 Zones x 8,760 Hours) panel.
        3. Computes deterministic cyclical encodings & strictly backward-looking lags (k >= 1).
        """
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        if self.panel_path.exists() and self.clean_trips_path.exists() and not self.force_rebuild:
            return

        temp_dir = self.processed_dir / "duckdb_temp"
        temp_dir.mkdir(parents=True, exist_ok=True)

        con = duckdb.connect(database=":memory:")
        # Prevent OOM during large Parquet COPY exports
        con.execute("SET preserve_insertion_order = false;")
        con.execute("SET threads = 4;")
        con.execute(f"SET temp_directory = '{temp_dir.as_posix()}';")

        # Step 1A: Deterministic Row-Level Cleaning (skip if already generated in Phase 1)
        if not self.clean_trips_path.exists() or self.force_rebuild:
            cleaning_query = f"""
            COPY (
                WITH base AS (
                    SELECT 
                        VendorID, tpep_pickup_datetime, tpep_dropoff_datetime,
                        passenger_count, trip_distance, RatecodeID, store_and_fwd_flag,
                        PULocationID, DOLocationID, payment_type, fare_amount, extra,
                        mta_tax, tip_amount, tolls_amount, improvement_surcharge,
                        total_amount, congestion_surcharge, Airport_fee, cbd_congestion_fee,
                        EXTRACT(EPOCH FROM (tpep_dropoff_datetime - tpep_pickup_datetime)) / 60.0 AS duration_min,
                        CASE 
                            WHEN EXTRACT(EPOCH FROM (tpep_dropoff_datetime - tpep_pickup_datetime)) > 0 
                            THEN trip_distance / (EXTRACT(EPOCH FROM (tpep_dropoff_datetime - tpep_pickup_datetime)) / 3600.0)
                            ELSE NULL 
                        END AS speed_mph
                    FROM '{self.raw_parquet_glob}'
                )
                SELECT 
                    VendorID, tpep_pickup_datetime, tpep_dropoff_datetime,
                    passenger_count, trip_distance, RatecodeID, store_and_fwd_flag,
                    PULocationID, DOLocationID, payment_type, fare_amount, extra,
                    mta_tax, tip_amount, tolls_amount, improvement_surcharge,
                    total_amount, congestion_surcharge, Airport_fee, cbd_congestion_fee
                FROM base
                WHERE tpep_pickup_datetime >= '2025-01-01 00:00:00'
                  AND tpep_pickup_datetime <  '2026-01-01 00:00:00'
                  AND duration_min > 0 AND duration_min <= 240 AND duration_min IS NOT NULL
                  AND NOT (duration_min < 1.0 AND speed_mph > 70)
                  AND trip_distance > 0
                  AND ((DOLocationID != 265 AND trip_distance <= 100) OR (DOLocationID = 265 AND trip_distance <= 200))
                  AND fare_amount >= 0
                  AND PULocationID NOT IN (264, 265)
                  AND DOLocationID != 264
                  AND speed_mph IS NOT NULL AND speed_mph <= 80
            ) TO '{self.clean_trips_path.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD, ROW_GROUP_SIZE 100000);
            """
            con.execute(cleaning_query)

        # Step 1B: Zero-Filled Spatio-Temporal Panel + Lags + Cyclical Features
        zone_meta, edges_df = self._build_spatial_tables()
        con.register("zone_meta", zone_meta)
        con.register("zone_edges", edges_df)

        panel_query = f"""
        COPY (
            WITH hours AS (
                SELECT UNNEST(generate_series(
                    TIMESTAMP '2025-01-01 00:00:00',
                    TIMESTAMP '2025-12-31 23:00:00',
                    INTERVAL 1 HOUR
                )) AS pickup_hour
            ),
            grid AS (
                SELECT z.LocationID AS zone_id, h.pickup_hour
                FROM zone_meta z CROSS JOIN hours h
            ),
            pickups AS (
                SELECT PULocationID AS zone_id, date_trunc('hour', tpep_pickup_datetime) AS pickup_hour,
                       COUNT(*) AS trip_count, AVG(trip_distance) AS avg_distance
                FROM '{self.clean_trips_path}'
                GROUP BY 1, 2
            ),
            dropoffs AS (
                SELECT DOLocationID AS zone_id, date_trunc('hour', tpep_dropoff_datetime) AS pickup_hour,
                       COUNT(*) AS dropoff_count
                FROM '{self.clean_trips_path}'
                WHERE DOLocationID BETWEEN 1 AND 263
                GROUP BY 1, 2
            ),
            base_panel AS (
                SELECT g.zone_id, g.pickup_hour,
                       COALESCE(p.trip_count, 0) AS trip_count,
                       COALESCE(d.dropoff_count, 0) AS dropoff_count,
                       COALESCE(p.avg_distance, 0.0) AS avg_distance
                FROM grid g
                LEFT JOIN pickups p  ON g.zone_id = p.zone_id AND g.pickup_hour = p.pickup_hour
                LEFT JOIN dropoffs d ON g.zone_id = d.zone_id AND g.pickup_hour = d.pickup_hour
            ),
            lagged_panel AS (
                SELECT
                    b.*,
                    LAG(trip_count, 1)   OVER (PARTITION BY zone_id ORDER BY pickup_hour) AS demand_lag_1h,
                    LAG(trip_count, 2)   OVER (PARTITION BY zone_id ORDER BY pickup_hour) AS demand_lag_2h,
                    LAG(trip_count, 24)  OVER (PARTITION BY zone_id ORDER BY pickup_hour) AS demand_lag_24h,
                    LAG(trip_count, 168) OVER (PARTITION BY zone_id ORDER BY pickup_hour) AS demand_lag_168h,
                    AVG(trip_count) OVER (PARTITION BY zone_id ORDER BY pickup_hour ROWS BETWEEN 3 PRECEDING AND 1 PRECEDING) AS rolling_mean_3h,
                    AVG(trip_count) OVER (PARTITION BY zone_id ORDER BY pickup_hour ROWS BETWEEN 24 PRECEDING AND 1 PRECEDING) AS rolling_mean_24h,
                    LAG(dropoff_count - trip_count, 1) OVER (PARTITION BY zone_id ORDER BY pickup_hour) AS net_inflow_lag_1h,
                    LAG(avg_distance, 1)               OVER (PARTITION BY zone_id ORDER BY pickup_hour) AS avg_dist_lag_1h
                FROM base_panel b
            ),
            spatial_lags AS (
                SELECT e.zone_id, lp.pickup_hour, AVG(lp.demand_lag_1h) AS neighbor_demand_lag_1h
                FROM zone_edges e
                JOIN lagged_panel lp ON e.neighbor_id = lp.zone_id
                GROUP BY 1, 2
            )
            SELECT
                lp.zone_id, lp.pickup_hour, lp.trip_count,
                lp.demand_lag_1h, lp.demand_lag_2h, lp.demand_lag_24h, lp.demand_lag_168h,
                lp.rolling_mean_3h, lp.rolling_mean_24h, lp.net_inflow_lag_1h, lp.avg_dist_lag_1h,
                COALESCE(sl.neighbor_demand_lag_1h, 0.0) AS neighbor_demand_lag_1h,
                EXTRACT(HOUR FROM lp.pickup_hour) AS hour,
                EXTRACT(DOW FROM lp.pickup_hour) AS dayofweek,
                EXTRACT(MONTH FROM lp.pickup_hour) AS month,
                CASE WHEN EXTRACT(DOW FROM lp.pickup_hour) IN (0, 6) THEN 1 ELSE 0 END AS is_weekend,
                SIN(2 * PI() * EXTRACT(HOUR FROM lp.pickup_hour) / 24.0) AS hour_sin,
                COS(2 * PI() * EXTRACT(HOUR FROM lp.pickup_hour) / 24.0) AS hour_cos,
                SIN(2 * PI() * EXTRACT(DOW FROM lp.pickup_hour) / 7.0) AS dow_sin,
                COS(2 * PI() * EXTRACT(DOW FROM lp.pickup_hour) / 7.0) AS dow_cos,
                SIN(2 * PI() * (EXTRACT(MONTH FROM lp.pickup_hour) - 1) / 12.0) AS month_sin,
                COS(2 * PI() * (EXTRACT(MONTH FROM lp.pickup_hour) - 1) / 12.0) AS month_cos,
                zm.Borough, zm.service_zone, zm.Shape_Leng, zm.Shape_Area, zm.centroid_lon, zm.centroid_lat
            FROM lagged_panel lp
            LEFT JOIN spatial_lags sl ON lp.zone_id = sl.zone_id AND lp.pickup_hour = sl.pickup_hour
            LEFT JOIN zone_meta zm    ON lp.zone_id = zm.LocationID
            ORDER BY lp.zone_id, lp.pickup_hour
        ) TO '{self.panel_path}' (FORMAT PARQUET, COMPRESSION ZSTD);
        """
        con.execute(panel_query)
        con.close()

    def split(self):
        """Loads the compact 2.3M panel, drops the 168h burn-in window, and splits chronologically."""
        df = pd.read_parquet(self.panel_path).dropna(subset=["demand_lag_168h"])
        train_df = df[df["pickup_hour"] < self.split_date].copy()
        test_df = df[df["pickup_hour"] >= self.split_date].copy()
        return train_df, test_df

    def fit(self, X: pd.DataFrame, y=None):
        """Fits scalers and encoders strictly on training data."""
        self.preprocessor_ = ColumnTransformer(
            transformers=[
                ("num", StandardScaler(), self.num_cols),
                ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), self.cat_cols),
                ("pass", "passthrough", self.passthrough_cols),
            ]
        )
        self.preprocessor_.fit(X)
        return self

    def transform(self, X: pd.DataFrame):
        """Applies fitted scalers and encoders without data leakage."""
        return self.preprocessor_.transform(X)