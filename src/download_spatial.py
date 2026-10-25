import os
import urllib.request

# Create spatial data directory if it doesn't exist
os.makedirs("data/spatial", exist_ok=True)

# 1. Official NYC TLC Taxi Zone Lookup Table (CSV)
lookup_url = "https://d37ci6vzurychx.cloudfront.net/misc/taxi+_zone_lookup.csv"
lookup_path = "data/spatial/taxi_zone_lookup.csv"

print("Downloading Taxi Zone Lookup Table (CSV)...")
try:
    urllib.request.urlretrieve(lookup_url, lookup_path)
    print(f"-> Successfully saved to {lookup_path}")
except Exception as e:
    print(f"Error downloading lookup table: {e}")

# 2. Taxi Zones GeoParquet (Spatial Geometries)
# Note: This is the cloud-native GeoParquet translation of the NYC TLC shapefile, 
# optimized for direct querying with DuckDB and spatial libraries like geopandas.
parquet_url = "https://data.source.coop/cholmes/nyc-taxi-zones/taxi_zones.parquet"
parquet_path = "data/spatial/taxi_zones.parquet"

print("Downloading Taxi Zones GeoParquet...")
try:
    urllib.request.urlretrieve(parquet_url, parquet_path)
    print(f"-> Successfully saved to {parquet_path}")
except Exception as e:
    print(f"Error downloading zones parquet: {e}")

print("Spatial data download complete!")