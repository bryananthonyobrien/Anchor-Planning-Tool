import numpy as np
import math
import matplotlib.pyplot as plt
import json
import random
import os
import datetime

# Prepare logging
log_messages = []

def compute_coverage_stats(anchor_positions, length, width, radius):
    # Create a 1m x 1m grid
    step = 1
    covered_counts = []
    
    for y in range(0, int(width), step):
        for x in range(0, int(length), step):
            count = 0
            for ax, ay, *_ in anchor_positions:
                if math.hypot(ax - x, ay - y) <= radius:
                    count += 1
            covered_counts.append(count)
    
    max_overlap = max(covered_counts)
    histogram = {n: 0 for n in range(max_overlap + 1)}
    for c in covered_counts:
        histogram[c] += 1

    total = len(covered_counts)
    print("\n📊 Coverage Stats (per 1m² cell):")
    for n in sorted(histogram.keys()):
        percent = 100 * histogram[n] / total
        print(f"  Covered by {n} anchor(s): {percent:.2f}%")
    
    return histogram

def tile_rectangle_with_circles(length, width, r, log_messages):
    row_distance = r / rows_per_radius
    col_distance = r / cols_per_radius
    
    circle_centers = []
    min_distance = r / density_factor

    def is_too_close(new_x, new_y):
        for center in circle_centers:
            x, y = center[0], center[1]
            distance = math.sqrt((new_x - x) ** 2 + (new_y - y) ** 2)
            if distance < min_distance:
                log_messages.append(
                    f"({x:.2f},{y:.2f}) and ({new_x:.2f},{new_y:.2f}) are {distance:.2f}m apart - need at least {min_distance:.2f}m"
                )
                return True
        return False

    def try_random_position(loop_id):
        for attempt in range(attempts):
            rx = random.uniform(0, length)
            ry = random.uniform(0, width)
            if not is_too_close(rx, ry):
                circle_centers.append((rx, ry, loop_id))  # ✅ include loop_id here
                log_messages.append(
                    f"Used random position ({rx:.2f}, {ry:.2f}) on attempt {attempt + 1}"
                )
                return True
        log_messages.append(f"Failed to find valid random position after {attempts} attempts.")
        return False
    
    def place_if_valid(x, y, loop_id):
        if 0 <= x <= length and 0 <= y <= width:
            if not is_too_close(x, y):
                circle_centers.append((x, y, loop_id))
                log_messages.append(
                    f"Used initial position ({x:.2f}, {y:.2f}) from loop {loop_id}"
                )
            else:
                log_messages.append(
                    f"Cannot use initial position ({x:.2f}, {y:.2f}) from loop {loop_id}"
                )
                try_random_position(loop_id)
        else:
            log_messages.append(
                f"Cannot use initial position ({x:.2f}, {y:.2f}) out of bounds {loop_id}"
            )

    grid_points_checked = 0

    # Top-to-bottom, left-to-right, even rows offset
    # Pattern: Forward sweep
    # Grid: Regular grid
    # Even rows: Offset by half a row to simulate a hexagonal pattern
    
    loop_id = 1
    for y in range(0, int(width), int(col_distance)):
        for x in range(0, int(length), int(row_distance)):
            grid_points_checked += 1
            place_if_valid(x, y, loop_id)
            if y % 2 == 0:
                grid_points_checked += 1
                place_if_valid(x + row_distance / 2, y + col_distance / 2, loop_id)
                
    # Bottom-to-top, right-to-left, odd rows offset
    # Pattern: Reverse sweep
    # Offset: This time on odd rows
    # Purpose: Places anchors in slightly different positions missed in loop 1
    loop_id = 2
    for y in range(int(width), 0, -int(col_distance)):
        for x in range(int(length), 0, -int(row_distance)):
            place_if_valid(x, y, loop_id)
            grid_points_checked += 1
            if y % 2 != 0:
                grid_points_checked += 1
                place_if_valid(x - row_distance / 2, y - col_distance / 2, loop_id)

    # Bottom-to-top, left-to-right, even rows offset
    # Pattern: Alternating direction again
    # Offset: Opposite corner than before
    # Goal: Fill diagonal gaps and test symmetry
    loop_id = 3
    for y in range(int(width), 0, -int(col_distance)):
        for x in range(0, int(length), int(row_distance)):
            place_if_valid(x, y, loop_id)
            grid_points_checked += 1
            if y % 2 == 0:
                grid_points_checked += 1
                place_if_valid(x + row_distance / 2, y - col_distance / 2, loop_id)

    # Top-to-bottom, right-to-left, odd rows offset
    # Pattern: Final sweep
    # Offset: Completes the offsetting logic
    # Goal: Ensure full area is saturated without gaps, improving density when other placements fail
    loop_id = 4
    for y in range(0, int(width), int(col_distance)):
        for x in range(int(length), 0, -int(row_distance)):
            place_if_valid(x, y, loop_id)
            grid_points_checked += 1
            if y % 2 != 0:
                grid_points_checked += 1
                place_if_valid(x - row_distance / 2, y + col_distance / 2, loop_id)

    log_messages.append(f"🔍 Grid positions considered for placement: {grid_points_checked}")

    return circle_centers

