"""
LiteWing Blackbox Playback
============================
Post-flight analysis tool that reads a CSV flight log and renders
a rich multi-panel dashboard for visual review.

Usage:
    python blackbox_playback.py                        # uses default my_flight_log.csv
    python blackbox_playback.py path/to/flight.csv     # custom log file

Panels:
    1. Position Trail  — XY dead-reckoning path (top-down, forward=up)
    2. Height          — Filtered + Raw + Target height over time
    3. Attitude        — Roll, Pitch, Yaw over time
    4. Velocity + PID  — VX/VY and Correction VX/VY
    5. Battery         — Voltage curve with threshold marker
    6. Commands        — Commanded VX/VY sent to the drone

No drone connection required — works entirely from the CSV file.
"""

import csv
import sys
import os

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.collections import LineCollection
import numpy as np


# ─── Dark theme ──────────────────────────────────────────────────────
def _apply_dark_theme():
    plt.rcParams.update({
        "figure.facecolor": "#1e1e2e",
        "axes.facecolor": "#2a2a3d",
        "axes.edgecolor": "#444466",
        "axes.labelcolor": "#cdd6f4",
        "text.color": "#cdd6f4",
        "xtick.color": "#a6adc8",
        "ytick.color": "#a6adc8",
        "grid.color": "#3a3a5c",
        "grid.alpha": 0.5,
        "lines.linewidth": 1.4,
        "font.size": 9,
        "axes.titlesize": 11,
        "axes.titleweight": "bold",
        "figure.titlesize": 14,
        "figure.titleweight": "bold",
    })


COLORS = {
    "cyan":   "#89dceb",
    "green":  "#a6e3a1",
    "yellow": "#f9e2af",
    "red":    "#f38ba8",
    "mauve":  "#cba6f7",
    "blue":   "#89b4fa",
    "peach":  "#fab387",
    "teal":   "#94e2d5",
    "pink":   "#f5c2e7",
}

# Flight phase → color mapping for background bands
PHASE_COLORS = {
    "TAKEOFF":   "#45475a",
    "HOVER":     "#313244",
    "HOVERING":  "#313244",
    "LANDING":   "#45475a",
    "STABILIZE": "#3b3b55",
    "MOVE":      "#2d3a4a",
    "WAYPOINT":  "#2d4a3a",
    "MANUAL":    "#4a2d3a",
}


# ─── CSV Reader ──────────────────────────────────────────────────────
def load_flight_log(filepath):
    """Read a LiteWing CSV flight log and return a dict of numpy arrays."""
    data = {
        "time": [], "pos_x": [], "pos_y": [],
        "height": [], "range": [], "vx": [], "vy": [],
        "corr_vx": [], "corr_vy": [],
        "battery": [], "roll": [], "pitch": [], "yaw": [],
        "gyro_x": [], "gyro_y": [], "gyro_z": [],
        "phase": [], "target_h": [],
        "cmd_vx": [], "cmd_vy": [],
    }

    with open(filepath, "r") as f:
        reader = csv.reader(f)
        header = next(reader)  # skip header

        for row in reader:
            if len(row) < 20:
                continue
            try:
                data["time"].append(float(row[0]))
                data["pos_x"].append(float(row[1]))
                data["pos_y"].append(float(row[2]))
                data["height"].append(float(row[3]))
                data["range"].append(float(row[4]))
                data["vx"].append(float(row[5]))
                data["vy"].append(float(row[6]))
                data["corr_vx"].append(float(row[7]))
                data["corr_vy"].append(float(row[8]))
                data["battery"].append(float(row[9]))
                data["roll"].append(float(row[10]))
                data["pitch"].append(float(row[11]))
                data["yaw"].append(float(row[12]))
                data["gyro_x"].append(float(row[13]))
                data["gyro_y"].append(float(row[14]))
                data["gyro_z"].append(float(row[15]))
                data["phase"].append(row[16].strip())
                data["target_h"].append(float(row[17]))
                data["cmd_vx"].append(float(row[18]))
                data["cmd_vy"].append(float(row[19]))
            except (ValueError, IndexError):
                continue

    # Convert to numpy arrays (except phase which stays as list)
    for key in data:
        if key != "phase":
            data[key] = np.array(data[key])

    return data


# ─── Flight phase background bands ──────────────────────────────────
def _draw_phase_bands(ax, time, phases):
    """Draw semi-transparent colored background bands for each flight phase."""
    if len(phases) == 0:
        return

    current_phase = phases[0]
    phase_start = time[0]

    for i in range(1, len(phases)):
        if phases[i] != current_phase or i == len(phases) - 1:
            phase_end = time[i]
            color = PHASE_COLORS.get(current_phase, "#2a2a3d")
            ax.axvspan(phase_start, phase_end, alpha=0.3, color=color, linewidth=0)
            current_phase = phases[i]
            phase_start = time[i]


