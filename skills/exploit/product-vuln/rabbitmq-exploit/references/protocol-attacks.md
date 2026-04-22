# epmd枚举与协议攻击

## epmd端口枚举

### 漏洞描述

Erlang Port Mapper Daemon (epmd) 运行在4369端口，用于映射Erlang节点名到端口。攻击者可查询epmd获取RabbitMQ的Erlang分布端口信息，为进一步的Cookie攻击做准备。

### 枚举命令

```bash
# 使用epmd查询
epmd -names -address <target>

# 输出示例:
# epmd: up and running on port 4369 with data:
# name rabbit at port 25672
```

### 手工枚举

```bash
# 发送ALIVE请求
printf "\x00\x00\x00\x01\x6e" | nc -w 3 <target> 4369

# 发送NAMES请求
printf "\x00\x00\x00\x00" | nc -w 3 <target> 4369
```

### Nmap扫描

```bash
# AMQP信息枚举
nmap -sV -Pn -n -T4 -p 5672 --script amqp-info <target>

# epmd枚举
nmap -sV -Pn -n -T4 -p 4369 --script epmd-info <target>
```

---

## STOMP未授权

当启用STOMP插件 (61613端口) 时：

```bash
# 使用nmap检测
nmap -sV -p 61613 --script stomp-info <target>
```

---

## MQTT匿名访问 & Docker环境利用

当启用MQTT插件 (1883端口) 或运行于Docker环境时，存在额外攻击面：
- MQTT匿名订阅/发布 (mosquitto命令)
- Docker默认Cookie获取
- Docker API读取Cookie
