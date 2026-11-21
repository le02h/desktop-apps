def main() -> int:
    from PySide6.QtWidgets import QApplication

    from .window import FocusWindow
    from .windows_power import PowerEvents, WindowsClock

    app = QApplication([])
    window = FocusWindow(WindowsClock(), QApplication.beep)
    power = PowerEvents(int(window.winId()), window.handle_power)
    app.installNativeEventFilter(power)
    window.show()
    try:
        return app.exec()
    finally:
        app.removeNativeEventFilter(power)
