# Anchor Placement & Simulation Tool

## Overview
This tool automates the placement of anchors (e.g., BLE beacons) within a rectangular area, evaluates signal coverage density, and outputs configuration files and diagnostics for indoor location system planning and simulation.

---

## Inputs

### `coverage_density.json`
Defines spatial and tiling parameters.

#### Example:
```json
{
  "radius": 30,
  "length": 100,
  "width": 100,
  "attempts": 30,
  "density_factor": 4
}
```

#### Parameters:
- **radius**: Signal range of each anchor in meters.
- **length / width**: Dimensions of the rectangular coverage area in meters.
- **attempts**: Number of random placement retries if a proposed anchor is too close to another.
- **density_factor**: Controls spacing. Minimum allowed distance between anchors is `radius / density_factor`.

### `config.json`
Provides simulation parameters.

#### Key sections:
- **anchors**: Placeholder list to be replaced by generated anchors.
- **tag_path**: Walking path of a simulated tag.
- **device_profile**: Radio characteristics of the device.
- **environment**: Signal propagation characteristics like path loss and body attenuation.

---

## Outputs

### `config_{timestamp}.json`
- **anchors**: List of placed anchors with `x`, `y`, and `id`.
- **tiling_config**: Echo of input from `coverage_density.json`.
- **plot_file**: Name of generated PNG showing placement and heatmap.
- **log_file**: Diagnostic log file.
- **coverage_stats**: Cumulative coverage histogram.

### `plot_{timestamp}.png`
- Visual heatmap showing:
  - Anchor locations (red dots)
  - Signal coverage areas (blue circles)
  - Overlap intensity in background heatmap

### `config_{timestamp}.log`
- Anchor spacing violations
- Random placement attempts
- Cumulative coverage statistics

---

## Tiling Strategy
The anchor placement algorithm uses four passes with hexagonal bias:
1. Left to right, top to bottom
2. Right to left, bottom to top
3. Left to right, bottom to top
4. Right to left, top to bottom

If a position is too close to existing anchors, random fallback positions are attempted (up to `attempts` times).

---

## Coverage Metrics
Coverage is sampled at 1m² resolution. The tool calculates the cumulative percentage of the area covered by at least `n` anchors.

### Sample Output:
```
📊 Coverage Stats (per 1m² cell, cumulative):
  Covered by 6 anchor(s): 99.99%
  Covered by 10 anchor(s): 75.40%
  Covered by 14 anchor(s): 33.65%
```

These statistics help evaluate how well the space is covered and how robust signal redundancy is across the deployment area.

---

## Usage
1. Edit `coverage_density.json` with your area and constraints.
2. Run the tool.
3. Review outputs:
   - `config_*.json` for system configuration
   - `plot_*.png` for visual validation
   - `config_*.log` for diagnostics
4. Use `config_*.json` in downstream simulation tools.

---

## License
MIT or similar license placeholder.

---

## Author
Your Name / Team - 2025

