# 云函数目录说明

每个子目录对应一个 SCF 函数入口 `main.main_handler`：

- `send_code`
- `verify_login`
- `trigger_sos`
- `heartbeat`
- `check_risk`

公共模块放在 `common/`，部署时会被复制进每个函数包中。

