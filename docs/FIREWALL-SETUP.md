# Windows 11 防火墙设置指南

## 方法一：使用 PowerShell（推荐）

以管理员身份打开 PowerShell 或终端，运行以下命令：

```powershell
# 允许后端端口 8765（TCP）
New-NetFirewallRule -DisplayName "YinYi Backend" -Direction Inbound -Protocol TCP -LocalPort 8765 -Action Allow

# 允许前端端口 3000（TCP）
New-NetFirewallRule -DisplayName "YinYi Frontend" -Direction Inbound -Protocol TCP -LocalPort 3000 -Action Allow

# 验证规则是否创建成功
Get-NetFirewallRule -DisplayName "YinYi*" | Format-Table DisplayName, Enabled, Direction, Action
```

## 方法二：使用图形界面（Windows 安全中心）

1. **打开 Windows 安全中心**
   - 按 `Win + I` 打开设置
   - 点击"隐私和安全性" → "Windows 安全中心"

2. **打开防火墙设置**
   - 点击"防火墙和网络保护"
   - 点击"高级设置"（需要管理员权限）

3. **创建入站规则**
   - 在左侧点击"入站规则"
   - 右侧点击"新建规则..."

4. **配置规则（以 3000 端口为例）**
   - 规则类型：选择"端口" → 点击"下一步"
   - 协议和端口：选择"TCP"，特定本地端口输入 `3000` → 点击"下一步"
   - 操作：选择"允许连接" → 点击"下一步"
   - 配置文件：勾选"域"、"专用"、"公用" → 点击"下一步"
   - 名称：输入 `YinYi Frontend` → 点击"完成"

5. **重复上述步骤创建 8765 端口的规则**
   - 名称：`YinYi Backend`
   - 端口：`8765`

## 方法三：使用 netsh 命令

以管理员身份打开 CMD 或 PowerShell：

```cmd
:: 允许 3000 端口
netsh advfirewall firewall add rule name="YinYi Frontend" dir=in action=allow protocol=TCP localport=3000

:: 允许 8765 端口
netsh advfirewall firewall add rule name="YinYi Backend" dir=in action=allow protocol=TCP localport=8765

:: 查看规则
netsh advfirewall firewall show rule name="YinYi*"
```

## 验证端口是否开放

在另一台电脑上测试连接：

```cmd
:: 测试前端端口
telnet 192.168.x.x 3000

:: 测试后端端口
telnet 192.168.x.x 8765
```

或者使用浏览器访问：
- `http://192.168.x.x:3000`（前端）
- `http://192.168.x.x:8765/docs`（API 文档）

## 网络类型注意事项

确保你的网络设置为"专用网络"以获得最佳访问：

1. 打开"设置" → "网络和 Internet" → "WLAN" 或 "以太网"
2. 点击当前连接的网络
3. 将"网络配置文件类型"改为"专用网络"

## 删除规则（如需撤销）

```powershell
# 使用 PowerShell
Remove-NetFirewallRule -DisplayName "YinYi Backend"
Remove-NetFirewallRule -DisplayName "YinYi Frontend"

:: 或使用 netsh
netsh advfirewall firewall delete rule name="YinYi Backend"
netsh advfirewall firewall delete rule name="YinYi Frontend"
```

## 常见问题

**Q: 设置了防火墙但还是无法访问？**
- 检查印忆服务是否已启动
- 确认使用的是正确的 IP 地址
- 检查路由器是否开启了 AP 隔离
- 尝试临时关闭 Windows Defender 防火墙测试

**Q: 如何查看本机 IP？**
```cmd
ipconfig
```
查找"IPv4 地址"，通常是 `192.168.x.x` 或 `10.x.x.x`

**Q: 公共场所网络无法访问？**
- 公共场所网络可能有 AP 隔离，无法访问其他设备
- 建议使用手机热点或家用 WiFi
