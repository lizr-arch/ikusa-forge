import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


REPO_ROOT = Path(__file__).resolve().parents[2]
SIM_DIR = REPO_ROOT / "sim-python"
TOOLS_DIR = REPO_ROOT / "tools"
for path in (SIM_DIR, TOOLS_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from export_xlsx_to_json import export_tables  # noqa: E402
from ikusa_sim.config_loader import ConfigLoadError, load_config  # noqa: E402


class ConfigLoaderTests(unittest.TestCase):
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

    def test_load_sample_config_succeeds(self):
        output_dir = self.export_sample_config()

        bundle = load_config(output_dir)

        self.assertIn("ashigaru_spear", bundle.units)
        self.assertIn("fish_scale", bundle.formations)
        self.assertIn("demo_001", bundle.encounters)

    def test_config_bundle_counts_match_sample_data(self):
        output_dir = self.export_sample_config()

        bundle = load_config(output_dir)

        self.assertEqual(12, len(bundle.units))
        self.assertEqual(5, len(bundle.weapons))
        self.assertEqual(10, len(bundle.skills))
        self.assertEqual(3, len(bundle.formations))
        self.assertEqual(6, len(bundle.synergies))
        self.assertEqual(1, len(bundle.encounters))

    def test_constants_match_sample_data(self):
        output_dir = self.export_sample_config()

        constants = load_config(output_dir).constants

        self.assertEqual(20, constants.tick_rate)
        self.assertEqual(1200, constants.max_ticks)
        self.assertEqual(3, constants.board_rows)
        self.assertEqual(4, constants.board_cols)
        self.assertEqual(1001, constants.default_seed)

    def test_invalid_generated_config_fails_before_load(self):
        output_dir = self.export_sample_config()
        constants = self.load_table(output_dir, "constants")
        del constants["tick_rate"]
        self.write_table(output_dir, "constants", constants)

        with self.assertRaises(ConfigLoadError) as context:
            load_config(output_dir)

        self.assertIn("Invalid generated config", str(context.exception))
        self.assertIn("missing required key 'tick_rate'", str(context.exception))


if __name__ == "__main__":
    unittest.main()
