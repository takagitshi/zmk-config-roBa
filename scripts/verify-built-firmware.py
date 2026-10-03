#!/usr/bin/env python3
"""Verify contracts that only exist after ZMK has generated build files."""

from pathlib import Path
import re
import sys


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def node_body(dts: str, label: str) -> str:
    match = re.search(rf"\b{re.escape(label)}:\s*[^{{]+\{{(?P<body>.*?)\n\s*\}};", dts,
                      re.DOTALL)
    require(match is not None, f"generated node missing: {label}")
    return match.group("body")


def enabled(config: str, symbol: str) -> bool:
    return re.search(rf"^{re.escape(symbol)}=y$", config, re.MULTILINE) is not None


def main() -> int:
    if len(sys.argv) != 5:
        print("usage: verify-built-firmware.py RIGHT_DTS RIGHT_CONFIG LEFT_DTS LEFT_CONFIG",
              file=sys.stderr)
        return 2

    right_dts, right_config, left_dts, left_config = map(read, sys.argv[1:])
    sensor = node_body(right_dts, "trackball")
    listener = node_body(right_dts, "trackball_listener")
    normalized_listener = re.sub(r"\s+", "", listener)

    for name, dts in (("right-central", right_dts), ("left-peripheral", left_dts)):
        require("wakeup-source;" in node_body(dts, "kscan0"),
                f"{name} matrix wake source is missing")

    for prop in (
        'compatible = "pixart,pmw3610";',
        "reg = < 0x0 >;", "spi-max-frequency = < 0x1e8480 >;",
        "pointer-acceleration;",
        "pointer-acceleration-base-gain-milli = < 0x2ee >;",
        "pointer-acceleration-takeoff-speed = < 0x8 >;",
        "pointer-acceleration-full-speed = < 0x74 >;",
        "pointer-acceleration-max-gain-milli = < 0x5dc >;",
        "pointer-acceleration-reference-interval-ms = < 0x8 >;",
        "pointer-acceleration-idle-reset-ms = < 0x3c >;",
        "pointer-acceleration-scroll-layer = < 0x2 >;",
        "pointer-acceleration-gesture-layer = < 0x3 >;",
        "pointer-acceleration-gesture-layer-2 = < 0x4 >;",
    ):
        require(prop in sensor, f"generated pointer contract missing: {prop}")
    require("pointer-acceleration-precision" not in sensor,
            "generated curve unexpectedly retains a precision stage")

    for label, direction in (("encoder_key_divider_cw", "0x1"),
                             ("encoder_key_divider_ccw", "0x2")):
        divider = re.sub(r"\s+", "", node_body(right_dts, label))
        for prop in (
            'compatible="zmk,behavior-encoder-key-divider";',
            "divisor=<0x2>;", "timeout-ms=<0x12c>;", f"direction=<{direction}>;",
        ):
            require(prop in divider, f"generated {label} contract missing: {prop}")

    require(
        "input-processors=<&gesture_2_processor>,<&gesture_processor>,"
        "<&zip_temp_layer0x10x2710>;" in normalized_listener,
        "generated Pointer/Gesture/AML processor order changed",
    )
    require(
        "input-processors=<&zip_xy_to_scroll_mapper>,"
        "<&zip_scroll_transform0x4>,<&zip_scroll_scaler0x10xa>,"
        "<&zip_scroll_scaler0x10x4>;" in normalized_listener,
        "generated Scroll processor order changed",
    )
    require("process-next;" in normalized_listener,
            "generated Scroll chain no longer continues to HID")

    for label, layer_id in (("gesture_processor", "0x3"),
                            ("gesture_2_processor", "0x4")):
        processor = re.sub(r"\s+", "", node_body(right_dts, label))
        for prop in (
            f"layer=<{layer_id}>;", f"binding-layer=<{layer_id}>;",
            "up-position=<0x7>;", "left-position=<0x12>;",
            "right-position=<0x14>;", "down-position=<0x1f>;",
            "threshold=<0xb4>;", "cooldown-ms=<0x96>;",
        ):
            require(prop in processor, f"generated {label} contract missing: {prop}")

    layers = sorted({int(value) for value in re.findall(r"\blayer_(\d+)\s*\{", right_dts)})
    require(layers == list(range(10)), f"generated keymap is not exactly ten layers: {layers}")

    for symbol in (
        "CONFIG_ZMK_BLE", "CONFIG_ZMK_SPLIT", "CONFIG_ZMK_SPLIT_ROLE_CENTRAL",
        "CONFIG_ZMK_STUDIO", "CONFIG_ZMK_STUDIO_TRANSPORT_BLE",
        "CONFIG_ZMK_BEHAVIOR_ENCODER_KEY_DIVIDER",
        "CONFIG_PMW3610_POINTER_ACCELERATION", "CONFIG_ZMK_POINTING_SMOOTH_SCROLLING",
    ):
        require(enabled(right_config, symbol), f"right-central build missing {symbol}")
    for value in (
        'CONFIG_BT_DEVICE_NAME="roBa"', "CONFIG_PMW3610_CPI=800",
        "CONFIG_PMW3610_CPI_DIVIDOR=1", "CONFIG_PMW3610_ORIENTATION_180=y",
        "CONFIG_PMW3610_POLLING_RATE_125_SW=y", "CONFIG_PMW3610_SMART_ALGORITHM=y",
        "CONFIG_PMW3610_RUN_DOWNSHIFT_TIME_MS=3264",
        "CONFIG_PMW3610_REST1_SAMPLE_TIME_MS=20", "CONFIG_INPUT_THREAD_STACK_SIZE=4096",
    ):
        require(value in right_config, f"right-central config changed: {value}")
    require(not enabled(right_config, "CONFIG_PMW3610_FORCE_AWAKE"),
            "right-central unexpectedly enables force-awake")
    require(not enabled(right_config, "CONFIG_ZMK_SETTINGS_RESET_ON_START"),
            "right-central normal firmware would erase settings on boot")

    require(not enabled(right_config, "CONFIG_RGBLED_WIDGET"),
            "right-central unexpectedly enables the RGB LED widget")

    for symbol in ("CONFIG_ZMK_BLE", "CONFIG_ZMK_SPLIT"):
        require(enabled(left_config, symbol), f"left-peripheral build missing {symbol}")
    require(not enabled(left_config, "CONFIG_RGBLED_WIDGET"),
            "left-peripheral unexpectedly enables the RGB LED widget")
    require(not enabled(left_config, "CONFIG_ZMK_BEHAVIOR_ENCODER_KEY_DIVIDER"),
            "encoder divider must keep its state on the central side only")
    require(not enabled(left_config, "CONFIG_ZMK_SPLIT_ROLE_CENTRAL"),
            "left build unexpectedly became the split central")
    require(not enabled(left_config, "CONFIG_ZMK_SETTINGS_RESET_ON_START"),
            "left-peripheral normal firmware would erase settings on boot")
    require("steps = < 0xc >;" in node_body(left_dts, "left_encoder"),
            "roBa 12-step encoder hardware setting changed")
    left_listener = node_body(left_dts, "trackball_listener")
    require('status = "disabled";' in left_listener,
            "left-peripheral trackball listener is unexpectedly enabled")

    print("verify-built-firmware: PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"verify-built-firmware: FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