def plot_anchor_positions_with_heatmap(anchor_positions, length, width, radius, save_path=None):
    num_anchors = len(anchor_positions)

    # Group by loop_id
    loop_groups = {}
    for x, y, loop_id in anchor_positions:
        loop_groups.setdefault(loop_id, []).append((x, y))

    plt.figure(figsize=(10, 10))
    
    # Scatter each group with a label
    for loop_id, coords in sorted(loop_groups.items()):
        xs, ys = zip(*coords)
        plt.scatter(xs, ys, label=f'Loop {loop_id} ({len(xs)})', alpha=0.7)

    # Prepare the heatmap grid
    grid_size = 1
    grid_x = np.arange(0, length, grid_size)
    grid_y = np.arange(0, width, grid_size)
    heatmap = np.zeros((len(grid_y), len(grid_x)))

    # Add coverage heatmap
    for x, y, _ in anchor_positions:
        for i in range(len(grid_x)):
            for j in range(len(grid_y)):
                distance = np.sqrt((grid_x[i] - x) ** 2 + (grid_y[j] - y) ** 2)
                if distance <= radius:
                    heatmap[j, i] += 1

    plt.imshow(heatmap, extent=[0, length, 0, width], origin='lower', cmap='YlGnBu', alpha=0.4)

    # Draw circles
    for x, y, _ in anchor_positions:
        circle = plt.Circle((x, y), radius, color='blue', fill=False, linestyle='--', alpha=0.3)
        plt.gca().add_artist(circle)

    plt.xlim(0, length)
    plt.ylim(0, width)
    plt.xlabel('Length (m)')
    plt.ylabel('Width (m)')
    plt.grid(True)
    plt.title(f"{num_anchors} Anchor Positions and Coverage Heatmap for {length}m x {width}m Area", pad=20)

    # Legend moved below the plot, centered
    plt.legend(
        loc='upper center',
        bbox_to_anchor=(0.5, -0.25),
        ncol=min(len(loop_groups), 4),
        frameon=False
    )

    plt.colorbar(label="Overlap Count per 1 m x 1 m")

    # Configuration table
    table_data = [
        ["Radius", config["radius"]],
        ["Length", config["length"]],
        ["Width", config["width"]],
        ["Attempts", config["attempts"]],
        ["Density Factor", config["density_factor"]],
        ["Rows per Radius", config["rows_per_radius"]],
        ["Cols per Radius", config["cols_per_radius"]],
    ]
    
    table = plt.gca().table(
        cellText=table_data,
        colLabels=["Configuration", "Value"],
        cellLoc='left',
        bbox=[0.1, -1.0, 0.8, 0.5],
    )
    table.auto_set_font_size(True)
    table.set_fontsize(11)
    table.scale(1.0, 1.0)

    # More room at the bottom for the legend and table
    plt.subplots_adjust(top=0.85, bottom=0.55, right=0.95)

    if save_path:
        plt.savefig(save_path, bbox_inches='tight')
        print(f"✅ Plot saved to: {save_path}")
    else:
        plt.show()

    plt.close()



# Load parameters from JSON
current_dir = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(current_dir, "coverage_density.json")

with open(json_path) as f:
    config = json.load(f)

length = config["length"]
width = config["width"]
radius = config["radius"]
attempts = config["attempts"]
density_factor = config["density_factor"]
rows_per_radius = config["rows_per_radius"]
cols_per_radius = config["cols_per_radius"]


# Get anchor positions
anchor_positions = tile_rectangle_with_circles(length, width, radius, log_messages)

print(f"Number of anchor positions: {len(anchor_positions)}")

# Generate timestamp
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
output_plot_path = os.path.join(current_dir, f"plot_{timestamp}.png")
output_json_path = os.path.join(current_dir, f"config_{timestamp}.json")
output_log_path = os.path.join(current_dir, f"config_{timestamp}.log")

with open(output_log_path, "w") as log_file:
    for message in log_messages:
        log_file.write(message + "\n")

coverage_stats = compute_coverage_stats(anchor_positions, length, width, radius)

# Append to log and save for JSON output
log_messages.append("\n📊 Coverage Stats (per 1m² cell):")
total = sum(coverage_stats.values())
sorted_counts = sorted(coverage_stats.items())
running_total = 0
coverage_percentages = {}

log_messages.append("\n📊 Coverage Stats (per 1m² cell, cumulative):")
for n, count in reversed(sorted_counts):
    running_total += count
    percent = 100 * running_total / total
    log_line = f"  Covered by {n} anchor(s): {percent:.2f}%"
    log_messages.append(log_line)
    coverage_percentages[str(n)] = round(percent, 2)

# Plot and save
plot_anchor_positions_with_heatmap(anchor_positions, length, width, radius, save_path=output_plot_path)

# Load config template
with open(os.path.join(current_dir, "config.json")) as f:
    config_template = json.load(f)

# Convert and inject anchors
anchor_dicts = [
    {
        "id": i + 1,
        "x": f"{x:.2f}",
        "y": f"{y:.2f}",
        "loop_id": loop_id  # Optional but useful!
    }
    for i, (x, y, loop_id) in enumerate(anchor_positions)
]
config_template["anchors"] = anchor_dicts

# Add tiling config and plot reference
config["plot_file"] = os.path.basename(output_plot_path)
config["log_file"] = os.path.basename(output_log_path)
config_template["tiling_config"] = config
config["coverage_stats"] = dict(sorted(coverage_percentages.items(), key=lambda item: int(item[0])))

# Save output config
with open(output_json_path, "w") as out:
    json.dump(config_template, out, indent=2)
    
    # Save log file at the end
with open(output_log_path, "w") as log_file:
    for message in log_messages:
        log_file.write(message + "\n")


print(f"\n✅ New config saved to: {output_json_path}")
