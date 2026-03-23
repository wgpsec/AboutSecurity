---
name: ctf-crypto
description: "CTF 密码学攻击技术。用于 RSA/AES/ECC/格密码/PRNG/ZKP/古典密码等 CTF 加密类挑战。覆盖从古典替换密码到现代公钥密码、椭圆曲线、格攻击、零知识证明等全方位密码学攻防技术"
metadata:
  tags: "ctf,crypto,rsa,aes,ecc,lattice,prng,zkp,密码学,加密"
  difficulty: "hard"
  icon: "🔐"
  category: "CTF"
---

# CTF 密码学攻击

## 深入参考

- 古典密码（Vigenere/Atbash/XOR/OTP/同音替换） → 读 [references/classic-ciphers.md](references/classic-ciphers.md)
- 现代密码攻击（AES/CBC/Padding Oracle/LFSR/MAC伪造） → 读 [references/modern-ciphers.md](references/modern-ciphers.md)
- RSA 攻击（小指数/Wiener/Pollard/Coppersmith/Hastad/CRT） → 读 [references/rsa-attacks.md](references/rsa-attacks.md)
- ECC 攻击（小子群/无效曲线/Smart/ECDSA nonce重用） → 读 [references/ecc-attacks.md](references/ecc-attacks.md)
- 高级数学攻击（格/LWE/同源/Pohlig-Hellman/LLL） → 读 [references/advanced-math.md](references/advanced-math.md)
- PRNG 攻击（MT19937/LCG/V8 XorShift128+/混沌映射） → 读 [references/prng.md](references/prng.md)
- ZKP 与约束求解（Z3/图着色/Groth16/Shamir SSS） → 读 [references/zkp-and-advanced.md](references/zkp-and-advanced.md)
- 历史密码（Lorenz SZ40/42/Book Cipher） → 读 [references/historical.md](references/historical.md)
- 奇异代数结构（辫群DH/热带半环/FPE/Goldwasser-Micali） → 读 [references/exotic-crypto.md](references/exotic-crypto.md)

---

## 分类决策树

```
题目涉及加密？
├─ 古典密码（Caesar/Vigenere/XOR/替换） → references/classic-ciphers.md
├─ 对称加密（AES/DES/RC4/分组密码）
│  ├─ ECB → 块重排 / 逐字节oracle
│  ├─ CBC → 比特翻转 / Padding Oracle
│  └─ 流密码 → LFSR / Berlekamp-Massey
├─ RSA
│  ├─ 小e → 开根号         ├─ 小d → Wiener
│  ├─ p≈q → Fermat          ├─ 公共模数 → ExtGCD
│  └─ 部分已知因子 → Coppersmith (SageMath)
├─ ECC
│  ├─ 阶有小因子 → Pohlig-Hellman
│  ├─ 奇异曲线 → 映射到加法群
│  └─ ECDSA nonce重用 → 恢复私钥
├─ 格/LWE → Babai CVP / LLL 短向量
├─ PRNG → MT19937 untemper / LCG / V8 xs128p
├─ ZKP → 碰撞/预测盐 / Z3求解
└─ 哈希 → 长度扩展(hashpump) / 生日攻击
```

## 速查工具

| 场景 | 工具/命令 |
|------|----------|
| RSA 自动攻击 | `RsaCtfTool.py -n N -e E --uncipher C` |
| 替换密码 | quipqiup.com |
| SageMath | `sage -python script.py`（Coppersmith/ECC/格） |
| Z3 约束求解 | `pip install z3-solver` → BitVec / Int |
| PRNG MT19937 | `pip install not_random`（浮点恢复状态） |
| V8 Math.random | `d0nutptr/v8_rand_buster` |
| Padding Oracle | PadBuster / `padding-oracle` 库 |
| XOR 操作 | `from pwn import xor` |

## 常用 Python 库

```bash
pip install pycryptodome z3-solver sympy gmpy2
```

## RSA 基础速查

```python
from Crypto.Util.number import inverse, long_to_bytes
phi = (p-1)*(q-1)
d = inverse(e, phi)
m = pow(c, d, n)
print(long_to_bytes(m))
```

## 常见模式

- **RSA 乘法同态**：未填充 RSA `S(a)*S(b) mod n = S(a*b)`，可组合签名伪造
- **CBC Padding Oracle**：~4096 次查询解密一个16字节块
- **Bleichenbacher (ROBOT)**：RSA PKCS#1 v1.5 填充oracle → ~10K 次查询恢复明文
- **CRC32 线性**：追加4字节可伪造任意CRC32签名
- **哈希长度扩展**：Merkle-Damgard 结构 `hash(SECRET||data)` 可追加数据
