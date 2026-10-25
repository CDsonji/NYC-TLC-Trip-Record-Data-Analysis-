import os
import urllib.request

# Create data/raw directory if it doesn't exist
os.makedirs("data/raw", exist_ok=True)

base_url = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2025-"

print("Starting download of 2025 Yellow Taxi trip records (12 months)...")

for month in range(1, 13):
    month_str = f"{month:02d}"
    file_name = f"yellow_tripdata_2025-{month_str}.parquet"
    file_url = f"{base_url}{month_str}.parquet"
    file_path = os.path.join("data/raw", file_name)
    
    if os.path.exists(file_path):
        print(f"[{month}/12] {file_name} already exists. Skipping download.")
        continue
        
    print(f"[{month}/12] Downloading {file_name}...")
    try:
        urllib.request.urlretrieve(file_url, file_path)
        print(f"Successfully downloaded {file_name}")
    except Exception as e:
        print(f"Error downloading {file_name}: {e}")

print("All downloads complete!")