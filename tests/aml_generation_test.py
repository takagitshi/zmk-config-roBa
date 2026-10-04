#!/usr/bin/env python3
"""Regress AML generation against real Editor edits and independent DTS arrays."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/generate-aml-exclusions.py'
_spec = spec_from_file_location('aml_generator', ROOT / 'scripts/aml_keymap.py')
generator = module_from_spec(_spec)
_spec.loader.exec_module(generator)


def edit_mouse(keymap, position, binding):
    body = generator.layer_body(keymap, 'layer_1')
    entries = generator.bindings(body)
    entries[position] = binding
    new_body = re.sub(r'(?<!sensor-)\bbindings\s*=\s*<.*?>;',
                      'bindings = <' + ' '.join(entries) + '>;', body, flags=re.DOTALL)
    return keymap.replace(body, new_body)


class AmlGenerationTest(unittest.TestCase):
    def setUp(self):
        self.keymap = (ROOT / 'config/roBa.keymap').read_text()
        # Keep fixtures independent of future Editor-owned bindings.
        body = generator.layer_body(self.keymap, 'layer_1')
        entries = ['&trans'] * 43
        for position in (18, 19, 20, 21, 22, 35, 36):
            entries[position] = '&kp F13'
        body_fixture = re.sub(r'(?<!sensor-)\bbindings\s*=\s*<.*?>;',
                              'bindings = <' + ' '.join(entries) + '>;', body, flags=re.DOTALL)
        self.keymap = self.keymap.replace(body, body_fixture)
        self.positions = generator.mouse_positions(self.keymap, 1, 43)

    def test_actual_mouse_bindings(self):
        self.assertEqual(self.positions, [18, 19, 20, 21, 22, 35, 36])

    def test_editor_add_and_remove(self):
        edited = edit_mouse(self.keymap, 0, '&kp F13')
        edited = edit_mouse(edited, 18, '&trans')
        self.assertEqual(generator.mouse_positions(edited, 1, 43),
                         [0] + [value for value in self.positions if value != 18])
        self.assertIn('excluded-positions = <AML_EXCLUDED_POSITIONS>;', edited)

    def test_none_is_not_excluded(self):
        edited = edit_mouse(self.keymap, 18, '&none')
        self.assertNotIn(18, generator.mouse_positions(edited, 1, 43))

    def test_comments_and_sensor_do_not_add_positions(self):
        edited = self.keymap.replace('display-name = "Mouse";',
                                   'display-name = "Mouse"; /* &kp F13 */\n // &mkp MB1\n')
        self.assertEqual(generator.mouse_positions(edited, 1, 43), self.positions)

    def test_empty_mouse_keeps_aml_cancellation(self):
        edited = self.keymap
        for position in self.positions:
            edited = edit_mouse(edited, position, '&trans')
        self.assertEqual(generator.mouse_positions(edited, 1, 43), [])
        self.assertIn('#define AML_EXCLUDED_POSITIONS 65535\n', generator.aml_header(edited, 1, 43))

    def test_wrong_slot_count_fails(self):
        with self.assertRaisesRegex(AssertionError, '43'):
            body = generator.layer_body(self.keymap, 'layer_1')
            generator.mouse_positions(self.keymap.replace(body, body.replace('&trans', '', 1)), 1, 43)

    def test_cli_idempotence_and_no_source_write(self):
        with tempfile.TemporaryDirectory() as temp:
            keymap = Path(temp) / 'edited.keymap'
            output = Path(temp) / 'generated/aml-exclusions.h'
            keymap.write_text(self.keymap)
            command = [sys.executable, str(SCRIPT), str(keymap), str(output),
                       '--mouse-layer', '1', '--key-count', '43']
            subprocess.run(command, check=True)
            timestamp = output.stat().st_mtime_ns
            subprocess.run(command, check=True)
            self.assertEqual(output.stat().st_mtime_ns, timestamp)
            self.assertEqual(keymap.read_text(), self.keymap)
            keymap.write_text(edit_mouse(self.keymap, 0, '&mkp MB4'))
            subprocess.run(command, check=True)
            self.assertIn('#define AML_EXCLUDED_POSITIONS 0 ', output.read_text())


if __name__ == '__main__':
    unittest.main()
