# Stanley Health

个人使用的华为运动健康数据接入项目。当前阶段包含一个部署在 `siqiguo.me` 的 OAuth 回调服务，后续将在 Health Service Kit 审批通过后加入授权、令牌交换、数据同步与个人趋势摘要。

## 已配置地址

- OAuth 回调：`https://siqiguo.me/health/oauth/callback`
- 服务状态：`https://siqiguo.me/health/status`
- 隐私说明：`https://siqiguo.me/health/privacy`

## 安全约定

- 华为应用密钥、访问令牌和授权码禁止提交到 Git。
- 所有密钥通过受保护的密钥存储或服务器环境变量注入。
- OAuth 授权必须使用随机 `state`，并在回调时进行恒定时间比较。
- 回调查询串可能包含授权码，Nginx 和应用日志均不得记录完整查询串。
- 仅申请读取个人健康趋势所需的最小权限。

## 服务文件

- `callback.py`：无第三方依赖的回调接收器。
- `huawei-health-callback.service`：systemd 单元。
- `nginx-health.conf`：HTTPS 站点中的 Nginx location 配置片段。

## 当前状态

华为账号服务已开通，Health Service Kit 权限仍在申请中。Health Service Kit 审批通过前不会尝试读取真实健康数据。

