"""
Optical Flow Axis Diagnostic
==============================
Slide the drone slowly on a flat surface to find which
raw sensor axis corresponds to which physical direction.

How to use:
  1. Place the drone on a flat, textured surface (paper/carpet works well)
  2. Run this script and let it connect
  3. Slowly slide the drone FORWARD (nose direction) — watch which value changes
  4. Slide it SIDEWAYS (left) — watch which value changes
  5. Note the axis and sign for each direction

Expected result (will tell you sensor orientation):
  - If deltaX changes when moving FORWARD → deltaX = forward axis
  - If deltaY changes when moving FORWARD → deltaY = forward axis
"""

import time
from litewing import LiteWing

DRONE_IP = "192.168.43.42"
SAMPLE_COUNT = 5   # average over N samples before printing

drone = LiteWing(DRONE_IP)

print("Connecting to drone...")
drone.connect()
print("Connected! Sensor streaming.\n")
print("=" * 55)
print(f"{'Time':>6}  {'deltaX':>8}  {'deltaY':>8}  {'Move direction':}")
print("=" * 55)
print(">>> Slide drone FORWARD slowly and watch which value moves")
print(">>> Then slide LEFT and observe the other axis")
print(">>> Press Ctrl+C to stop\n")

try:
    while True:
        dx_accum = []
        dy_accum = []

        # Collect a burst of samples using the RAW firmware values
        # (bypasses any axis remapping done in the position engine)
        for _ in range(SAMPLE_COUNT):
            # Access raw firmware deltaX/deltaY directly from internal sensor state
            dx_accum.append(drone._sensors.raw_delta_x)
            dy_accum.append(drone._sensors.raw_delta_y)
            time.sleep(0.02)

        # Average them to reduce noise
        avg_dx = sum(dx_accum) / len(dx_accum)
        avg_dy = sum(dy_accum) / len(dy_accum)

        # Determine dominant direction hint
        thresh = 2.0
        if abs(avg_dx) > thresh or abs(avg_dy) > thresh:
            if abs(avg_dx) > abs(avg_dy):
                hint = f"← deltaX dominant ({'+ left' if avg_dx > 0 else '- right'})"
            else:
                hint = f"← deltaY dominant ({'+ forward' if avg_dy > 0 else '- backward'})"
        else:
            hint = "(still / noise)"

        t = time.strftime("%H:%M:%S")
        print(f"{t}   dX={avg_dx:+7.1f}   dY={avg_dy:+7.1f}   {hint}")

except KeyboardInterrupt:
    print("\n\nStopping.")
finally:
    drone.disconnect()
    print("Disconnected.")
