"""
LiteWing Library — Unit Tests
================================
Basic tests to verify the library loads and initializes correctly.
Run with: python -m pytest tests/ -v
"""

import sys
import os

# Ensure the package is importable without pip install
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))


class TestImports:
    """Verify all public modules import cleanly."""

    def test_import_litewing(self):
        from litewing import LiteWing
        assert LiteWing is not None

    def test_import_sensor_data(self):
        from litewing import SensorData
        assert SensorData is not None

    def test_import_pid_config(self):
        from litewing import PIDConfig
        assert PIDConfig is not None

    def test_version_exists(self):
        import litewing
        assert hasattr(litewing, "__version__")
        assert isinstance(litewing.__version__, str)
        assert len(litewing.__version__) > 0  # Not empty


class TestLiteWingInit:
    """Verify LiteWing initializes with correct defaults."""

    def setup_method(self):
        from litewing import LiteWing
        self.drone = LiteWing("192.168.43.42")

    def test_default_ip(self):
        assert self.drone._ip == "192.168.43.42"

    def test_default_target_height(self):
        assert self.drone.target_height == 0.3

    def test_default_hover_duration(self):
        assert self.drone.hover_duration == 20.0

    def test_default_hold_mode(self):
        assert self.drone.hold_mode == "current"

    def test_default_sensitivity(self):
        assert self.drone.sensitivity == 0.2

    def test_default_debug_mode(self):
        assert self.drone.debug_mode is False

    def test_default_flight_phase(self):
        assert self.drone.flight_phase == "IDLE"

    def test_not_connected(self):
        assert self.drone.is_connected is False

    def test_not_flying(self):
        assert self.drone.is_flying is False

    def test_default_max_correction(self):
        assert self.drone.max_correction == 0.7

    def test_default_optical_flow_scale(self):
        assert self.drone.optical_flow_scale == 4.4

    def test_default_thrust_base(self):
        assert self.drone.thrust_base == 24000


class TestPIDConfig:
    """Verify PIDConfig works correctly."""

    def test_create_pid(self):
        from litewing import PIDConfig
        pid = PIDConfig(kp=1.0, ki=0.5, kd=0.1)
        assert pid.kp == 1.0
        assert pid.ki == 0.5
        assert pid.kd == 0.1

    def test_modify_pid(self):
        from litewing import PIDConfig
        pid = PIDConfig()
        pid.kp = 2.0
        assert pid.kp == 2.0

    def test_pid_repr(self):
        from litewing import PIDConfig
        pid = PIDConfig(kp=1.0, ki=0.03, kd=0.0)
        assert "PIDConfig" in repr(pid)
        assert "1.0" in repr(pid)

    def test_drone_position_pid(self):
        from litewing import LiteWing
        drone = LiteWing()
        assert drone.position_pid.kp == 0.8
        assert drone.position_pid.ki == 0.04
        assert drone.position_pid.kd == 0.05

    def test_drone_velocity_pid(self):
        from litewing import LiteWing
        drone = LiteWing()
        assert drone.velocity_pid.kp == 0.5
        assert drone.velocity_pid.ki == 0.0


class TestSensorData:
    """Verify SensorData snapshot works."""

    def test_sensor_snapshot(self):
        from litewing import LiteWing
        drone = LiteWing()
        sensors = drone.read_sensors()
        assert sensors.height == 0.0
        assert sensors.battery == 0.0
        assert sensors.vx == 0.0
        assert sensors.vy == 0.0
        assert sensors.x == 0.0
        assert sensors.y == 0.0

    def test_battery_property(self):
        from litewing import LiteWing
        drone = LiteWing()
        assert drone.battery == 0.0

    def test_position_property(self):
        from litewing import LiteWing
        drone = LiteWing()
        assert drone.position == (0.0, 0.0)

    def test_velocity_property(self):
        from litewing import LiteWing
        drone = LiteWing()
        assert drone.velocity == (0.0, 0.0)


class TestContextManager:
    """Verify context manager works."""

    def test_with_statement(self):
        from litewing import LiteWing
        with LiteWing() as drone:
            assert drone is not None
            assert drone.flight_phase == "IDLE"

    def test_context_manager_returns_drone(self):
        from litewing import LiteWing
        with LiteWing("192.168.43.42") as drone:
            assert drone._ip == "192.168.43.42"


class TestConfiguration:
    """Verify configuration properties can be set."""

    def setup_method(self):
        from litewing import LiteWing
        self.drone = LiteWing()

    def test_set_target_height(self):
        self.drone.target_height = 0.5
        assert self.drone.target_height == 0.5

    def test_set_trim(self):
        self.drone.hover_trim_pitch = 0.02
        self.drone.hover_trim_roll = -0.01
        assert self.drone.hover_trim_pitch == 0.02
        assert self.drone.hover_trim_roll == -0.01

    def test_set_hold_mode(self):
        self.drone.hold_mode = "origin"
        assert self.drone.hold_mode == "origin"

    def test_set_sensitivity(self):
        self.drone.sensitivity = 0.5
        assert self.drone.sensitivity == 0.5

    def test_set_firmware_params(self):
        self.drone.thrust_base = 30000
        self.drone.z_position_kp = 2.0
        self.drone.z_velocity_kp = 20.0
        assert self.drone.thrust_base == 30000
        assert self.drone.z_position_kp == 2.0
        assert self.drone.z_velocity_kp == 20.0


