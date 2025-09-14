import os
import math
import requests
from PIL import Image

# Google tile server template (satellite view)
TILE_URL = "https://mt0.google.com/vt/lyrs=s&x={x}&y={y}&z={z}"

def latlon_to_tile(lat, lon, zoom):
    """Convert latitude and longitude to Slippy Map tile numbers."""
    lat_rad = math.radians(lat)
    n = 2.0 ** zoom
    x_tile = int((lon + 180.0) / 360.0 * n)
    y_tile = int((1.0 - math.log(math.tan(lat_rad) + 1 / math.cos(lat_rad)) / math.pi) / 2.0 * n)
    return x_tile, y_tile

def download_tile(x, y, z, out_dir="tiles"):
    os.makedirs(out_dir, exist_ok=True)
    url = TILE_URL.format(x=x, y=y, z=z)
    path = f"{out_dir}/{z}_{x}_{y}.png"

    if not os.path.exists(path):
        r = requests.get(url, stream=True)
        if r.status_code == 200:
            with open(path, "wb") as f:
                f.write(r.content)
        else:
            print(f"Tile {x},{y} -> HTTP {r.status_code}")
    return path

def stitch_tiles(x_min, x_max, y_min, y_max, z, out_file="stitched.png"):
    tile_size = 256
    width = (x_max - x_min + 1) * tile_size
    height = (y_max - y_min + 1) * tile_size
    stitched = Image.new("RGB", (width, height))

    for y in range(y_min, y_max + 1):
        for x in range(x_min, x_max + 1):
            path = download_tile(x, y, z)
            if os.path.exists(path):
                tile = Image.open(path)
                stitched.paste(tile, ((x - x_min) * tile_size, (y - y_min) * tile_size))

    stitched.save(out_file)
    print(f"[STATUS] Saved -> {out_file}")

if __name__ == "__main__":
    # Ask user for bounding box
    top_lat = float(input("Enter top latitude: "))
    bottom_lat = float(input("Enter bottom latitude: "))
    left_lon = float(input("Enter left longitude: "))
    right_lon = float(input("Enter right longitude: "))
    zoom = int(input("Enter zoom level (e.g., 13–17): "))

    # Convert to tile indices
    x_min, y_max = latlon_to_tile(bottom_lat, left_lon, zoom)
    x_max, y_min = latlon_to_tile(top_lat, right_lon, zoom)

    # Ensure order
    x_min, x_max = min(x_min, x_max), max(x_min, x_max)
    y_min, y_max = min(y_min, y_max), max(y_min, y_max)

    print(f"[STATUS] Downloading tiles x:{x_min}-{x_max}, y:{y_min}-{y_max}, zoom={zoom}...")
    stitch_tiles(x_min, x_max, y_min, y_max, zoom, out_file="map_output.png")
    print("[STATUS] Done.")
