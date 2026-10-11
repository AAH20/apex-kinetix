"""
Unit tests for MAP-Elites Quality-Diversity Evolutionary Archive.
Governed by Apex Growth Systems LLC.
"""

import unittest
from apex_kinetix.core.types import BehavioralGenome, PhenotypicDescriptor
from apex_kinetix.evolutionary.map_elites import MAPElitesArchive


class TestMAPElites(unittest.TestCase):
    def setUp(self):
        self.archive = MAPElitesArchive()

    def test_grid_indexing(self):
        desc = PhenotypicDescriptor(
            mean_velocity=600.0,
            curvature_entropy=1.40,
            submovement_ratio=0.20,
            fitts_id_deviation=0.08,
        )
        idx = self.archive.get_grid_index(desc)
        self.assertEqual(len(idx), 4)
        for i in range(4):
            self.assertGreaterEqual(idx[i], 0)
            self.assertLess(idx[i], self.archive.bins[i])

    def test_add_and_elite_replacement(self):
        desc = PhenotypicDescriptor(
            mean_velocity=750.0,
            curvature_entropy=1.60,
            submovement_ratio=0.15,
            fitts_id_deviation=0.04,
        )
        genome1 = BehavioralGenome(fitts_a=0.12)
        genome2 = BehavioralGenome(fitts_a=0.15)

        # First insertion should succeed
        added1 = self.archive.add(genome1, desc, fitness=0.80)
        self.assertTrue(added1)
        self.assertEqual(self.archive.illuminated_count(), 1)

        # Insertion with lower fitness should be rejected
        added_lower = self.archive.add(genome2, desc, fitness=0.70)
        self.assertFalse(added_lower)
        retrieved = self.archive.get_elite(desc)
        self.assertEqual(retrieved.fitts_a, 0.12)

        # Insertion with higher fitness should replace elite
        added_higher = self.archive.add(genome2, desc, fitness=0.92)
        self.assertTrue(added_higher)
        retrieved2 = self.archive.get_elite(desc)
        self.assertEqual(retrieved2.fitts_a, 0.15)

    def test_mutation_bounds(self):
        genome = BehavioralGenome()
        for _ in range(50):
            mutated = MAPElitesArchive.mutate_genome(genome, mutation_rate=0.5)
            self.assertGreaterEqual(mutated.fitts_a, 0.080)
            self.assertLessEqual(mutated.fitts_a, 0.240)
            self.assertGreaterEqual(mutated.tremor_freq, 7.5)
            self.assertLessEqual(mutated.tremor_freq, 12.5)

    def test_crossover(self):
        p1 = BehavioralGenome(fitts_a=0.10, tremor_freq=8.0)
        p2 = BehavioralGenome(fitts_a=0.20, tremor_freq=12.0)
        child = MAPElitesArchive.crossover(p1, p2)
        self.assertIsNotNone(child)
        self.assertEqual(len(child.to_vector()), 12)


if __name__ == "__main__":
    unittest.main()
