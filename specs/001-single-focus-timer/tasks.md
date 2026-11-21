---
description: "单次专注计时器的实施与验收任务"
---

# 任务：单次专注计时器

**依据**：[功能规范](spec.md)、[实现方案](plan.md)、[数据模型](data-model.md)、[桌面交互契约](contracts/desktop.md)、[技术研究](research.md)、[启动与验收](quickstart.md)

`[P]` 表示在前置条件满足时可与同阶段另一项并行。文件路径以仓库根目录为起点。

## 阶段 1：项目准备

- [X] T001 核对 `pyproject.toml`、`.python-version` 和 `uv.lock`，用 `uv sync --locked` 准备 Windows 上的 Python 3.13 环境，保留现有 PySide6、pytest、pytest-qt、Ruff 和 uv_build 配置。

## 阶段 2：共享基础

- [X] T002 [P] 在 `src/pomodoro/timer.py` 定义纯 Python 计时状态和显式时间输入。依照 [data-model.md](data-model.md) 的 `专注设置.整数分钟`、`计时会话.状态`、`计时会话.剩余量` 建立单会话初态与输入校验，核心可在无 Qt 环境中导入。
- [X] T003 [P] 在 `src/pomodoro/windows_power.py` 封装 `QueryUnbiasedInterruptTime` 与 `time.monotonic_ns()`，统一提供整数纳秒读数，并把原生挂起及自动恢复消息转换为可传给核心的事件。

## 阶段 3：US1（P1）设置并完成专注

**独立验收**：启动显示待开始和 25 分钟。设为 1 分钟，用可控时间推进至到期，界面归零并提示一次。另覆盖提前恢复与到点恢复。

### 自动化测试

- [X] T004 [P] [US1] 在 `tests/test_timer.py` 添加 pytest 测试，覆盖默认值、有效端点和无效时长、延迟刷新、自然归零、挂起后提前及到点或超期恢复、重复恢复通知。
- [X] T005 [P] [US1] 在 `tests/test_window.py` 使用 pytest-qt、假时钟和提示音替身验证默认显示、合法与非法提交、倒计时、完成文案及两种完成路径各只触发一次提示音。

### 核心与界面

- [X] T006 [US1] 在 `src/pomodoro/timer.py` 实现待开始时改时长、开始、按实际经过时间结算、挂起和恢复及一次性完成。按 [data-model.md](data-model.md) 实现 `运行区间.清醒时钟截止点`、`运行区间.含挂起时钟截止点`、`挂起快照.剩余量`、`挂起快照.含挂起时钟截止点` 和 `完成事件.单次触发`，重复通知不得再次消费快照。
- [X] T007 [US1] 在 `src/pomodoro/window.py` 使用标准 Qt 控件实现中文时长输入、开始、剩余时间与状态反馈。非法提交阻止开始并反馈。QTimer 只请求刷新，连接 Windows 电源事件并在首次进入已完成时调用一次系统提示音。
- [X] T008 [US1] 在 `src/pomodoro/__init__.py` 的 `main` 创建并显示窗口，在 `pyproject.toml` 将 `focusclockqt` 映射到 `pomodoro:main`；用 `uv run focusclockqt` 确认能进入主窗口。

## 阶段 4：US2（P1）暂停、继续、重置和退出

**独立验收**：开始 2 分钟会话，暂停期间保持剩余量，继续后从原值递减。从运行中、已暂停及已完成重置都能恢复完整设定；关闭重开后恢复默认值。

### 自动化测试

- [X] T009 [P] [US2] 在 `tests/test_timer.py` 覆盖暂停与继续的精确余量、时长锁定、已暂停时挂起和恢复、各状态重置、到期前后操作及重置后旧会话不补发完成事件。
- [X] T010 [P] [US2] 在 `tests/test_window.py` 验证运行与暂停时不能改时长、按钮随状态启用、重置后可修改，以及从运行和暂停关闭后新窗口采用初始设置。

### 核心与界面

- [X] T011 [US2] 在 `src/pomodoro/timer.py` 实现暂停、继续和重置，按 [data-model.md](data-model.md) 的 `计时会话.剩余量` 保存精确暂停余量，继续重建运行区间，重置清除旧区间与快照；暂停前核对是否已到期。
- [X] T012 [US2] 在 `src/pomodoro/window.py` 连接暂停、继续、重置和关闭；按会话状态锁定时长、更新按钮、停止或恢复刷新，关闭后丢弃会话并使旧回调失效。

## 阶段 5：US3（P1）纯键盘与 NVDA

**独立验收**：在 Windows 上仅用键盘完成计时、重置及退出；NVDA 能按需读取关键值和状态，连续 10 秒的时间刷新不触发逐秒播报。

- [X] T013 [US3] 在 `tests/test_window.py` 用 pytest-qt 覆盖 Tab、Shift+Tab、空格操作、启停时的焦点迁移和标准控件的中文可访问名称；同时验证时间刷新不移动焦点。
- [X] T014 [US3] 在 `src/pomodoro/window.py` 按 [桌面交互契约](contracts/desktop.md) 设置控件名称、可见焦点及键盘顺序，保持剩余时间和状态可按需读取，并提供可察觉的状态切换反馈。逐秒刷新不主动发送朗读事件。后台完成的主动播报策略留待确认。
- [ ] T015 [US3] 按 `specs/001-single-focus-timer/quickstart.md` 在 Windows 上用键盘和 NVDA 人工验收完整操作、失焦处理、控件信息、状态变化、静音下的完成状态及无逐秒播报，记录系统和 NVDA 版本与结果。后台主动播报仅记录观察现象，验收标准以澄清后的规范为准。

## 阶段 6：启动说明与整体验证

- [X] T016 [P] 更新 `README.md` 的中文 Windows 启动说明，记录在项目根目录执行 `uv sync --locked`、`uv run focusclockqt`、`uv run pytest -q` 和 `uv run ruff check .`，并链接功能验收指南。
- [ ] T017 [P] 按 `specs/001-single-focus-timer/quickstart.md` 在支持相应电源状态的 Windows 设备上分别验证睡眠和休眠，记录提前与超期恢复、暂停后恢复、恢复通知顺序、完成状态和提示音。逐项记录设备、结果及未验证原因；缺少设备或通知异常时，保留 FR-010 / SC-006 的相关场景为待验证。
- [X] T018 根据 `specs/001-single-focus-timer/quickstart.md` 完成最终启动验证，并执行 `uv run pytest -q` 和 `uv run ruff check .`；记录命令结果及仍待确认或实测的场景。

## 依赖与并行顺序

- `T001 → T002、T003 → US1 → US2 → US3 → 阶段 6`。US2 复用 US1 的计时器和窗口，US3 依赖完整交互。
- US1 的核心测试 T004 与窗口测试 T005 可并行，随后依次实施 T006–T008。
- US2 的核心测试 T009 与窗口测试 T010 可并行，随后依次实施 T011–T012。
- US3 的 T013、T014、T015 顺序执行，先覆盖键盘契约，再实现并人工验收。US3 人工验收与 T017 的电源验收在 T014 后可分别安排。
- T016 与 T017 可并行，T018 汇总结果。

## 实施策略

先以 US1 形成可演示的最小计时流程，再加入 US2 的会话控制和 US3 的无障碍交互。三条故事均为 P1，交付验收覆盖三条故事。可控时钟测试提供计时规则证据，Windows 睡眠、休眠和 NVDA 的实际表现以对应人工验收记录为准。
