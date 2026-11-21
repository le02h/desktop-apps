# 技术研究

## 计时与 Windows 电源恢复

- **决策**：通过标准库 `ctypes` 调用 Windows 的 `QueryUnbiasedInterruptTime`，换算为整数纳秒，计算清醒期间经过的时间。用 Windows 上含挂起时间的 `time.monotonic_ns()` 判断恢复时是否已经到点。通过 Qt 原生事件过滤器读取 `WM_POWERBROADCAST` 的 `PBT_APMSUSPEND` 和 `PBT_APMRESUMEAUTOMATIC`。普通刷新保持在 Qt 事件循环中。
- **理由**：正常倒计时排除挂起时间，恢复时的超期判定需要独立的时间基准。两个值分别与各自的截止点比较，避免系统校时改变会话结果。重复恢复通知应忽略。挂起期间暂停刷新和会话操作，恢复后先处理电源状态，再更新界面。
- **备选**：每次回调减一秒会累积延迟。仅用 Python 单调时钟或 Qt 计时器无法同时表达两种时间语义。系统日期时间会受手动校时和时间同步影响。
- **验证**：在目标 Windows 设备上记录时钟读数和消息顺序，覆盖睡眠、休眠、提前恢复、超期恢复、连续两次挂起和暂停期间挂起。单独检查支持 Modern Standby 的设备、锁屏后自动恢复、计时刷新与恢复消息的到达顺序。若挂起或恢复通知缺失，清醒时钟仍可排除系统睡眠时间，但两次时钟读数本身无法确定应在哪一次恢复时触发超期提示。记录复现条件和受影响的 FR-010 / SC-006，现场验证通过后再确认该场景可交付。

参考 [Windows 清醒计数](https://learn.microsoft.com/en-us/windows/win32/api/realtimeapiset/nf-realtimeapiset-queryunbiasedinterrupttime)、[Python 3.13 时钟](https://docs.python.org/3.13/library/time.html#time.monotonic_ns)、[Windows QPC 时钟](https://learn.microsoft.com/en-us/windows/win32/sysinfo/acquiring-high-resolution-time-stamps#resolution-precision-accuracy-and-stability)、[Windows 自动恢复通知](https://learn.microsoft.com/en-us/windows/win32/power/pbt-apmresumeautomatic)、[Qt 原生事件过滤器](https://doc.qt.io/qtforpython-6/PySide6/QtCore/QAbstractNativeEventFilter.html)及 [Qt QTimer](https://doc.qt.io/qtforpython-6/PySide6/QtCore/QTimer.html)。

## 标准控件、朗读与声音

- **决策**：使用 Qt Widgets 标准控件，通过键盘焦点和可访问名称提供按需查询。余量和状态分别呈现。按显示值变化刷新时间，避免显式发送每秒朗读事件。完成音使用 `QApplication.beep()`，仅在首次进入已完成时调用。
- **理由**：标准控件提供既有的键盘和无障碍语义。将视觉刷新、状态反馈和音频触发分开，便于验证重复回调下的行为。
- **备选**：自绘控件需要自己提供键盘和无障碍语义。独立音频资源和播放器增加打包工作。Qt 的无障碍公告 API 可供状态通知验证使用，调用成功不足以证明 NVDA 会朗读。
- **验证**：用 NVDA 实测控件名称、角色、值、禁用状态、焦点迁移和每秒刷新静默。用 Windows 可用音频、静音和从睡眠恢复的场景验证系统提示音。后台是否主动播报仍是产品决定，保留为 [规范](spec.md) 中的待澄清事项。

参考 [Qt QWidget](https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QWidget.html)、[Qt 无障碍公告事件](https://doc.qt.io/qtforpython-6/PySide6/QtGui/QAccessibleAnnouncementEvent.html)及 [Qt QApplication](https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QApplication.html)。

## 项目入口与测试

- **决策**：保留 `src/pomodoro`、uv 构建配置、现有依赖及命令名 `focusclockqt`。实施时将现有项目脚本目标从 `focusclockqt:main` 改为 `pomodoro:main`，并由 `main` 启动 Qt 窗口。
- **理由**：现有入口指向不存在的模块，修改映射即可复用现有包。纯 Python 测试直接传递时钟读数，Qt 测试使用同一假时钟和提示音替身，系统行为用真实 Windows 验证。
- **备选**：创建同名兼容模块会增加转发层。让测试等待真实长会话会减慢反馈，且难以稳定覆盖到期与恢复边界。

参考 [uv 项目命令](https://docs.astral.sh/uv/concepts/projects/run/)。