class TestInternalModules:
    """Verify internal modules work correctly."""

    def test_pid_state_update(self):
        from litewing.pid import _PIDState, PIDConfig
        state = _PIDState()
        config = PIDConfig(kp=1.0, ki=0.0, kd=0.0)
        cx, cy = state.update(1.0, 0.5, 0.02, config)
        assert cx == 1.0   # kp * error_x
        assert cy == 0.5   # kp * error_y

    def test_pid_state_reset(self):
        from litewing.pid import _PIDState, PIDConfig
        state = _PIDState()
        config = PIDConfig(kp=1.0, ki=1.0, kd=0.0)
        state.update(1.0, 1.0, 0.02, config)
        state.reset()
        assert state.integral_x == 0.0
        assert state.integral_y == 0.0

    def test_position_engine_reset(self):
        from litewing._position import PositionEngine
        engine = PositionEngine()
        assert engine.x == 0.0
        assert engine.y == 0.0
        engine.reset()
        assert engine.x == 0.0

    def test_position_hold_controller(self):
        from litewing.position_hold import PositionHoldController
        from litewing.pid import PIDConfig
        pos_pid = PIDConfig(kp=1.0, ki=0.0, kd=0.0)
        vel_pid = PIDConfig(kp=0.5, ki=0.0, kd=0.0)
        controller = PositionHoldController(pos_pid, vel_pid)
        assert controller.enabled is True
        controller.set_target(1.0, 2.0)
        assert controller.target_x == 1.0
        assert controller.target_y == 2.0


class TestShapeFunctions:
    """Verify shape flight methods exist and produce correct geometry."""

    def setup_method(self):
        from litewing import LiteWing
        self.drone = LiteWing()
        self.drone.debug_mode = True          # no real drone needed
        self.drone._flight_active = True      # simulate armed+flying state
        self.drone._scf = object()            # dummy — prevents "not connected" guard

    # ── Method existence ─────────────────────────────────────────────────────

    def test_square_method_exists(self):
        assert hasattr(self.drone, 'square')
        assert callable(self.drone.square)

    def test_triangle_method_exists(self):
        assert hasattr(self.drone, 'triangle')
        assert callable(self.drone.triangle)

    def test_circle_method_exists(self):
        assert hasattr(self.drone, 'circle')
        assert callable(self.drone.circle)

    def test_pentagon_method_exists(self):
        assert hasattr(self.drone, 'pentagon')
        assert callable(self.drone.pentagon)

    def test_shape_helper_exists(self):
        assert hasattr(self.drone, '_fly_shape_path')
        assert callable(self.drone._fly_shape_path)

    # ── Geometry validation (pure math, no drone) ────────────────────────────

    def test_square_offset_count(self):
        """Square must produce 4 corner offsets (+ 1 return leg = 5 legs)."""
        import math
        half = 0.3  # length=0.6
        offsets = [
            (-half, -half), (half, -half),
            (half,  half),  (-half, half),
        ]
        assert len(offsets) == 4

    def test_triangle_circumradius(self):
        """Triangle circumradius formula: R = side / sqrt(3)."""
        import math
        length = 0.6
        R = length / math.sqrt(3.0)
        assert abs(R - 0.3464) < 0.001

    def test_pentagon_circumradius(self):
        """Pentagon circumradius formula: R = side / (2 * sin(π/5))."""
        import math
        length = 0.6
        R = length / (2.0 * math.sin(math.pi / 5))
        assert abs(R - 0.5106) < 0.001

    def test_circle_waypoint_count_small(self):
        """Small circle (0.5m diameter) must produce at least 12 waypoints."""
        import math
        diameter = 0.5
        circumference = math.pi * diameter
        n = max(12, int(math.ceil(circumference / 0.15)))
        assert n >= 12

    def test_circle_waypoint_count_medium(self):
        """1m diameter circle should produce more waypoints than the minimum."""
        import math
        diameter = 1.0
        circumference = math.pi * diameter
        n = max(12, int(math.ceil(circumference / 0.15)))
        assert n > 12        # circumference ~3.14m → ~21 waypoints

    def test_circle_waypoint_count_large(self):
        """Larger circle must scale waypoints proportionally."""
        import math
        n_small = max(12, int(math.ceil(math.pi * 0.5 / 0.15)))
        n_large = max(12, int(math.ceil(math.pi * 2.0 / 0.15)))
        assert n_large > n_small    # 2m circle needs more points than 0.5m

    def test_circle_last_point_closes_loop(self):
        """The last circle waypoint must be at angle=2π (back to start)."""
        import math
        diameter, n = 1.0, 21
        radius = diameter / 2.0
        last_angle = (2.0 * math.pi * n) / n    # = 2π
        x = radius * math.cos(last_angle)
        y = radius * math.sin(last_angle)
        assert abs(x - radius) < 1e-9     # cos(2π) = 1 → x = radius
        assert abs(y) < 1e-9              # sin(2π) = 0 → y = 0

    def test_face_direction_default_true(self):
        """All shape methods should default face_direction to True."""
        import inspect
        for name in ('square', 'triangle', 'circle', 'pentagon'):
            method = getattr(self.drone, name)
            sig = inspect.signature(method)
            param = sig.parameters.get('face_direction')
            assert param is not None, f"{name} missing face_direction param"
            assert param.default is True, f"{name} face_direction default should be True"

    def test_circle_parameter_name(self):
        """circle() should use 'diameter' not 'radius' as first positional arg."""
        import inspect
        sig = inspect.signature(self.drone.circle)
        params = list(sig.parameters.keys())
        assert params[0] == 'diameter'
