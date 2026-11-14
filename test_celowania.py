"""Regresja: bot nie może stać bez strzału obok wąskiego celu."""
import random
import unittest
from types import SimpleNamespace

from defend_the_center import choose_action


class CelowanieTest(unittest.TestCase):
    def action(self, labels):
        game = SimpleNamespace(get_state=lambda: SimpleNamespace(labels=labels))
        return choose_action(game, random.Random(1), False)[0]

    def target(self, x, width):
        return SimpleNamespace(object_name='MarineChainsawVzd', x=x, width=width)

    def test_waski_cel_po_prawej(self):
        self.assertEqual(self.action([self.target(163, 9)]), [0, 1, 0])

    def test_waski_cel_po_lewej(self):
        self.assertEqual(self.action([self.target(149, 9)]), [1, 0, 0])

    def test_cel_na_srodku(self):
        self.assertEqual(self.action([self.target(157, 7)]), [0, 0, 1])

    def test_brak_celu(self):
        self.assertEqual(self.action([]), [0, 1, 0])


if __name__ == '__main__':
    unittest.main()
