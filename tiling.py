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
            for ax, ay in anchor_positions:
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
    row_distance = r
    col_distance = r
    
    circle_centers = []
    min_distance = r / density_factor

    def is_too_close(new_x, new_y):
        for (x, y) in circle_centers:
            distance = math.sqrt((new_x - x) ** 2 + (new_y - y) ** 2)
            if distance < min_distance:
                log_messages.append(
                    f"({x:.2f},{y:.2f}) and ({new_x:.2f},{new_y:.2f}) are {distance:.2f}m apart - need at least {min_distance:.2f}m"
                )
                return True
        return False

    def try_random_position():
        for attempt in range(attempts):
            rx = random.uniform(0, length)
            ry = random.uniform(0, width)
            if not is_too_close(rx, ry):
                circle_centers.append((rx, ry))
                log_messages.append(
                    f"Used random position ({rx:.2f}, {ry:.2f}) on attempt {attempt + 1}"
                )
                return True
        log_messages.append(f"Failed to find valid random position after {attempts} attempts.")
        return False

    def place_if_valid(x, y):
        if 0 <= x <= length and 0 <= y <= width:
            if not is_too_close(x, y):
                circle_centers.append((x, y))
                log_messages.append(
                    f"Used initial position ({x:.2f}, {y:.2f})"
                )
            else:
                log_messages.append(
                    f"Cannot use initial position ({x:.2f}, {y:.2f})"
                )
                try_random_position()

    for y in range(0, int(width), int(col_distance)):
        for x in range(0, int(length), int(row_distance)):
            place_if_valid(x, y)
            if y % 2 == 0:
                place_if_valid(x + row_distance / 2, y + col_distance / 2)

    for y in range(int(width), 0, -int(col_distance)):
        for x in range(int(length), 0, -int(row_distance)):
            place_if_valid(x, y)
            if y % 2 != 0:
                place_if_valid(x - row_distance / 2, y - col_distance / 2)

    for y in range(int(width), 0, -int(col_distance)):
        for x in range(0, int(length), int(row_distance)):
            place_if_valid(x, y)
            if y % 2 == 0:
                place_if_valid(x + row_distance / 2, y - col_distance / 2)

    for y in range(0, int(width), int(col_distance)):
        for x in range(int(length), 0, -int(row_distance)):
            place_if_valid(x, y)
            if y % 2 != 0:
                place_if_valid(x - row_distance / 2, y + col_distance / 2)

    return circle_centers

def plot_anchor_positions_with_heatmap(anchor_positions, length, width, radius, save_path=None):
    x_positions, y_positions = zip(*anchor_positions)

    plt.figure(figsize=(8, 8))
    plt.scatter(x_positions, y_positions, color='red', label='Anchor Positions')

    grid_size = 1
    grid_x = np.arange(0, length, grid_size)
    grid_y = np.arange(0, width, grid_size)
    heatmap = np.zeros((len(grid_y), len(grid_x)))

    for x, y in zip(x_positions, y_positions):
        for i in range(len(grid_x)):
            for j in range(len(grid_y)):
                distance = np.sqrt((grid_x[i] - x) ** 2 + (grid_y[j] - y) ** 2)
                if distance <= radius:
                    heatmap[j, i] += 1

    plt.imshow(heatmap, extent=[0, length, 0, width], origin='lower', cmap='YlGnBu', alpha=0.5)

    for (x, y) in zip(x_positions, y_positions):
        circle = plt.Circle((x, y), radius, color='blue', fill=False, linestyle='--')
        plt.gca().add_artist(circle)

    plt.xlim(0, length)
    plt.ylim(0, width)
    plt.xlabel('Length (m)')
    plt.ylabel('Width (m)')
    plt.grid(True)
    plt.title(f"Anchor Positions, Coverage Radius, and Overlap Heatmap for {length}m x {width}m Area")
    plt.legend(loc='best')
    plt.colorbar(label="Overlap Count per 1 m x 1 m")

    if save_path:
        plt.savefig(save_path)
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
        "y": f"{y:.2f}"
    }
    for i, (x, y) in enumerate(anchor_positions)
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