# ─── Position trail with phase coloring ──────────────────────────────
def _draw_position_trail(ax, data):
    """Draw XY position trail, color-coded by flight phase."""
    # Map to screen: forward (X) = up, left (Y) = left
    x_screen = -data["pos_y"]  # negate so +Y (left) goes left on screen
    y_screen = data["pos_x"]   # +X (forward) goes up on screen

    if len(x_screen) < 2:
        return

    # Create phase-colored trail segments
    phase_color_map = {
        "TAKEOFF": COLORS["green"],
        "HOVER":   COLORS["cyan"],
        "HOVERING": COLORS["cyan"],
        "LANDING": COLORS["red"],
        "STABILIZE": COLORS["yellow"],
        "MOVE":    COLORS["blue"],
        "WAYPOINT": COLORS["mauve"],
        "MANUAL":  COLORS["peach"],
    }

    # Draw segments colored by phase
    for i in range(len(x_screen) - 1):
        phase = data["phase"][i]
        color = phase_color_map.get(phase, COLORS["cyan"])
        ax.plot(
            [x_screen[i], x_screen[i + 1]],
            [y_screen[i], y_screen[i + 1]],
            color=color, linewidth=1.5, alpha=0.7,
        )

    # Start marker
    ax.plot(x_screen[0], y_screen[0], 's', color=COLORS["green"],
            markersize=12, zorder=5, label="Start")
    # End marker
    ax.plot(x_screen[-1], y_screen[-1], 'o', color=COLORS["red"],
            markersize=10, zorder=5, label="End")

    # Labels
    ax.set_xlabel("← Right / Left → (m)")
    ax.set_ylabel("← Backward / Forward → (m)")
    ax.set_title("Position Trail (Dead Reckoning)")
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(True)
    ax.set_aspect("equal", adjustable="datalim")

    # Phase legend
    patches = []
    for phase, color in phase_color_map.items():
        if phase in data["phase"]:
            patches.append(mpatches.Patch(color=color, alpha=0.7, label=phase))
    if patches:
        leg2 = ax.legend(handles=patches, loc="lower right", fontsize=7,
                         title="Phase", title_fontsize=8)
        ax.add_artist(leg2)
        # Re-add start/end legend
        ax.legend(loc="upper right", fontsize=8)


