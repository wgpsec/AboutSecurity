# Regular

---

`字典来自网络,仅供学习和研究使用,请勿将字典用于非法用途,任何人造成的任何负面影响,与本人无关.`

---

# 分类

- Address : 地址字典
    - 省级、县级、地级,更加详细的不提供,请参考下面的提取方式自行用 `jq` 从源文件生成

- letter : 字母字典
    - 英文大小写字母字典

- number : 数字字典
    - 0-10、0-100、0-1000、0-10000、000000-010000、000000-100000 等

---

# 来源

- [modood/Administrative-divisions-of-China](https://github.com/modood/Administrative-divisions-of-China) - 中华人民共和国行政区划:省级(省份直辖市自治区)、 地级(城市)、 县级(区县)、 乡级(乡镇街道)、 村级(村委会居委会) ,中国省市区镇村二级三级四级五级联动地址数据 Node.js 爬虫.

---

# 提取方式

linux 下使用 jq 工具,以 Administrative-divisions-of-China 中的 pcas.json 为例

```bash
wget https://raw.githubusercontent.com/modood/Administrative-divisions-of-China/master/dist/pcas.json

apt install -y jq

cat pcas.json | jq '."北京市"' > out.txt                      # 获取北京市所有辖区、街道信息
cat pcas.json | jq '."北京市"."市辖区"' > out.txt
cat pcas.json | jq '."北京市"."市辖区"."东城区"' > out.txt      # 获取北京市东城区所有街道信息

cat pcas.json | jq '."江苏省"' > out.txt
cat pcas.json | jq '."江苏省"."南京市"' > out.txt
cat pcas.json | jq '."江苏省"."南京市"."玄武区"' > out.txt
```
