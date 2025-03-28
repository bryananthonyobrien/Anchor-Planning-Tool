# Anchor Placement & Simulation Tool

## Overview
This tool automates the placement of anchors (e.g., BLE beacons) within a rectangular area, evaluates signal coverage density, and outputs configuration files and diagnostics for indoor location system planning and simulation.

It uses multiple placement passes (called **loops**) to maximize coverage. Each anchor is tagged with its loop of origin and color-coded in the plot for visibility and debugging.

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
  "density_factor": 4,
  "rows_per_radius": 2,
  "cols_per_radius": 2
}
```

#### Parameters:
- **radius**: Signal range of each anchor in meters.
- **length / width**: Dimensions of the rectangular coverage area in meters.
- **attempts**: Number of random placement retries if a proposed anchor is too close to another.
- **density_factor**: Controls minimum spacing between anchors (`radius / density_factor`).
- **rows_per_radius**: Controls horizontal anchor grid density (`row_distance = radius / rows_per_radius`).
- **cols_per_radius**: Controls vertical anchor grid density (`col_distance = radius / cols_per_radius`).

> ⚠️ **Note**: If the area is too small relative to the radius, density tuning may have limited effect.

---

### `config.json`
Defines simulation and radio characteristics.

#### Key sections:
- **tag_path**: Walking path of a simulated tag.
- **device_profile**: Radio characteristics of the tag device (e.g. iPhone).
- **environment**: Propagation environment (path loss exponent, body attenuation).

#### Example:
```
{
  "tag_path": {
    "from_anchor_id": 1,
    "to_anchor_id": 2,
    "height_cm": 183,
    "mode": "steady_walk"
  },
  "device_profile": {
    "name": "iPhone",
    "P0": -49
  },
  "environment": {
    "path_loss_exponent": 2.0,
    "body_attenuation_dB": 6.0
  }
}
```
---

### `config_{timestamp}.json`
- `anchors`: List of generated anchor positions with `x`, `y`, `id`, and `loop_id`.
- `tiling_config`: Echo of all input parameters.
- `plot_file` / `log_file`: References to the output files.
- `coverage_stats`: Cumulative coverage percentages (per m²).

#### Example:
```{
  "anchors": [
    {
      "id": 1,
      "x": "0.00",
      "y": "0.00",
      "loop_id": 1
    },
    {
      "id": 2,
      "x": "15.09",
      "y": "19.10",
      "loop_id": 1
    },
    {
      "id": 3,
      "x": "10.43",
      "y": "10.29",
      "loop_id": 1
    },
    {
      "id": 4,
      "x": "16.55",
      "y": "5.76",
      "loop_id": 1
    },
    {
      "id": 5,
      "x": "1.60",
      "y": "17.90",
      "loop_id": 1
    },
    {
      "id": 6,
      "x": "2.09",
      "y": "7.32",
      "loop_id": 1
    },
    {
      "id": 7,
      "x": "20.00",
      "y": "13.00",
      "loop_id": 2
    },
    {
      "id": 8,
      "x": "8.34",
      "y": "1.00",
      "loop_id": 2
    }
  ],
  "tag_path": {
    "from_anchor_id": 1,
    "to_anchor_id": 2,
    "height_cm": 183,
    "mode": "steady_walk"
  },
  "device_profile": {
    "name": "iPhone",
    "P0": -49
  },
  "environment": {
    "path_loss_exponent": 2.0,
    "body_attenuation_dB": 6.0
  },
  "tiling_config": {
    "radius": 30,
    "length": 20,
    "width": 20,
    "attempts": 3,
    "density_factor": 4,
    "rows_per_radius": 4,
    "cols_per_radius": 4,
    "plot_file": "plot_20250328_102916.png",
    "log_file": "config_20250328_102916.log",
    "coverage_stats": {
      "0": 100.0,
      "1": 100.0,
      "2": 100.0,
      "3": 100.0,
      "4": 100.0,
      "5": 100.0,
      "6": 100.0,
      "7": 100.0,
      "8": 100.0
    }
  }
}
```

### `plot_{timestamp}.png`
A rendered plot showing:
- Colored dots for anchor positions, grouped by loop
- Blue dashed circles showing coverage area per anchor
- Background heatmap of overlap intensity
- Table of input configuration
- Legend below indicating loop origin

![Example Plot](examples/coverage_heatmap_example.png)

### `config_{timestamp}.log`
- Detailed log of placements
- Violations (too close)
- Fallback attempts
- Coverage stats

<details>
<summary>📂 Sample Log Snippet</summary>

```
Used initial position (0.00, 0.00) from loop 1  
Cannot use initial position (3.75, 3.75) from loop 1  
Used random position (15.09, 19.10) on attempt 1  
...
📊 Coverage Stats (per 1m² cell, cumulative):
  Covered by 8 anchor(s): 100.00%
  Covered by 7 anchor(s): 100.00%
  ...
```

</details>

---

## Tiling Strategy: Multi-Loop Coverage

The anchor placement algorithm performs four grid sweeps (called loops) with different biases to avoid blind spots and ensure uniform density:

| Loop | Direction               | Offset Logic                     | Purpose                                    |
|------|-------------------------|----------------------------------|--------------------------------------------|
| 1    | Top→Bottom, Left→Right  | Even rows offset (hex grid)      | Main sweep with hex-like symmetry          |
| 2    | Bottom→Top, Right→Left  | Odd rows offset                  | Alternate sweep to fill skipped gaps       |
| 3    | Bottom→Top, Left→Right  | Even rows, opposite corner offset| Reinforcement sweep for symmetry           |
| 4    | Top→Bottom, Right→Left  | Odd rows offset                  | Final sweep to fill remaining gaps         |

If a proposed anchor is too close to an existing one, the tool will attempt up to `attempts` random fallback placements.

Each anchor is tagged with its `loop_id`, and the plot colors reflect which loop placed it.

---

## Coverage Metrics
Coverage is computed at 1m² resolution. Each cell records how many anchors cover it.

The tool outputs a **cumulative coverage histogram**, showing what percentage of the area is covered by at least `n` anchors:

#### Example:
```
📊 Coverage Stats (per 1m² cell, cumulative):
  Covered by 8 anchor(s): 100.00%
  Covered by 7 anchor(s): 100.00%
  ...
```

This helps assess redundancy and area coverage quality.

---

## Usage

1. Edit `coverage_density.json` and `config.json` with your parameters.
2. Run the tool:

```bash
python tiling.py
```

3. Review the generated files:
   - `plot_*.png`: Visual output
   - `config_*.json`: Anchor + environment config
   - `config_*.log`: Diagnostic logs

---

## 🐳 Docker Support (No Python setup required)

You can run the tool inside Docker for portability:

### 1. Build:
```bash
docker build -t anchor-tiling-tool .
```

### 2. Run:
```bash
docker run --rm -v $(pwd):/app anchor-tiling-tool
```

Ensure `coverage_density.json` and `config.json` exist in your working directory.

---

## License
MIT or similar license placeholder.

---

## Author
Bryan O'Brien / Personal Projects