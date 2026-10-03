#!/usr/bin/env python3
"""Regression tests for Keymap Editor-owned binding values."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import re
import shutil
import tempfile

ROOT = Path(__file__).resolve().parents[1]
VERIFIER = ROOT / "scripts" / "verify-roba-config.py"


def load_verifier():
    spec = spec_from_file_location("verify_roba_config", VERIFIER)
    if spec is None or spec.loader is None:
        raise AssertionError("could not load verifier")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def remove_safe_access(text: str, target: int) -> str:
    patterns = (
        rf"&lt\s+{target}\s+[^\s>]+",
        rf"&mouse_lt\s+{target}\s+[^\s>]+",
        rf"&mo\s+{target}\b",
    )
    replacements = 0
    for pattern in patterns:
        text, count = re.subn(pattern, "&kp F15", text)
        replacements += count
    if replacements == 0:
        raise AssertionError(f"test fixture has no safe access to layer {target}")
    return text


def main() -> None:
    verifier = load_verifier()
    verifier.main()

    with tempfile.TemporaryDirectory(prefix="roba-keymap-editor-") as temp_dir:
        test_root = Path(temp_dir) / "repo"
        shutil.copytree(ROOT, test_root, ignore=shutil.ignore_patterns(".git", "gesture_state_test"))
        keymap_path = test_root / "config" / "roBa.keymap"
        keymap = keymap_path.read_text(encoding="utf-8")

        keymap = re.sub(r"(&lt\s+\d+\s+)[^\s>]+", r"\g<1>F13", keymap)
        keymap_path.write_text(keymap, encoding="utf-8")
        verifier.ROOT = test_root
        verifier.main()

        # Keymap Editor owns encoder directions and gesture action bindings.
        edited, volume_count = re.subn(
            r"sensor-bindings\s*=\s*<&inc_dec_kp\s+[^>]+>;",
            "sensor-bindings = <&inc_dec_kp C_VOLUME_UP C_VOLUME_DOWN>;",
            keymap,
        )
        edited, scroll_count = re.subn(
            r"sensor-bindings\s*=\s*<&scroll_(?:up_down|down_up)>;",
            "sensor-bindings = <&scroll_down_up>;",
            edited,
        )
        if volume_count != 2 or scroll_count != 2:
            raise AssertionError("Editor encoder fixture no longer covers both edited layers")
        if 'display-name = "Base";' not in edited or '&kp LG(T)' not in edited:
            raise AssertionError("Editor display/Gesture fixture no longer matches the keymap")
        edited = edited.replace('display-name = "Base";', 'display-name = "Custom Base";')
        edited = edited.replace('&kp LG(T)', '&none', 1)
        keymap_path.write_text(edited, encoding="utf-8")
        verifier.main()

        keymap_path.write_text(keymap, encoding="utf-8")

        keymap = remove_safe_access(keymap, 5)
        keymap_path.write_text(keymap, encoding="utf-8")
        try:
            verifier.main()
        except AssertionError as exc:
            if "must remain reachable" not in str(exc):
                raise
        else:
            raise AssertionError("unreachable customized layer was not rejected")

        keymap = keymap.replace("&kp F15", "&to 5", 1)
        keymap_path.write_text(keymap, encoding="utf-8")
        try:
            verifier.main()
        except AssertionError as exc:
            if "must remain reachable" not in str(exc):
                raise
        else:
            raise AssertionError("fixed layer transition was accepted as safe reachability")

    print("keymap-editor-contract-test: PASS")


if __name__ == "__main__":
    main()
