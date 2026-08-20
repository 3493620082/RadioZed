# RadioZed 电台制作工具

> 用于 [Project Zomboid](https://store.steampowered.com/app/108600/Project_Zomboid/) 模组的电台数据编辑工具，支持频道、时段、台词的可视化管理与多语言翻译。 

## 功能特性

- **频道管理** — 新增/编辑/删除收音机或电视机频道，支持 88.0-108.0（收音机）和 200-500（电视机）频段
- **时段管理** — 为每个频道配置多个广播时段，按天和起始/结束时间组织
- **台词管理** — 单条或批量添加台词，支持颜色选择、右键复制、搜索过滤
- **翻译系统** — 内置 CN/EN 双语支持，可扩展 29 种语言，台词文本通过 JSON 翻译文件管理
- **多语言 UI** — 运行时切换界面语言，即时生效
- **批量导入** — 从 TXT 文件批量导入台词，逐行读取

## 项目结构

```
RadioZed/
├── app.py              # 主程序
├── build.py            # 打包脚本
├── build.bat           # 打包批处理
├── config.json         # 配置文件（版本、语言、UI 文本）
├── icon.ico            # 程序图标
├── output/             # 项目文件输出目录
└── temp/               # 模板文件参考
```

## 快速开始

### 运行源码

```bash
pip install -r requirements.txt  # 无额外依赖，仅需 tkinter（Python 内置）
python app.py
```

### 打包

```bash
python build.py
```

输出目录：`RadioZed v{version}/`

## 数据格式

### RadioData.xml

每个新建项目自动生成 `output/{时间戳}/RadioData.xml`，结构如下：

```xml
<RadioData>
  <FileGUID>...</FileGUID>
  <Channels>
    <ChannelEntry name="..." cat="Radio" freq="88000">
      <ScriptEntry>
        <BroadcastEntry day="0" timestamp="360" endstamp="720">
          <LineEntry ID="1" r="255" g="192" b="0" />
        </BroadcastEntry>
      </ScriptEntry>
      <ExitOptions />
    </ChannelEntry>
  </Channels>
</RadioData>
```

- `freq`：收音机 = 频率 × 1000（如 88.0 → 88000），电视机 = 频率值（200-500）
- `timestamp` / `endstamp`：`day × 1440 + 分钟数`
- `LineEntry` 不含 `text` 属性，台词文本存储在翻译文件中

### 翻译文件

```
Translate/
├── CN/
│   └── RadioData.json    # {"RD_1": "台词文本", ...}
└── EN/
    └── RadioData.json    # {"RD_1": "Line text", ...}
```

## 支持的语言

| 代码 | 语言 | 代码 | 语言 |
|------|------|------|------|
| AR | 阿拉伯语 | JP | 日语 |
| CA | 加泰罗尼亚语 | KO | 韩语 |
| CH | 中文（繁体） | NL | 荷兰语 |
| CN | 中文（简体） | NO | 挪威语 |
| CS | 捷克语 | PL | 波兰语 |
| DA | 丹麦语 | PT | 葡萄牙语 |
| DE | 德语 | PTBR | 葡萄牙语（巴西） |
| EN | 英语 | RO | 罗马尼亚语 |
| ES | 西班牙语 | RU | 俄语 |
| ES_CL | 西班牙语（智利） | STREW | 自定义 |
| ES_MX | 西班牙语（墨西哥） | TH | 泰语 |
| FI | 芬兰语 | TR | 土耳其语 |
| FR | 法语 | UA | 乌克兰语 |
| HU | 匈牙利语 | | |
| ID | 印尼语 | | |
| IT | 意大利语 | | |

## 许可证

MIT