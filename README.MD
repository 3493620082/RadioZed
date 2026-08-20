# RadioZed 电台制作工具

> 用于 [Project Zomboid](https://store.steampowered.com/app/108600/Project_Zomboid/) 模组的电台数据编辑工具，支持频道、时段、台词的可视化管理、多语言翻译，以及服务器端翻译文件的生成与同步。

## 功能特性

### 频道界面
- **频道管理** — 新增/编辑/删除收音机或电视机频道，收音机频段 88.0-108.0，电视机频段 200-500
- **时段管理** — 为每个频道配置多个广播时段，按天和起始/结束时间组织，支持批量新增（按天+间隔自动生成）
- **台词管理** — 单条或批量（TXT 导入）添加台词，支持颜色选择器
- **复制粘贴** — 支持多选台词以 JSON 格式复制到剪贴板，跨频道粘贴，自动生成新 UUID
- **搜索过滤** — 频道/时段/台词列表均支持回车搜索过滤

### 翻译界面
- **多语言翻译** — 内置 CN/EN 双语支持，可扩展至 29 种语言
- **文本编辑** — 双击编辑翻译文本，ID + 文本键值对管理
- **语言管理** — 新增/删除语言，右键打开对应语言文件夹

### 服务器翻译界面
- **服务器翻译文件** — 新建项目时自动从 `src/` 复制服务器翻译模板到 `ServerTranslate/`
- **同步功能** — 一键将翻译界面的所有翻译代码追加到服务器翻译文件末尾
- **文件定位** — 打开服务器翻译文件所在目录，方便手动操作

### 通用功能
- **多语言 UI** — 运行时切换界面语言（CN/EN），即时生效
- **文件管理** — 新建/打开/保存电台文件，按钮打开文件所在目录
- **设置窗口** — 语言切换 + 版本号显示

## 项目结构

```
RadioZed/
├── app.py              # 主程序
├── build.py            # 打包脚本
├── build.bat           # 打包批处理
├── config.json         # 配置文件（版本、语言、UI 文本）
├── icon.ico            # 程序图标
├── src/                # 服务器翻译模板文件
│   ├── Server_RadioData_CN.json
│   └── Server_RadioData_EN.json
├── output/             # 项目文件输出目录
└── temp/               # 临时/参考文件
```

### 新建项目结构

```
output/{时间戳}/
├── RadioData.xml               # 电台数据
├── Translate/                  # 翻译文件
│   ├── CN/RadioData.json       # 中文翻译
│   └── EN/RadioData.json       # 英文翻译
└── ServerTranslate/            # 服务器翻译文件
    ├── CN/RadioData.json       # 服务器中文翻译
    └── EN/RadioData.json       # 服务器英文翻译
```

## 快速开始

### 运行源码

```bash
python app.py
```

无额外依赖，仅需 Python 内置的 tkinter。

### 打包

```bash
python build.py
```

输出目录：`RadioZed v{version}/`，包含 `RadioZed.exe`、`config.json`、`icon.ico` 和 `src/` 文件夹。

## 数据格式

### RadioData.xml

```xml
<RadioData>
  <RootInfo>
    <SourceFile>Radio</SourceFile>
    <FileGUID>...</FileGUID>
    <Version>1</Version>
  </RootInfo>
  <Channels>
    <ChannelEntry name="频道名" cat="Radio" freq="88000">
      <ScriptEntry>
        <BroadcastEntry ID="..." timestamp="360" endstamp="720" type="ActivateBroadcast" day="0" advertCat="none" isSegment="false">
          <LineEntry ID="..." r="255" g="192" b="0" />
        </BroadcastEntry>
      </ScriptEntry>
      <ExitOptions />
    </ChannelEntry>
  </Channels>
</RadioData>
```

- `cat`：`Radio`（收音机）或 `TV`（电视机）
- `freq`：收音机 = 频率 × 1000（如 88.0 → 88000），电视机 = 频率值（200-500）
- `timestamp` / `endstamp`：`day × 1440 + 分钟数`
- `LineEntry` 不含 `text` 属性，台词文本存储在翻译文件的 `RD_{ID}` 键中

### 翻译文件

```json
{
    "RD_uuid": "台词文本",
    "RD_uuid2": "另一句台词"
}
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