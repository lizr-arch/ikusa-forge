import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS_DIR = REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from export_xlsx_to_json import export_tables  # noqa: E402
from validate_config import validate_config  # noqa: E402


class ConfigValidationTests(unittest.TestCase):
    def export_sample_config(self):
        temp_dir = TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)

        output_dir = Path(temp_dir.name) / "generated"
        export_tables(REPO_ROOT / "config" / "source", output_dir)
        return output_dir

    def load_table(self, output_dir, table):
        path = output_dir / "{}.json".format(table)
        return json.loads(path.read_text(encoding="utf-8"))

    def write_table(self, output_dir, table, data):
        path = output_dir / "{}.json".format(table)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def assert_has_error(self, errors, expected_text):
        self.assertTrue(
            any(expected_text in error for error in errors),
            "expected {!r} in errors: {}".format(expected_text, errors),
        )

    def test_valid_sample_config_passes(self):
        output_dir = self.export_sample_config()

        errors = validate_config(output_dir)

        self.assertEqual([], errors)

    def test_valid_constants_object_passes(self):
        output_dir = self.export_sample_config()
        constants = self.load_table(output_dir, "constants")

        errors = validate_config(output_dir)

        self.assertEqual([], errors)
        self.assertEqual(
            {
                "tick_rate": 20,
                "max_ticks": 1200,
                "board_rows": 3,
                "board_cols": 4,
                "default_seed": 1001,
            },
            constants,
        )

    def test_invalid_missing_reference_fails(self):
        output_dir = self.export_sample_config()
        units = self.load_table(output_dir, "units")
        units[0]["skill_ids"].append("missing_skill")
        self.write_table(output_dir, "units", units)

        errors = validate_config(output_dir)

        self.assert_has_error(errors, "unknown skill 'missing_skill'")

    def test_invalid_duplicate_id_fails(self):
        output_dir = self.export_sample_config()
        units = self.load_table(output_dir, "units")
        duplicate = dict(units[0])
        units.append(duplicate)
        self.write_table(output_dir, "units", units)

        errors = validate_config(output_dir)

        self.assert_has_error(errors, "duplicate id '{}'".format(units[0]["id"]))

    def test_invalid_negative_number_fails(self):
        output_dir = self.export_sample_config()
        units = self.load_table(output_dir, "units")
        units[0]["hp"] = -1
        self.write_table(output_dir, "units", units)

        errors = validate_config(output_dir)

        self.assert_has_error(errors, "field 'hp' must not be negative")

    def test_missing_tick_rate_fails(self):
        output_dir = self.export_sample_config()
        constants = self.load_table(output_dir, "constants")
        del constants["tick_rate"]
        self.write_table(output_dir, "constants", constants)

        errors = validate_config(output_dir)

        self.assert_has_error(errors, "missing required key 'tick_rate'")

    def test_missing_max_ticks_fails(self):
        output_dir = self.export_sample_config()
        constants = self.load_table(output_dir, "constants")
        del constants["max_ticks"]
        self.write_table(output_dir, "constants", constants)

        errors = validate_config(output_dir)

        self.assert_has_error(errors, "missing required key 'max_ticks'")

    def test_negative_max_ticks_fails(self):
        output_dir = self.export_sample_config()
        constants = self.load_table(output_dir, "constants")
        constants["max_ticks"] = -1
        self.write_table(output_dir, "constants", constants)

        errors = validate_config(output_dir)

        self.assert_has_error(errors, "constants.max_ticks: value must not be negative")

    def test_encounter_coordinate_outside_formation_slots_fails(self):
        output_dir = self.export_sample_config()
        encounters = self.load_table(output_dir, "encounters")
        encounters[0]["player_units"][0]["x"] = 0
        encounters[0]["player_units"][0]["y"] = 1
        self.write_table(output_dir, "encounters", encounters)

        errors = validate_config(output_dir)

        self.assert_has_error(errors, "player coordinate (0, 1) is not in formation slots")


if __name__ == "__main__":
    unittest.main()
