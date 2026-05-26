# DeepSeek Image OCR Bridge

让 DeepSeek、Reasonix 等文本模型"看懂"图片 — 通过 Tesseract OCR 提取文字证据，再由模型基于文字做推理分析。

## 工作流程

```
图片 → Tesseract OCR (文字提取) → 结构化元数据 → DeepSeek/Reasonix 文本模型 (推理分析)
```

## 文件结构

```
deepseek-image-ocr/
├── SKILL.md                          # Codex 技能定义（工作流与使用说明）
├── README.md                         # 本文件
├── scripts/
│   └── image_ocr_bridge.py           # OCR 桥接脚本（核心）
└── references/
    └── provider-env.md               # Provider 环境变量配置说明
```

## 依赖安装

### 1. Tesseract OCR

```powershell
winget install --id=UB-Mannheim.TesseractOCR
```

### 2. 中文语言包

```powershell
# 下载到 tessdata 目录
Invoke-WebRequest -Uri "https://github.com/tesseract-ocr/tessdata/raw/main/chi_sim.traineddata" -OutFile "$env:ProgramFiles\Tesseract-OCR\tessdata\chi_sim.traineddata"
```

### 3. Python 依赖

```powershell
pip install Pillow
```

## 使用示例

### 基础 OCR 提取

```powershell
python scripts/image_ocr_bridge.py photo.png --lang chi_sim+eng --format markdown
```

### 中文 OCR

```powershell
python scripts/image_ocr_bridge.py screenshot.png --lang chi_sim --psm 11
```

### OCR + 模型推理（DeepSeek）

```powershell
$env:DEEPSEEK_API_KEY="sk-..."
$env:DEEPSEEK_BASE_URL="https://api.deepseek.com"
python scripts/image_ocr_bridge.py image.png --ask --question "这张图里有什么重点信息？"
```

### OCR + 模型推理（Reasonix）

```powershell
$env:REASONIX_API_KEY="..."
$env:REASONIX_BASE_URL="https://your-endpoint"
python scripts/image_ocr_bridge.py image.png --provider reasonix --ask
```

## 输出格式

- `--format markdown` — Markdown 格式（默认），包含元数据、OCR 文本、模型回复
- `--format json` — JSON 格式，适合程序化处理

## Tesseract PSM 模式参考

| PSM | 适用场景 |
|-----|---------|
| `3` | 自动页面分割（默认） |
| `6` | 整齐段落文本 |
| `11` | 稀疏内容（截图/UI） |

## License

MIT
