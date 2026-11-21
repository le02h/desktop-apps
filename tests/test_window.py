import pytest
from PySide6.QtCore import Qt

from pomodoro.window import FocusWindow

SECOND = 10**9


@pytest.fixture
def desktop(qtbot):
    times = [0, 0]
    sounds = []
    window = FocusWindow(lambda: tuple(times), lambda: sounds.append(True))
    qtbot.addWidget(window)
    window.show()
    return window, times, sounds


@pytest.mark.parametrize("resume", [False, True])
def test_completion_once(desktop, qtbot, resume):
    window, times, sounds = desktop
    assert window.remaining.text() == "25:00"
    window.duration.setValue(1)
    qtbot.mouseClick(window.start_button, Qt.MouseButton.LeftButton)
    if resume:
        window.handle_power(True)
        times[1] = 60 * SECOND
        window.handle_power(False)
        window.handle_power(False)
    else:
        times[:] = [60 * SECOND, 60 * SECOND]
    window.refresh()
    window.refresh()
    assert window.remaining.text() == "00:00"
    assert window.status.text() == "专注完成"
    assert sounds == [True]


def test_keyboard_session(desktop, qtbot):
    window, times, _ = desktop
    window.activateWindow()
    window.duration.setFocus()
    qtbot.keyClick(window.duration, Qt.Key.Key_Tab)
    assert window.remaining.hasFocus()
    qtbot.keyClick(window.remaining, Qt.Key.Key_Tab, Qt.KeyboardModifier.ShiftModifier)
    assert window.duration.hasFocus()
    qtbot.keyClick(window.duration, Qt.Key.Key_Tab)
    qtbot.keyClick(window.remaining, Qt.Key.Key_Tab)
    qtbot.keyClick(window.status, Qt.Key.Key_Tab)
    assert window.start_button.hasFocus()
    qtbot.keyClick(window.start_button, Qt.Key.Key_Space)
    assert window.pause_button.hasFocus()
    assert not window.duration.isEnabled()
    times[:] = [10 * SECOND, 10 * SECOND]
    qtbot.keyClick(window.pause_button, Qt.Key.Key_Space)
    assert window.continue_button.hasFocus()
    assert window.remaining.text() == "24:50"
    assert not window.duration.isEnabled()
    times[:] = [20 * SECOND, 20 * SECOND]
    window.refresh()
    assert window.remaining.text() == "24:50"
    assert window.continue_button.hasFocus()
    qtbot.keyClick(window.continue_button, Qt.Key.Key_Space)
    qtbot.keyClick(window.reset_button, Qt.Key.Key_Space)
    assert window.duration.isEnabled()
    assert window.remaining.text() == "25:00"
    assert window.remaining.accessibleName() == "剩余时间"
    assert window.status.accessibleName() == "当前状态"


@pytest.mark.parametrize("leave_field_first", [False, True])
def test_invalid_duration_does_not_start(desktop, qtbot, leave_field_first):
    window, _, sounds = desktop
    editor = window.duration.lineEdit()
    editor.setFocus()
    editor.selectAll()
    qtbot.keyClicks(editor, "2")
    assert window.remaining.text() == "02:00"
    editor.selectAll()
    qtbot.keyClick(editor, Qt.Key.Key_Backspace)
    if leave_field_first:
        qtbot.keyClick(editor, Qt.Key.Key_Tab)
    qtbot.mouseClick(window.start_button, Qt.MouseButton.LeftButton)
    assert window.status.text() == "待开始"
    assert window.remaining.text() == "02:00"
    assert window.feedback.text()
    assert not sounds


@pytest.mark.parametrize("paused", [False, True])
def test_closing_discards_session(qtbot, desktop, paused):
    window, times, sounds = desktop
    window.duration.setValue(2)
    window.start_button.click()
    if paused:
        window.pause_button.click()
    window.close()
    times[:] = [120 * SECOND, 120 * SECOND]
    window.refresh()
    new_window = FocusWindow(lambda: tuple(times), lambda: sounds.append(True))
    qtbot.addWidget(new_window)
    assert new_window.duration.value() == 25
    assert new_window.status.text() == "待开始"
    assert not window.ticker.isActive()
    assert not sounds
