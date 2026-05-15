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
from ikusa_sim.config_loader import load_config  # noqa: E402
from ikusa_sim.formation import FormationLookupError, get_slot_role  # noqa: E402


class FormationLookupTests(unittest.TestCase):
    def export_sample_config(self):
        temp_dir = TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)

        output_dir = Path(temp_dir.name) / "generated"
        export_tables(REPO_ROOT / "config" / "source", output_dir)
        return output_dir

    def load_sample_bundle(self):
        return load_config(self.export_sample_config())

    def test_fish_scale_front_slot_returns_vanguard(self):
        bundle = self.load_sample_bundle()
        formation = bundle.formations["fish_scale"]

        role = get_slot_role(formation, 1, 0)

        self.assertEqual("vanguard", role)

    def test_fish_scale_missing_coordinate_fails(self):
        bundle = self.load_sample_bundle()
        formation = bundle.formations["fish_scale"]

        with self.assertRaises(FormationLookupError):
            get_slot_role(formation, 0, 1)

    def test_demo_player_units_all_map_to_player_formation_roles(self):
        bundle = self.load_sample_bundle()
        encounter = bundle.encounters["demo_001"]
        formation = bundle.formations[encounter.player_formation]

        roles = [get_slot_role(formation, unit.x, unit.y) for unit in encounter.player_units]

        self.assertEqual(
            ["vanguard", "vanguard", "center", "center", "support", "support"],
            roles,
        )

    def test_demo_enemy_units_all_map_to_enemy_formation_roles(self):
        bundle = self.load_sample_bundle()
        encounter = bundle.encounters["demo_001"]
        formation = bundle.formations[encounter.enemy_formation]

        roles = [get_slot_role(formation, unit.x, unit.y) for unit in encounter.enemy_units]

        self.assertEqual(
            ["left_flank", "right_flank", "center", "center", "left_support", "right_support"],
            roles,
        )


if __name__ == "__main__":
    unittest.main()
