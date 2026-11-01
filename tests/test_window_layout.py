"""Tests for the shared window sizes. These tests do not open a window.

Run them from the project folder:

    .venv/bin/python -m unittest tests.test_window_layout -v
"""

import unittest

from window_layout import (
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
    apply_layout_scale,
    choose_layout_factor,
    size_that_fits,
)


class WindowLayoutTests(unittest.TestCase):
    def test_mac_size_is_unchanged_when_the_factor_is_one(self):
        self.assertEqual(WINDOW_WIDTH, 720)
        self.assertEqual(WINDOW_HEIGHT, 640)
        self.assertEqual(apply_layout_scale(WINDOW_WIDTH, 1), 720)
        self.assertEqual(apply_layout_scale(WINDOW_HEIGHT, 1), 640)
        self.assertEqual(apply_layout_scale((8, 4), 1), (8, 4))

    def test_windows_150_percent_grows_the_window_and_the_gaps(self):
        # 150% is the common laptop setting. 1.5 times 720 is 1080.
        # 1.5 times a 4 pixel gap is 6, not 5. Halves round away from zero.
        self.assertEqual(apply_layout_scale(WINDOW_WIDTH, 1.5), 1080)
        self.assertEqual(apply_layout_scale(WINDOW_HEIGHT, 1.5), 960)
        self.assertEqual(apply_layout_scale(4, 1.5), 6)
        self.assertEqual(apply_layout_scale((16, 4), 1.5), (24, 6))

    def test_a_tall_scaled_window_is_shortened_to_the_screen(self):
        # 200% of 640 is 1280, which is taller than a 1080 screen
        # once the taskbar margin is reserved.
        width, height = size_that_fits(1440, 1280, 1920, 1080, 48)
        self.assertEqual(width, 1440)
        self.assertEqual(height, 1032)

    def test_a_window_that_already_fits_is_not_shrunk(self):
        self.assertEqual(size_that_fits(720, 640, 1920, 1080, 48), (720, 640))

    def test_the_window_uses_the_larger_of_tk_and_the_display(self):
        # Buttons follow Tk. If Tk stayed at 1 while Windows is at 150%,
        # the window still grows. If Tk already grew, do not grow again.
        self.assertEqual(choose_layout_factor(1.0, 1.5), 1.5)
        self.assertEqual(choose_layout_factor(1.5, 1.5), 1.5)
        self.assertEqual(choose_layout_factor(1.5, 1.25), 1.5)
        self.assertEqual(choose_layout_factor(0.5, 0.5), 1.0)
