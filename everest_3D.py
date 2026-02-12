import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 - needed for 3D projection
import requests
import os
import time
import argparse
from dotenv import load_dotenv
from typing import Tuple, Dict

# Load API key from .env file
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError(
        "GOOGLE_MAPS_API_KEY not found in .env file. "
        "Please create a .env file with: GOOGLE_MAPS_API_KEY=your_api_key"
    )


def get_elevation_data(
    center_lat: float,
    center_lon: float,
    grid_size: int = 50,
    area_size_deg: float = 0.15,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Fetch elevation data from Google Elevation API for a grid around a center point.
    
    Args:
        center_lat: Center latitude (degrees)
        center_lon: Center longitude (degrees)
        grid_size: Number of points per side (total points = grid_size^2)
        area_size_deg: Size of area to cover in degrees (e.g., 0.15 = ~16.7 km)
    
    Returns:
        Tuple of (lat_grid, lon_grid, elevation_grid) as numpy arrays
    """
    # Create a grid of lat/lon points
    lat_min = center_lat - area_size_deg / 2
    lat_max = center_lat + area_size_deg / 2
    lon_min = center_lon - area_size_deg / 2
    lon_max = center_lon + area_size_deg / 2

    lat_vals = np.linspace(lat_min, lat_max, grid_size)
    lon_vals = np.linspace(lon_min, lon_max, grid_size)
    lat_grid, lon_grid = np.meshgrid(lat_vals, lon_vals, indexing="ij")

    # Flatten for API request
    total_points = grid_size * grid_size
    locations = [
        f"{lat_grid.flat[i]},{lon_grid.flat[i]}" for i in range(total_points)
    ]

    # Google Elevation API allows up to 512 locations per request
    # However, URL length limits mean we should use smaller batches (100-200)
    # Split into batches if needed
    batch_size = 100  # Reduced to avoid URL length limits
    elevations = []

    print(f"Fetching elevation data for {total_points} points...")

    for i in range(0, total_points, batch_size):
        batch = locations[i : i + batch_size]
        locations_str = "|".join(batch)

        url = "https://maps.googleapis.com/maps/api/elevation/json"
        params = {
            "locations": locations_str,
            "key": GOOGLE_API_KEY,
        }

        response = requests.get(url, params=params)
        
        # Better error handling
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print(f"Error response: {response.text[:500]}")  # Print first 500 chars of error
            raise RuntimeError(
                f"HTTP Error {response.status_code}: {e}\n"
                f"Response: {response.text[:500]}"
            )

        data = response.json()

        if data["status"] != "OK":
            error_msg = data.get("error_message", "No error message provided")
            raise RuntimeError(
                f"Google Elevation API error: {data.get('status', 'Unknown')}\n"
                f"Error message: {error_msg}"
            )

        batch_elevations = [result["elevation"] for result in data["results"]]
        elevations.extend(batch_elevations)

        print(f"  Fetched batch {i // batch_size + 1}/{(total_points - 1) // batch_size + 1}")
        
        # Small delay to avoid rate limiting
        if i + batch_size < total_points:
            time.sleep(0.1)

    # Reshape elevations to match grid
    elevation_grid = np.array(elevations).reshape(grid_size, grid_size)

    return lat_grid, lon_grid, elevation_grid


def lat_lon_to_3d(
    lat_grid: np.ndarray, lon_grid: np.ndarray, elevation_grid: np.ndarray
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Convert lat/lon/elevation to 3D Cartesian coordinates (meters).
    Uses a simple local projection centered on the grid center.
    
    Args:
        lat_grid: Latitude grid (degrees)
        lon_grid: Longitude grid (degrees)
        elevation_grid: Elevation grid (meters)
    
    Returns:
        Tuple of (X, Y, Z) grids in meters
    """
    # Approximate conversion: 1 degree lat ≈ 111,000 m, 1 degree lon ≈ 111,000 * cos(lat) m
    center_lat = np.mean(lat_grid)
    center_lon = np.mean(lon_grid)

    # Convert to meters relative to center
    lat_m = (lat_grid - center_lat) * 111000
    lon_m = (lon_grid - center_lon) * 111000 * np.cos(np.radians(center_lat))

    return lon_m, lat_m, elevation_grid


# Dictionary of all 14 eight-thousander mountains (8000+ meters)
# Format: "name": {"lat": latitude, "lon": longitude, "height": height_in_meters}
EIGHT_THOUSANDERS: Dict[str, Dict[str, float]] = {
    "Everest": {"lat": 27.9881, "lon": 86.9250, "height": 8848},
    "K2": {"lat": 35.8814, "lon": 76.5133, "height": 8611},
    "Kangchenjunga": {"lat": 27.7025, "lon": 88.1475, "height": 8586},
    "Lhotse": {"lat": 27.9617, "lon": 86.9336, "height": 8516},
    "Makalu": {"lat": 27.8897, "lon": 87.0886, "height": 8485},
    "Cho Oyu": {"lat": 28.0944, "lon": 86.6608, "height": 8188},
    "Dhaulagiri": {"lat": 28.6967, "lon": 83.4953, "height": 8167},
    "Manaslu": {"lat": 28.5497, "lon": 84.5594, "height": 8163},
    "Nanga Parbat": {"lat": 35.2375, "lon": 74.5892, "height": 8126},
    "Annapurna": {"lat": 28.5956, "lon": 83.8203, "height": 8091},
    "Gasherbrum I": {"lat": 35.7247, "lon": 76.6958, "height": 8080},
    "Broad Peak": {"lat": 35.8106, "lon": 76.5681, "height": 8051},
    "Gasherbrum II": {"lat": 35.7581, "lon": 76.6531, "height": 8035},
    "Shishapangma": {"lat": 28.3531, "lon": 85.7786, "height": 8027},
}

# Parse command-line arguments
parser = argparse.ArgumentParser(
    description="Visualize 3D wireframe of eight-thousander mountains using Google Elevation API"
)
parser.add_argument(
    "--peak",
    type=str,
    #nargs="?",
    default="Everest",
    help=f"Mountain name to visualize. Options: {', '.join(EIGHT_THOUSANDERS.keys())}",
)
args = parser.parse_args()

# Get mountain name (case-insensitive)
mountain_name = args.peak.title()

# Handle alternative names
name_mapping = {
    "Kanchenjunga": "Kangchenjunga",
    "Kanchenjanga": "Kangchenjunga",
    "Shisha Pangma": "Shishapangma",
    "Shishapangma": "Shishapangma",
    "Gasherbrum 1": "Gasherbrum I",
    "Gasherbrum 2": "Gasherbrum II",
    "Gasherbrum I": "Gasherbrum I",
    "Gasherbrum II": "Gasherbrum II",
}

if mountain_name in name_mapping:
    mountain_name = name_mapping[mountain_name]

# Validate mountain name
if mountain_name not in EIGHT_THOUSANDERS:
    print(f"Error: '{args.mountain}' is not a valid mountain name.")
    print(f"Available mountains: {', '.join(EIGHT_THOUSANDERS.keys())}")
    exit(1)

# Get mountain coordinates
mountain_data = EIGHT_THOUSANDERS[mountain_name]
mountain_lat = mountain_data["lat"]
mountain_lon = mountain_data["lon"]
mountain_height = mountain_data["height"]

print(f"Visualizing: {mountain_name} ({mountain_height} m)")
print(f"Coordinates: {mountain_lat}°N, {mountain_lon}°E")

# Fetch real elevation data
print("Fetching elevation data from Google Elevation API...")
lat_grid, lon_grid, elevation_grid = get_elevation_data(
    center_lat=mountain_lat,
    center_lon=mountain_lon,
    grid_size=50,  # 30x30 = 900 points (reduced to avoid API limits)
    area_size_deg=0.15,  # ~16.7 km x 16.7 km area
)

# Convert to 3D coordinates
X, Y, Z = lat_lon_to_3d(lat_grid, lon_grid, elevation_grid)

print(f"Elevation range: {Z.min():.1f} m to {Z.max():.1f} m")
print(f"Peak elevation: {Z.max():.1f} m")

# Create 3D visualization
fig = plt.figure(figsize=(12, 8))
ax = fig.add_subplot(111, projection="3d")

LIGHT_GREEN = "#90EE90"  # light green color

# Main wireframe surface
ax.plot_wireframe(
    X,
    Y,
    Z,
    rstride=2,
    cstride=2,
    color=LIGHT_GREEN,
    linewidth=0.6,
    alpha=0.9,
)

# Highlight the peak with a thicker line
peak_idx = np.unravel_index(np.argmax(Z), Z.shape)
peak_x = X[peak_idx]
peak_y = Y[peak_idx]
peak_z = Z[peak_idx]

# Peak marker
box_size = 200  # Size reference for connecting line
ax.scatter(
    peak_x,
    peak_y,
    peak_z,
    s=300,  # 3 times bigger (was 100)
    marker="s",  # Square marker
    facecolors="none",  # No fill color
    edgecolors="yellow",  # Only border color
    linewidths=2,
    #label=f"Peak: {Z.max():.0f} m",
    label=f"Peak: {EIGHT_THOUSANDERS[mountain_name]["height"]:.0f} m"
)

# Calculate text position (further up and to the left)
text_offset_x = -800  # Move left (negative = left direction)
text_offset_y = 800   # Move up (positive = up direction)
text_offset_z = 500   # Move higher vertically
text_x = peak_x + text_offset_x
text_y = peak_y + text_offset_y
text_z = peak_z + text_offset_z

# Draw a line connecting the peak point to the text label
# Connect directly from the peak point to the text
line_start_x = peak_x
line_start_y = peak_y
line_start_z = peak_z

ax.plot(
    [line_start_x, text_x],
    [line_start_y, text_y],
    [line_start_z, text_z],
    color="yellow",
    linewidth=1.5,
    linestyle="--",
    alpha=0.7,
)

# Add text annotation showing mountain height near the peak
height_text = f"{mountain_height} m"
ax.text(
    text_x,
    text_y,
    text_z,
    height_text,
    color="yellow",
    fontsize=12,
    fontweight="bold",
    ha="left",  # Align left since we're positioning to the left
    va="bottom",
    bbox=dict(boxstyle="round,pad=0.3", facecolor="black", edgecolor="yellow", alpha=0.7),
)

# Base grid lines to enhance the wireframe feel
base_z = np.full_like(Z, Z.min())
ax.plot_wireframe(
    X,
    Y,
    base_z,
    rstride=5,
    cstride=5,
    color=LIGHT_GREEN,
    linewidth=0.3,
    alpha=0.2,
)

# Styling: dark background to emphasize the wire silhouette
ax.set_facecolor("black")
fig.patch.set_facecolor("black")

for axis in [ax.xaxis, ax.yaxis, ax.zaxis]:
    axis._axinfo["grid"]["color"] = (1, 1, 1, 0.15)

# Set limits with some padding
ax.set_xlim(X.min() - 500, X.max() + 500)
ax.set_ylim(Y.min() - 500, Y.max() + 500)
ax.set_zlim(Z.min() - 200, Z.max() + 500)

# Remove ticks for a clean look
ax.set_xticks([])
ax.set_yticks([])
ax.set_zticks([])

# Labels
ax.set_xlabel("East-West (m)", color="white", labelpad=10)
ax.set_ylabel("North-South (m)", color="white", labelpad=10)
ax.set_zlabel("Elevation (m)", color="white", labelpad=10)

# Adjust view angle for a nice 3D silhouette
ax.view_init(elev=30, azim=-50)

ax.set_title(
    f"3D Wire Silhouette of {mountain_name} ({mountain_height} m)\n(Real elevation data from Google Elevation API)",
    color="white",
    pad=20,
    fontsize=12,
)

ax.legend(loc="upper left", facecolor="black", edgecolor="white", labelcolor="white")

plt.tight_layout()
plt.show()
