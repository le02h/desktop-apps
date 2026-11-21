from enum import Enum

SECOND = 10**9
MINUTE = 60 * SECOND
DEFAULT_MINUTES = 25
MIN_MINUTES = 1
MAX_MINUTES = 180


class State(Enum):
    READY = "待开始"
    RUNNING = "运行中"
    PAUSED = "已暂停"
    COMPLETE = "专注完成"


class FocusTimer:
    def __init__(self):
        self.minutes = DEFAULT_MINUTES
        self.reset()

    def reset(self):
        self.state = State.READY
        self.remaining_ns = self.minutes * MINUTE
        self.suspended = False

    def configure(self, minutes):
        if self.state is not State.READY or type(minutes) is not int:
            return False
        if not MIN_MINUTES <= minutes <= MAX_MINUTES:
            return False
        self.minutes = minutes
        self.reset()
        return True

    def _run(self, awake, elapsed):
        self.state = State.RUNNING
        self.awake_deadline = awake + self.remaining_ns
        self.elapsed_deadline = elapsed + self.remaining_ns

    def start(self, awake, elapsed):
        if self.state is State.READY:
            self._run(awake, elapsed)

    def _complete(self):
        self.state = State.COMPLETE
        self.remaining_ns = 0
        return True

    def refresh(self, awake):
        if self.state is not State.RUNNING or self.suspended:
            return False
        self.remaining_ns = max(0, self.awake_deadline - awake)
        if self.remaining_ns == 0:
            return self._complete()
        return False

    def pause(self, awake):
        if self.state is not State.RUNNING or self.suspended:
            return False
        if self.refresh(awake):
            return True
        self.state = State.PAUSED
        return False

    def continue_session(self, awake, elapsed):
        if self.state is State.PAUSED:
            self._run(awake, elapsed)

    def suspend(self, awake):
        if self.state is not State.RUNNING or self.suspended:
            return False
        if self.refresh(awake):
            return True
        self.suspended = True
        return False

    def resume_system(self, awake, elapsed):
        if not self.suspended:
            return False
        self.suspended = False
        if elapsed >= self.elapsed_deadline:
            return self._complete()
        self._run(awake, elapsed)
        return False
