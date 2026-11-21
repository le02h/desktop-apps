# 专注计时器

在 Windows 上设置一次专注计时，支持暂停、继续和重置。退出后清除当前会话。

## 启动

在 Windows Terminal 的 PowerShell 中进入项目根目录。项目使用 uv 和 Python 3.13。

```powershell
uv sync --locked
uv run focusclockqt
```

启动后默认显示 25 分钟。使用 Tab 和 Shift+Tab 切换焦点，空格触发当前按钮，Alt+F4 关闭窗口。

## 开发验证

```powershell
uv run python -m pytest -q
uv run ruff check src tests
```

Windows 人工验收步骤见[启动与验收指南](specs/001-single-focus-timer/quickstart.md)，包含 NVDA 和电源恢复场景。
