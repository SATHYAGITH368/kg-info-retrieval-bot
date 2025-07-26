import csv
import json
import subprocess
from pathlib import Path
from datetime import date

# Define paths to your CSV folders
insitu_folder = Path("/Users/sathya/Downloads/knowledge_graph_agent/kg_pipeline/Catalog/Insitu(AWS)")
radar_folder = Path("/Users/sathya/Downloads/knowledge_graph_agent/kg_pipeline/Catalog/RADAR")
satellite_folder = Path("/Users/sathya/Downloads/knowledge_graph_agent/kg_pipeline/Catalog/Satellite")

# Output bulk file
bulk_file = "mordecai_geonames_bulk.json"
bulk_lines = []

# Get today's date in ISO format
today = date.today().isoformat()

# Statistics
total_rows = 0
used_rows = 0

# You can extend this to radar_folder and satellite_folder as needed
csv_folders = [insitu_folder, radar_folder, satellite_folder]

for folder in csv_folders:
    for csv_path in folder.glob("*.csv"):
        print(f" Processing: {csv_path.name}")
        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                total_rows += 1
                try:
                    lat = float(row.get("latres") or row.get("latitude") or row["lat"])
                    lon = float(row.get("longres") or row.get("longitude") or row["lon"])
                except (KeyError, ValueError, TypeError):
                    print(f"⚠️ Skipping row (bad lat/lon): {row}")
                    continue

                name = row.get("name", "").strip()
                state = row.get("state", "").strip()

                if not name or not state:
                    print(f"⚠️ Skipping row (missing name/state): {row}")
                    continue

                used_rows += 1

                # Prepare bulk index and data lines
                bulk_lines.append(json.dumps({"index": {"_index": "geonames"}}))
                bulk_lines.append(json.dumps({
                    "name": name,
                    "asciiname": name,
                    "alternativenames": [],
                    "latitude": lat,
                    "longitude": lon,
                    "feature_class": "P",
                    "feature_code": "PPL",
                    "geonameid": f"IN-{name}".replace(" ", "_").replace(",", ""),
                    "country_code": "IN",
                    "country_code3": "IND",
                    "admin1_code": state,
                    "admin1_name": state,
                    "admin2_code": "",
                    "admin2_name": "",
                    "city_id": "",
                    "city_name": "",
                    "population": 0,
                    "elevation": 0,
                    "dem": 0,
                    "timezone": "Asia/Kolkata",
                    "modification_date": today,
                    "coordinates": f"{lat},{lon}"
                }))


with open(bulk_file, "w", encoding="utf-8") as f:
    f.write("\n".join(bulk_lines) + "\n")

# Print summary
print(f"\nCreated bulk file: {bulk_file}")
print(f" Total rows scanned: {total_rows}")
print(f"Valid rows used:    {used_rows}")
print(f" Documents ready:    {len(bulk_lines) // 2}")

# Upload to Elasticsearch using curl
print("\n Uploading to Elasticsearch...")
try:
    result = subprocess.run([
        "curl", "-s", "-H", "Content-Type: application/x-ndjson",
        "-XPOST", "http://localhost:9200/_bulk",
        "--data-binary", f"@{bulk_file}"
    ], capture_output=True, text=True)

    if result.returncode == 0:
        print(" Upload complete.")
        print(result.stdout[:1000])  # Print only first 1000 chars to keep log clean
    else:
        print(" Upload failed.")
        print(result.stderr)

except FileNotFoundError:
    print("Curl not found. Make sure curl is installed and available in your terminal.")
