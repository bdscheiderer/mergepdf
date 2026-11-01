"""Sizes for the MergePDF window.

The Mac window and the Windows window share these numbers. They are
the comfortable Mac layout: a 720 by 640 window, with room around the
buttons.

Windows above 100% draws fonts and button padding larger. The window
and the gaps have to grow by that same amount, or the buttons sit
crushed inside a window that stayed at the 100% pixel size.
apply_layout_scale() does that multiplication. On a Mac, and on
Windows at 100%, the factor is 1, so these numbers are used as written.

mergepdf.py reads the factor from the screen and calls
apply_layout_scale(). This file does not import Tk.
"""


# The main window. Wide enough for the three instructions to wrap cleanly.
WINDOW_WIDTH = 720
WINDOW_HEIGHT = 640

# Status lines wrap inside the window instead of running off the edge.
MESSAGE_WRAP = 660

# The merge status sits beside the Open button, so it wraps in a narrower column.
MERGE_MESSAGE_WRAP = 330

# Space between the window edge and each step, and between the steps.
WINDOW_EDGE_PAD = 8
STEP_GAP = 4

# Space inside a step, around the instruction, the controls, and the status.
STEP_PAD_X = 16
STEP_PAD_TOP = 10
STEP_PAD_Y = 4
STEP_PAD_BOTTOM = 10

# Gap between Merge, Reset, Help, and Exit.
BUTTON_GAP = 4

# The checklist that opens after a folder is chosen.
DIALOG_LIST_WIDTH = 460
DIALOG_LIST_HEIGHT = 250
DIALOG_INTRO_WRAP = 640
DIALOG_STATUS_WRAP = 160
DIALOG_PAD_X = 20

# Pixels left free so the title bar is not under the screen edge
# and the bottom is not under the taskbar. This is a logical size.
# apply_layout_scale() grows it with the rest of the layout.
SCREEN_MARGIN = 48


def choose_layout_factor(tk_factor, dpi_factor):
    """Pick how much to enlarge the layout on Windows.

    Purpose:
        The buttons follow Tk's scale. The monitor may be set higher
        when Tk did not notice the DPI. The window uses the larger of
        the two so the buttons are not left inside a smaller frame.
        Anything below 1 is treated as 1, which is the Mac size.

    Inputs:
        tk_factor: the scale ttkbootstrap reports for this window.
            Pass 1 when it cannot be read.
        dpi_factor: Windows DPI divided by 96. 1.5 means 150%.
            Pass 1 when the DPI cannot be read.

    Outputs:
        A float of at least 1.

    Side effects:
        None.
    """
    if tk_factor < 1.0:
        tk_factor = 1.0
    if dpi_factor < 1.0:
        dpi_factor = 1.0
    if dpi_factor > tk_factor:
        return dpi_factor
    return tk_factor


def apply_layout_scale(logical_size, factor):
    """Multiply a layout size by the display factor.

    Purpose:
        The constants above are the Mac layout. On Windows the display
        factor is 1 at 100%, 1.5 at 150%, and 2 at 200%. Multiplying
        here keeps the window, the text wrap, and the gaps in step
        with the buttons, which already grow by this factor.

    Inputs:
        logical_size: an int, or a tuple of ints such as (8, 4).
        factor: a number. 1 leaves every value unchanged.

    Outputs:
        An int when logical_size is an int.
        A tuple of ints when logical_size is a tuple.
        Halves round away from zero, so 1.5 times 4 is 6, not 5.

    Side effects:
        None.
    """
    def scale_one(value):
        """Round one layout number to a whole pixel.

        Purpose:
            Tk wants integer pixel counts. A factor such as 1.5 does
            not always land on a whole number.

        Inputs:
            value: one int from logical_size.

        Outputs:
            An int.

        Side effects:
            None.
        """
        scaled = float(value) * float(factor)
        if scaled >= 0:
            return int(scaled + 0.5)
        return int(scaled - 0.5)

    if isinstance(logical_size, tuple):
        scaled_values = []
        for value in logical_size:
            scaled_values.append(scale_one(value))
        return tuple(scaled_values)

    return scale_one(logical_size)


def size_that_fits(width, height, screen_width, screen_height, margin):
    """Shrink a window so the whole title bar stays on the screen.

    Purpose:
        At 200%, the 720 by 640 layout becomes about 1440 by 1280.
        A short laptop screen is smaller than that. The window should
        open fully visible instead of running under the taskbar.

    Inputs:
        width, height: requested size in pixels.
        screen_width, screen_height: the screen, in pixels.
        margin: pixels to leave free. Comes from SCREEN_MARGIN after
            it has been scaled for this display.

    Outputs:
        A tuple (width, height) in pixels. A side that already fits is
        unchanged. A side that does not fit becomes the screen size
        minus the margin. If the screen is smaller than the margin,
        that side is the full screen size.

    Side effects:
        None.
    """
    fitted_width = fit_one_side(width, screen_width, margin)
    fitted_height = fit_one_side(height, screen_height, margin)
    return (fitted_width, fitted_height)


def fit_one_side(requested, screen, margin):
    """Fit one edge of the window onto the screen.

    Purpose:
        size_that_fits() does this once for the width and once for the
        height. The rule is the same for both.

    Inputs:
        requested: the size the layout asked for, in pixels.
        screen: the screen size on that axis, in pixels.
        margin: pixels to leave free on that axis.

    Outputs:
        An int. The requested size when it fits. Otherwise the largest
        size that leaves the margin, or the screen size when the
        margin does not fit on the screen.

    Side effects:
        None.
    """
    if screen <= 0:
        return requested

    room = screen - margin
    if room < 1:
        return screen
    if requested > room:
        return room
    return requested
