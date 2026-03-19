"""
Level 2 — Basic Flight
========================
The simplest flight: arm, take off, hover, and land.

What you'll learn:
    - The arm → takeoff → land sequence
    - What target_height controls
    - How to safely test your first flight

SAFETY FIRST:
    - Clear the area around the drone
    - Stay at least 1 meter away
    - Be ready to run emergency_stop() if needed
"""

import time
import threading
from litewing import LiteWing
drone = LiteWing("192.168.43.42")

# ── Configure before flight ──────────────────────────
drone.target_height = 0.9    # Hover at 30cm (keep it low for first tests!)
drone.hover_duration = 30.0   # Hover for 3 seconds
drone.debug_mode = False

# ── Connect ──────────────────────────────────────────
drone.connect()
drone.clear_leds()
time.sleep(2)
# plot = drone.start_dashboard()
# Pre-flight check
# print(f"Battery: {drone.battery:.2f}V")
# if drone.battery < 3.3:
#     print("Battery too low! Charge before flying.")
#     drone.disconnect()
#     exit()

# ── LED indicator: ready to fly ──────────────────────
drone.set_led_color(0, 255, 0)  # Green = ready
time.sleep(1)
# ── Fly! ─────────────────────────────────────────────
print("Arming...")
drone.arm()
# drone.start_logging("my_flight_log.csv")
print(f"Taking off to {drone.target_height}m...")
drone.takeoff()

print(f"Hovering for {drone.hover_duration}s...")

# # Print all sensor readings every second in a background thread (non-blocking)
# def _print_sensors(duration):
#     end = time.time() + duration
#     while time.time() < end:
#         s = drone.read_sensors()
#         print(
#             f"  H:{s.height:.2f}m  "
#             f"Vel:({s.vx:.3f},{s.vy:.3f})m/s  "
#             f"Pos:({s.x:.3f},{s.y:.3f})m  "
#             f"RPY:({s.roll:.1f},{s.pitch:.1f},{s.yaw:.1f})°  "
#             f"Bat:{s.battery:.2f}V",
#             flush=True,
#         )
#         time.sleep(1.0)

# threading.Thread(target=_print_sensors, args=(drone.hover_duration,), daemon=True).start()
drone.hover(drone.hover_duration)  # position-hold loop runs here

print("Landing...")
drone.land()

# ── Done ─────────────────────────────────────────────
# drone.clear_leds()
# plot.stop(save_path="my_flight_plot.png")
# drone.stop_logging()
drone.disconnect()
print("Flight complete!")
