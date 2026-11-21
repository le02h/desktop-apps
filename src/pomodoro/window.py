from itertools import pairwise

from PySide6.QtCore import QSignalBlocker, Qt, QTimer
from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from .timer import MAX_MINUTES, MIN_MINUTES, SECOND, FocusTimer, State


class DurationInput(QSpinBox):
    def focusOutEvent(self, event):
        # Keep rejected input visible so leaving the field cannot silently commit it.
        if self.hasAcceptableInput():
            super().focusOutEvent(event)
            return
        text = self.lineEdit().text()
        with QSignalBlocker(self):
            super().focusOutEvent(event)
            self.lineEdit().setText(text)
        self.editingFinished.emit()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and not self.hasAcceptableInput():
            self.editingFinished.emit()
            event.accept()
            return
        super().keyPressEvent(event)


class FocusWindow(QWidget):
    def __init__(self, clock, beep):
        super().__init__()
        self.clock = clock
        self.beep = beep
        self.session = FocusTimer()
        self.setWindowTitle("专注计时器")
        self.duration = DurationInput()
        self.duration.setRange(MIN_MINUTES, MAX_MINUTES)
        self.duration.setKeyboardTracking(False)
        self.duration.setValue(self.session.minutes)
        self.duration.setAccessibleName("专注时长（分钟）")
        self.remaining = QLineEdit()
        self.status = QLineEdit()
        for field, name in ((self.remaining, "剩余时间"), (self.status, "当前状态")):
            field.setReadOnly(True)
            field.setAccessibleName(name)
        self.feedback = QLabel()
        self.feedback.setWordWrap(True)
        self.start_button = QPushButton("开始")
        self.pause_button = QPushButton("暂停")
        self.continue_button = QPushButton("继续")
        self.reset_button = QPushButton("重置")
        buttons = (
            self.start_button,
            self.pause_button,
            self.continue_button,
            self.reset_button,
        )
        form = QFormLayout()
        form.addRow("专注时长（分钟）", self.duration)
        form.addRow("剩余时间", self.remaining)
        form.addRow("当前状态", self.status)
        actions = QHBoxLayout()
        for button in buttons:
            actions.addWidget(button)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addLayout(actions)
        layout.addWidget(self.feedback)
        tab_order = (self.duration, self.remaining, self.status, *buttons)
        for current, following in pairwise(tab_order):
            QWidget.setTabOrder(current, following)

        self.ticker = QTimer(self)
        self.ticker.setInterval(200)
        self.ticker.timeout.connect(self.refresh)
        self.duration.lineEdit().textEdited.connect(self._commit_duration)
        self.duration.valueChanged.connect(self._commit_duration)
        self.duration.editingFinished.connect(self._commit_duration)
        self.start_button.clicked.connect(self._start)
        self.pause_button.clicked.connect(self._pause)
        self.continue_button.clicked.connect(self._continue)
        self.reset_button.clicked.connect(self._reset)
        self._render()

    def _commit_duration(self):
        if self.session.state is not State.READY:
            return False
        if not self.duration.hasAcceptableInput():
            message = "请输入 1 至 180 分钟的整数。"
            self.feedback.setText(message)
            self.duration.setAccessibleDescription(message)
            return False
        minutes = int(self.duration.cleanText())
        self.session.configure(minutes)
        self.feedback.clear()
        self.duration.setAccessibleDescription("")
        self._render()
        return True

    def _start(self):
        if self._commit_duration():
            self.session.start(*self.clock())
            self._render()

    def _pause(self):
        self._render(self.session.pause(self.clock()[0]))

    def _continue(self):
        self.session.continue_session(*self.clock())
        self._render()

    def _reset(self):
        self.session.reset()
        # setValue may be a no-op when the value matches a rejected edit.
        self.duration.setValue(self.session.minutes)
        self.duration.lineEdit().setText(self.duration.textFromValue(self.session.minutes))
        self._commit_duration()

    def refresh(self):
        self._render(self.session.refresh(self.clock()[0]))

    def handle_power(self, suspended):
        awake, elapsed = self.clock()
        if suspended:
            completed = self.session.suspend(awake)
        else:
            completed = self.session.resume_system(awake, elapsed)
        self._render(completed)

    def _render(self, completed=False):
        state = self.session.state
        seconds = (self.session.remaining_ns + SECOND - 1) // SECOND
        minutes, seconds = divmod(seconds, 60)
        display = f"{minutes:02d}:{seconds:02d}"
        if self.remaining.text() != display:
            self.remaining.setText(display)
        if self.status.text() != state.value:
            self.status.setText(state.value)

        running = state is State.RUNNING and not self.session.suspended
        paused = state is State.PAUSED
        ready = state is State.READY
        focus = self.focusWidget()
        enabled = {
            self.duration: ready,
            self.start_button: ready,
            self.pause_button: running,
            self.continue_button: paused,
        }
        if focus in enabled and not enabled[focus]:
            target = self.pause_button if running else self.continue_button if paused else self.status
            target.setEnabled(True)
            target.setFocus()
        for widget, available in enabled.items():
            widget.setEnabled(available)

        if running and not self.ticker.isActive():
            self.ticker.start()
        elif not running:
            self.ticker.stop()
        if completed:
            self.beep()

    def closeEvent(self, event):
        self.ticker.stop()
        self.session = FocusTimer()
        self._reset()
        super().closeEvent(event)
