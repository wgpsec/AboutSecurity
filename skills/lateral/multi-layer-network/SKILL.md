---
name: multi-layer-network
description: "多层网络渗透与隧道搭建。当需要从 DMZ 跳转到内网、跨网段渗透、或目标在多层防火墙/网络分区后面时使用。覆盖代理搭建(frp/chisel/SSH)、多跳隧道链、端口转发、SOCKS 代理。从边界突破到域控的完整多层攻击路径"
metadata:
  tags: "pivot,proxy,tunnel,multi-layer,lateral,隧道,代理,端口转发,frp,chisel,ssh,socks,内网穿透,跳板,DMZ"
  difficulty: "hard"
  icon: "🌐"
  category: "横向移动"
---

# 多层网络渗透方法论

## ⛔ 深入参考（必读）

- ⛔**必读** 需要 frp/chisel/Neo-reGeorg/SSH 隧道配置命令、多跳代理链、proxychains 用法 → `read_skill(id="multi-layer-network", path="references/tunnel-tools.md")`

---

## Phase 1: 边界突破与立足点

获取 DMZ 主机 Shell 后，立即收集网络信息：
```bash
ip addr && ip route && arp -a && cat /etc/hosts      # Linux
ipconfig /all && route print && arp -a                 # Windows
```

**关键判断**：
- 双网卡（eth0=外网, eth1=10.x.x.x）→ 天然跳板
- 只有内网 IP → 需要搭建反向隧道

### 目标网络测绘
```bash
for i in $(seq 1 254); do ping -c 1 -W 1 10.0.0.$i &>/dev/null && echo "10.0.0.$i alive"; done
fscan -h 10.0.0.0/24 -nopoc
```

## Phase 2: 隧道选择决策树

```
目标出网情况？
├─ 可出网（有外网访问）
│   ├─ 有 SSH 凭据？→ SSH -D 1080（零部署，最简单）
│   ├─ 需要长期稳定？→ frp（断线重连）
│   └─ 快速部署？→ chisel（单二进制）
├─ 仅 HTTP 出网 → Neo-reGeorg HTTP 隧道
└─ 完全不出网 → SSH 反向隧道 / 在跳板上中转
```

所有工具的详细配置命令见 → `read_skill(id="multi-layer-network", path="references/tunnel-tools.md")`

## 隧道工具选择速查

| 场景 | 推荐工具 | 原因 |
|------|----------|------|
| 有 SSH 凭据 | SSH 隧道 | 零部署，最简单 |
| 目标出网 + 长期使用 | frp | 最稳定，支持断线重连 |
| 目标出网 + 快速部署 | chisel | 单二进制，无配置文件 |
| 仅 HTTP 出网 | Neo-reGeorg | HTTP 隧道穿越防火墙 |
| 高性能需求 | ligolo-ng | TUN 接口，接近原生性能 |

## Phase 3: 深层渗透

通过代理进入内网后，按优先级：
1. **内网侦察** → 参考 `internal-recon` 技能
2. **域环境攻击** → 参考 `ad-domain-attack` 技能
3. **凭据喷洒** → 参考 `cred-spray` 技能
4. **横向移动** → 参考 `lateral-movement` 技能

## 注意事项
- **proxychains 只支持 TCP**，不支持 ICMP（ping 不可用，nmap 用 `-Pn -sT`）
- 隧道建立后先 `proxychains curl` 测试连通性再做大范围扫描
- 隧道进程容易中断，用 `autossh` 或 frp 断线重连保持稳定
- 记录每一跳的凭据和隧道命令，便于重建

## Proxychains 限制
- UDP 不支持：proxychains 仅代理 TCP，UDP 扫描（-sU）会失败
