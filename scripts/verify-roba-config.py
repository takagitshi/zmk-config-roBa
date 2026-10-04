#!/usr/bin/env python3
"""Fast source-level contracts for the customized roBa configuration."""

from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from aml_keymap import mouse_positions

ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def main() -> int:
    keymap = read("config/roBa.keymap")
    dtsi = read("boards/shields/roBa/roBa.dtsi")
    right = read("boards/shields/roBa/roBa_R.overlay")
    right_conf = read("boards/shields/roBa/roBa_R.conf")
    west = read("config/west.yml")
    builds = read("build.yaml")
    workflow = read(".github/workflows/build.yml")

    require('display-name = "Mouse Layer-Tap";' in keymap,
            "Mouse Layer-Tap display name is missing")
    require('bindings = <&mo>, <&mkp>;' in keymap, "Mouse Layer-Tap contract missing")

    divider_override = re.search(
        r"&inc_dec_kp\s*\{(?P<body>.*?)\n\s*\};", keymap, re.DOTALL
    )
    require(divider_override is not None, "inc_dec_kp divider override is missing")
    require(
        "bindings = <&encoder_key_divider_cw>, <&encoder_key_divider_ccw>;"
        in divider_override.group("body"),
        "inc_dec_kp no longer routes both directions through the divider",
    )
    for label, direction in (("encoder_key_divider_cw", 1),
                             ("encoder_key_divider_ccw", 2)):
        divider = re.search(
            rf"{label}:\s*{label}\s*\{{(?P<body>.*?)\n\s*\}};", keymap, re.DOTALL
        )
        require(divider is not None, f"{label} behavior is missing")
        for fragment in (
            'compatible = "zmk,behavior-encoder-key-divider";',
            "#binding-cells = <1>;", "bindings = <&kp>;",
            "divisor = <2>;", "timeout-ms = <300>;", f"direction = <{direction}>;",
        ):
            require(fragment in divider.group("body"),
                    f"{label} contract missing: {fragment}")
    require('&zip_temp_layer 1 10000' in keymap and '&zip_temp_layer 1 10000' in right,
            "AML timeout path missing")

    for label in ("scroll_up_down", "scroll_down_up", "scroll_right_left"):
        behavior = re.search(
            rf"{label}:\s*[A-Za-z0-9_]+\s*\{{(?P<body>.*?)\n\s*\}};",
            keymap,
            re.DOTALL,
        )
        require(behavior is not None, f"encoder behavior {label} is missing")
        body = behavior.group("body")
        require('compatible = "zmk,behavior-sensor-rotate";' in body,
                f"encoder behavior {label} is not a sensor-rotate behavior")
        require(len(re.findall(r"&msc\s+[A-Za-z0-9_]+", body)) == 2,
                f"encoder behavior {label} must have two scroll bindings")

    layer_ids = sorted(int(value) for value in re.findall(r"\blayer_(\d+)\s*\{", keymap))
    require(layer_ids == list(range(10)), f"keymap is not exactly ten layers: {layer_ids}")

    layers = {}
    for layer_id in range(10):
        layer = re.search(
            rf"^\s*layer_{layer_id}\s*\{{(?P<body>.*?)^\s*\}};",
            keymap,
            re.MULTILINE | re.DOTALL,
        )
        require(layer is not None, f"missing layer {layer_id}")
        layers[layer_id] = layer.group("body")

    layer_names = []
    layer_bindings = {}
    for layer_id, layer in layers.items():
        display_name = re.search(r'display-name\s*=\s*"([^"]+)";', layer)
        require(display_name is not None, f"layer {layer_id} display name is missing")
        layer_names.append(display_name.group(1))
        bindings = re.search(r"bindings\s*=\s*<(?P<body>.*?)>;", layer, re.DOTALL)
        require(bindings is not None, f"layer {layer_id} bindings are missing")
        layer_bindings[layer_id] = bindings.group("body")
        behaviors = re.findall(r"&([A-Za-z0-9_]+)\b", bindings.group("body"))
        require(len(behaviors) == 43,
                f"layer {layer_id} must retain all 43 roBa input slots: {len(behaviors)}")
    require(all(layer_names), "every layer needs a display name")

    for layer_id in (0, 1):
        sensor_binding = re.search(
            r"sensor-bindings\s*=\s*<(?P<body>.*?)>;", layers[layer_id], re.DOTALL
        )
        require(sensor_binding is not None, f"layer {layer_id} volume encoder is missing")
        volume_binding = re.sub(r"\s+", " ", sensor_binding.group("body").strip())
        require(volume_binding.startswith("&inc_dec_kp ") and len(volume_binding.split()) == 3,
                f"layer {layer_id} lost the editable divided-volume binding: {volume_binding}")

    mouse_behaviors = re.findall(r"&([A-Za-z0-9_]+)\b", layer_bindings[1])
    configured_mouse_positions = [
        position for position, behavior in enumerate(mouse_behaviors)
        if behavior not in {"trans", "none"}
    ]
    require("excluded-positions = <AML_EXCLUDED_POSITIONS>;" in keymap,
            "AML exclusions must be generated from the editable Mouse layer")
    require('#include "aml-exclusions.h"' in dtsi,
            "generated AML header is not included by the shield")
    require(configured_mouse_positions == mouse_positions(keymap, 1, 43),
            "AML generator disagrees with Mouse positions")
    hook = read("modules/modules.cmake")
    for fragment in ("generate-aml-exclusions.py", "--mouse-layer 1 --key-count 43",
                     "CMAKE_CONFIGURE_DEPENDS", "KEYMAP_FILE", "DTS_EXTRA_CPPFLAGS"):
        require(fragment in hook, f"AML generation hook missing: {fragment}")

    layer_access_pattern = re.compile(r"&(?:lt|mo|mouse_lt)\s+(\d+)\b")
    layer_references = {
        layer_id: {int(value) for value in layer_access_pattern.findall(bindings)}
        for layer_id, bindings in layer_bindings.items()
    }
    require(all(target in layers for refs in layer_references.values() for target in refs),
            f"keymap references a missing layer: {layer_references}")
    reachable_layers = {0, 1}
    pending_layers = [0, 1]
    while pending_layers:
        source = pending_layers.pop()
        for target in layer_references[source] - reachable_layers:
            reachable_layers.add(target)
            pending_layers.append(target)
    require(set(range(2, 9)) <= reachable_layers,
            f"customized layers 2 through 8 must remain reachable: {sorted(reachable_layers)}")

    for label, layer_id in (("gesture_processor", 3), ("gesture_2_processor", 4)):
        processor = re.search(
            rf"{label}:\s*{label}\s*\{{(?P<body>.*?)\n\s*\}};", dtsi, re.DOTALL
        )
        require(processor is not None, f"{label} node missing")
        for fragment in (
            f"layer = <{layer_id}>;", f"binding-layer = <{layer_id}>;",
            "up-position = <7>;", "left-position = <18>;",
            "right-position = <20>;", "down-position = <31>;",
            "threshold = <180>;", "cooldown-ms = <150>;", "reset-on-layer = <2>;",
        ):
            require(fragment in processor.group("body"),
                    f"{label} contract missing: {fragment}")

    matrix = re.search(r"kscan0:\s*kscan\s*\{(?P<body>.*?)\n\s*\};", dtsi, re.DOTALL)
    require(matrix is not None and "wakeup-source;" in matrix.group("body"),
            "shared matrix wake source is missing")

    for fragment in (
        "pointer-acceleration;", "pointer-acceleration-base-gain-milli = <625>;",
        "pointer-acceleration-takeoff-speed = <8>;",
        "pointer-acceleration-full-speed = <80>;",
        "pointer-acceleration-max-gain-milli = <3000>;",
        "pointer-acceleration-reference-interval-ms = <8>;",
        "pointer-acceleration-idle-reset-ms = <60>;",
        "pointer-acceleration-scroll-layer = <2>;",
        "pointer-acceleration-gesture-layer = <3>;",
        "pointer-acceleration-gesture-layer-2 = <4>;",
    ):
        require(fragment in right, f"pointer acceleration contract missing: {fragment}")
    require("pointer-acceleration-precision" not in right,
            "500 CPI must be the base curve, not a separate precision stage")

    normalized_listener = re.sub(r"\s+", "", right)
    require(
        "input-processors=<&gesture_2_processor>,<&gesture_processor>,"
        "<&zip_temp_layer110000>;" in normalized_listener,
        "Pointer/Gesture/AML processor order changed",
    )
    require(
        "layers=<2>;input-processors=<&zip_xy_to_scroll_mapper>,"
        "<&zip_scroll_transformINPUT_TRANSFORM_Y_INVERT>,"
        "<&zip_scroll_scaler110>,<&zip_scroll_scaler14>;process-next;"
        in normalized_listener,
        "roBa-preserving Scroll processor order changed",
    )

    require("automouse-layer" not in keymap and "scroll-layers" not in keymap,
            "legacy driver AML/Scroll would conflict with the processor pipeline")
    for fragment in (
        "CONFIG_PMW3610_CPI=800", "CONFIG_PMW3610_CPI_DIVIDOR=1",
        "CONFIG_PMW3610_ORIENTATION_180=y", "CONFIG_PMW3610_POLLING_RATE_125_SW=y",
        "CONFIG_PMW3610_SMART_ALGORITHM=y", "CONFIG_PMW3610_RUN_DOWNSHIFT_TIME_MS=3264",
        "CONFIG_PMW3610_REST1_SAMPLE_TIME_MS=20",
        "CONFIG_PMW3610_POINTER_ACCELERATION=y",
        "CONFIG_ZMK_POINTING_SMOOTH_SCROLLING=y", "CONFIG_INPUT_THREAD_STACK_SIZE=4096",
    ):
        require(fragment in right_conf, f"roBa sensor/runtime contract missing: {fragment}")
    require("CONFIG_PMW3610_FORCE_AWAKE=y" not in right_conf,
            "roBa power behavior unexpectedly enables force-awake")

    require("CONFIG_RGBLED_WIDGET" not in right_conf,
            "original roBa LED behavior must not enable the RGB widget")
    require("rgbled_adapter" not in builds,
            "original roBa normal builds must not enable the RGB adapter")
    require("roba-pairing-reset-use-only-when-needed" in builds,
            "pairing-reset artifact is not clearly marked as recovery-only")

    revisions = re.findall(r"revision:\s*([0-9a-f]{40})", west)
    require(len(revisions) >= 2, "ZMK and PMW3610 dependencies must be pinned")
    require("revision: acfd8e5ea76cf23ad1c9b6b99848f97a95224257" in west,
            "ZMK v0.3 source is not pinned")
    require("revision: 00b389b9093f89f7cec3e025126383877008acd1" in west,
            "PMW3610 acceleration driver is not pinned")
    require("zmk-rgbled-widget" not in west,
            "original roBa dependency set must not include the RGB LED widget")
    require("python3 scripts/verify-built-firmware.py" in workflow,
            "generated firmware contract is not enforced in CI")

    print("verify-roba-config: PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"verify-roba-config: FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
