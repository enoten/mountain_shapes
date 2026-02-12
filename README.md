# Mountain Profiles - 3D Visualization

Visualize 3D wireframe silhouettes of the world's highest mountains using real elevation data from the Google Elevation API.

## Features

- **14 Eight-thousander mountains** (8000+ meters): Everest, K2, Kangchenjunga, Lhotse, Makalu, Cho Oyu, Dhaulagiri, Manaslu, Nanga Parbat, Annapurna, Gasherbrum I, Broad Peak, Gasherbrum II, Shishapangma
- **Real elevation data** from Google Elevation API
- **Interactive 3D wireframe** with glow effect and cyan/turquoise styling
- **Peak marker** with height label and connecting line
- **Animation** (in `everest_3D_1.py`): Continuous counter-clockwise rotation around the z-axis

## Prerequisites

- Python 3.7+
- [Google Maps API Key](https://developers.google.com/maps/documentation/elevation/get-api-key) with **Elevation API** enabled

## Setup

1. **Clone or download** this project.

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API key** — Create a `.env` file in the project root:
   ```
   GOOGLE_MAPS_API_KEY=your_api_key_here
   ```
   
   > Enable the [Elevation API](https://console.cloud.google.com/apis/library/elevation-backend.googleapis.com) in Google Cloud Console for your project. Billing must be enabled (free tier available).

## Usage

### everest_3D.py (Static 3D visualization)

```bash
# Default: Mount Everest
python everest_3D.py

# Specify a mountain with --peak
python everest_3D.py --peak K2
python everest_3D.py --peak "Gasherbrum I"
python everest_3D.py --peak Shishapangma
```

### everest_3D_1.py (Animated 3D visualization)

Same usage as above, with an animated rotating view:

```bash
python everest_3D_1.py
python everest_3D_1.py --peak Lhotse
```

## Available Mountains

| Mountain       | Height (m) |
|----------------|------------|
| Everest        | 8848       |
| K2             | 8611       |
| Kangchenjunga  | 8586       |
| Lhotse         | 8516       |
| Makalu         | 8485       |
| Cho Oyu        | 8188       |
| Dhaulagiri     | 8167       |
| Manaslu        | 8163       |
| Nanga Parbat   | 8126       |
| Annapurna      | 8091       |
| Gasherbrum I   | 8080       |
| Broad Peak     | 8051       |
| Gasherbrum II  | 8035       |
| Shishapangma   | 8027       |

Alternative names supported: `Kanchenjanga` → Kangchenjunga, `Shisha Pangma` → Shishapangma, `Gasherbrum 1` → Gasherbrum I.

## Command-Line Options

| Option   | Default | Description                                    |
|----------|---------|------------------------------------------------|
| `--peak` | Everest | Mountain name to visualize (see list above)    |

## Project Structure

```
mountain_profiles/
├── everest_3D.py      # Static 3D wireframe visualization
├── everest_3D_1.py    # Animated 3D wireframe (rotating)
├── wired_mountain.py  # Stylized wire silhouette (no API)
├── requirements.txt
├── .env               # API key (create this, do not commit)
└── README.md
```

## Troubleshooting

- **`ModuleNotFoundError`**: Run `pip install -r requirements.txt`
- **`REQUEST_DENIED`**: Enable the Elevation API in Google Cloud Console
- **`GOOGLE_MAPS_API_KEY not found`**: Create a `.env` file with `GOOGLE_MAPS_API_KEY=your_key`
- **400 Bad Request**: API key may be invalid or Elevation API may not be enabled