# ─── Main dashboard ─────────────────────────────────────────────────
def render_dashboard(data, filepath):
    """Render the full 6-panel dashboard."""
    _apply_dark_theme()

    fig = plt.figure(figsize=(16, 10))
    fig.suptitle(
        f"LiteWing Blackbox — {os.path.basename(filepath)}",
        color=COLORS["cyan"], fontsize=14, fontweight="bold",
    )

    # Layout: 3 rows x 2 cols
    ax_pos  = fig.add_subplot(3, 2, 1)  # Position trail
    ax_h    = fig.add_subplot(3, 2, 2)  # Height
    ax_att  = fig.add_subplot(3, 2, 3)  # Attitude
    ax_vel  = fig.add_subplot(3, 2, 4)  # Velocity + Corrections
    ax_bat  = fig.add_subplot(3, 2, 5)  # Battery
    ax_cmd  = fig.add_subplot(3, 2, 6)  # Commands

    t = data["time"]

    # ── Panel 1: Position Trail ──
    _draw_position_trail(ax_pos, data)

    # ── Panel 2: Height ──
    _draw_phase_bands(ax_h, t, data["phase"])
    ax_h.plot(t, data["height"], color=COLORS["cyan"], label="Filtered (Kalman)", linewidth=1.5)
    ax_h.plot(t, data["range"], color=COLORS["peach"], label="Raw ToF", alpha=0.6, linewidth=1.0)
    ax_h.plot(t, data["target_h"], color=COLORS["red"], label="Target", linestyle="--",
              alpha=0.8, linewidth=1.2)
    ax_h.set_title("Height")
    ax_h.set_ylabel("meters")
    ax_h.legend(loc="upper right", fontsize=7)
    ax_h.grid(True)

    # ── Panel 3: Attitude ──
    _draw_phase_bands(ax_att, t, data["phase"])
    ax_att.plot(t, data["roll"], color=COLORS["red"], label="Roll", alpha=0.8)
    ax_att.plot(t, data["pitch"], color=COLORS["green"], label="Pitch", alpha=0.8)
    ax_att.plot(t, data["yaw"], color=COLORS["yellow"], label="Yaw", alpha=0.8)
    ax_att.set_title("Attitude (IMU)")
    ax_att.set_ylabel("degrees")
    ax_att.legend(loc="upper right", fontsize=7)
    ax_att.grid(True)

    # ── Panel 4: Velocity + Corrections ──
    _draw_phase_bands(ax_vel, t, data["phase"])
    ax_vel.plot(t, data["vx"], color=COLORS["blue"], label="VX (fwd)", linewidth=1.3)
    ax_vel.plot(t, data["vy"], color=COLORS["mauve"], label="VY (lat)", linewidth=1.3)
    ax_vel.plot(t, data["corr_vx"], color=COLORS["teal"], label="Corr VX",
                linestyle="--", alpha=0.7, linewidth=1.0)
    ax_vel.plot(t, data["corr_vy"], color=COLORS["pink"], label="Corr VY",
                linestyle="--", alpha=0.7, linewidth=1.0)
    ax_vel.set_title("Velocity & PID Corrections")
    ax_vel.set_ylabel("m/s")
    ax_vel.legend(loc="upper right", fontsize=7)
    ax_vel.grid(True)

    # ── Panel 5: Battery ──
    _draw_phase_bands(ax_bat, t, data["phase"])
    ax_bat.plot(t, data["battery"], color=COLORS["green"], linewidth=2)
    ax_bat.axhline(y=2.9, color=COLORS["yellow"], linestyle="--", alpha=0.7, label="Low (2.9V)")
    ax_bat.axhline(y=2.7, color=COLORS["red"], linestyle="--", alpha=0.7, label="Critical (2.7V)")
    ax_bat.set_title("Battery")
    ax_bat.set_ylabel("volts")
    ax_bat.set_xlabel("Time (s)")
    ax_bat.legend(loc="upper right", fontsize=7)
    ax_bat.grid(True)
    # Filter out zero readings for better y-axis range
    bat_valid = data["battery"][data["battery"] > 0]
    if len(bat_valid) > 0:
        ax_bat.set_ylim(min(bat_valid.min(), 2.6) - 0.1, bat_valid.max() + 0.1)

    # ── Panel 6: Commands ──
    _draw_phase_bands(ax_cmd, t, data["phase"])
    ax_cmd.plot(t, data["cmd_vx"], color=COLORS["blue"], label="Cmd VX (→ pitch)", linewidth=1.3)
    ax_cmd.plot(t, data["cmd_vy"], color=COLORS["mauve"], label="Cmd VY (→ roll)", linewidth=1.3)
    ax_cmd.set_title("Commanded Velocities")
    ax_cmd.set_ylabel("m/s")
    ax_cmd.set_xlabel("Time (s)")
    ax_cmd.legend(loc="upper right", fontsize=7)
    ax_cmd.grid(True)

    # ── Summary stats ──
    duration = t[-1] - t[0] if len(t) > 1 else 0
    max_drift = max(
        abs(data["pos_x"].max()), abs(data["pos_x"].min()),
        abs(data["pos_y"].max()), abs(data["pos_y"].min()),
    ) if len(data["pos_x"]) > 0 else 0
    avg_h = data["height"].mean() if len(data["height"]) > 0 else 0
    min_bat = bat_valid.min() if len(bat_valid) > 0 else 0

    # Phase summary
    phase_counts = {}
    for p in data["phase"]:
        phase_counts[p] = phase_counts.get(p, 0) + 1

    phases_str = " → ".join(
        f"{p}({c})" for p, c in phase_counts.items()
    )

    fig.text(
        0.5, 0.01,
        f"Duration: {duration:.1f}s  |  Max drift: {max_drift:.3f}m  |  "
        f"Avg height: {avg_h:.3f}m  |  Min battery: {min_bat:.2f}V  |  "
        f"Phases: {phases_str}",
        ha="center", fontsize=8, color="#a6adc8",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#1e1e2e", edgecolor="#444466"),
    )

    fig.subplots_adjust(hspace=0.45, wspace=0.28, top=0.93, bottom=0.06)
    plt.show()


# ─── Entry point ─────────────────────────────────────────────────────
if __name__ == "__main__":
    # Default log path
    default_log = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "..", "..", "..", "my_flight_log.csv"
    )
    default_log = os.path.normpath(default_log)

    if len(sys.argv) > 1:
        log_path = sys.argv[1]
    elif os.path.exists(default_log):
        log_path = default_log
    else:
        print("Usage: python blackbox_playback.py [path/to/flight_log.csv]")
        print(f"  No file provided and default not found: {default_log}")
        sys.exit(1)

    if not os.path.exists(log_path):
        print(f"Error: File not found: {log_path}")
        sys.exit(1)

    print(f"Loading flight log: {log_path}")
    data = load_flight_log(log_path)
    print(f"  {len(data['time'])} data points loaded")
    print(f"  Duration: {data['time'][-1] - data['time'][0]:.1f}s")
    print(f"  Phases: {' → '.join(dict.fromkeys(data['phase']))}")
    print("Rendering dashboard...")
    render_dashboard(data, log_path)
