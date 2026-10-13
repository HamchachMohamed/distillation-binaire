"""Tests numériques essentiels du solveur."""
import unittest

from config import ATM_PA
from equilibrium import azeotrope, calculate_equilibrium_curve, equilibrium_at_liquid_composition
from material_balance import column_balance, feed_balance
from mccabe_thiele import step_off_stages
from main import determine_feed_thermal_state


class TestCore(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.curve = calculate_equilibrium_curve(ATM_PA, 121)

    def test_feed_balance(self):
        result = feed_balance(30.0, 0.40)
        self.assertAlmostEqual(result.water_mass_kg_h, 18.0)
        self.assertAlmostEqual(result.ethanol_mass_kg_h, 12.0)
        self.assertAlmostEqual(result.total_kmol_h, result.water_kmol_h + result.ethanol_kmol_h)
        self.assertTrue(0 < result.ethanol_mole_fraction < 1)

    def test_pure_component_endpoints(self):
        self.assertAlmostEqual(self.curve.y_ethanol[0], 0.0)
        self.assertAlmostEqual(self.curve.y_ethanol[-1], 1.0)
        self.assertAlmostEqual(self.curve.temperature_C[0], 100.0, delta=0.25)
        self.assertAlmostEqual(self.curve.temperature_C[-1], 78.3, delta=0.25)

    def test_azeotrope(self):
        az = azeotrope(self.curve)
        self.assertIsNotNone(az)
        x, T = az
        self.assertAlmostEqual(x, 0.8934, delta=0.01)
        self.assertAlmostEqual(T, 351.29, delta=0.25)

    def test_feed_vapor_richer(self):
        _, y = equilibrium_at_liquid_composition(0.206, ATM_PA)
        self.assertGreater(y, 0.206)

    def test_column_closure(self):
        feed = feed_balance(30.0, 0.40)
        result = column_balance(feed.total_kmol_h, feed.ethanol_mole_fraction, 0.85, 0.05)
        self.assertAlmostEqual(result.total_residual_kmol_h, 0.0, places=12)
        self.assertAlmostEqual(result.ethanol_residual_kmol_h, 0.0, places=12)
        self.assertAlmostEqual(result.total_mass_residual_kg_h, 0.0, places=12)

    def test_mccabe_thiele_example(self):
        result = step_off_stages(self.curve, 0.85, 0.05, 4.0, 1.0, 0.20679185)
        self.assertGreater(result.stages_including_reboiler, 1)
        self.assertLess(result.stages_including_reboiler, 100)

    def test_feed_temperature_is_classified_without_changing_elv(self):
        cold = determine_feed_thermal_state(25.0, 0.206, self.curve)
        saturated = determine_feed_thermal_state(cold.bubble_temperature_K - 273.15, 0.206, self.curve)
        self.assertIn("sous-refroidi", cold.label)
        self.assertIn("liquide saturé", saturated.label)


if __name__ == "__main__":
    unittest.main()
