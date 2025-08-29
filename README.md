# Docling OCR Document Processing Tool

## 概要

[Docling](https://github.com/docling-project/docling)ライブラリの検証用リポジトリです。
PDF、Word文書、PowerPoint、HTML、画像ファイルなどから高精度でテキストを抽出し、Markdown、JSON、プレーンテキスト形式で出力可能です。

## 対応形式

- **PDF** (.pdf) - レイアウト解析とOCR対応
- **Microsoft Word** (.docx) - テキスト・表・画像抽出
- **Microsoft PowerPoint** (.pptx) - スライド内容抽出
- **Microsoft Excel** (.xlsx) - スプレッドシート処理
- **HTML** (.html) - Webページ・HTMLファイル
- **画像ファイル** (.png, .jpg, .jpeg, .tiff) - OCRによるテキスト抽出

## 環境構築

### 必要条件

- Python 3.x系
- uv (パッケージ管理)

### インストール

```bash
# リポジトリをクローン
git clone <repository-url>
cd test-docling

# Python 3.12.3の仮想環境を作成
uv venv --python 3.12.3

# 仮想環境の有効化
source .venv/bin/activate

# 依存関係をインストール
uv sync
```

## 使用方法

### 基本的な使い方

```bash
# 単一ファイルをMarkdown形式で処理
uv run src/main.py --config src/config.json --doc-file media/sample.pdf

# 単一ファイルをMarkdown形式で処理(markdownを明示指定)
uv run src/main.py --config src/config.json --doc-file sample.pdf --format-to-markdown

# JSON出力
uv run src/main.py --config src/config.json --doc-file sample.pdf --output-format json

# テキスト出力
uv run src/main.py --config src/config.json --doc-file sample.pdf --output-format text

# ディレクトリ内の全対応ファイルを処理
uv run src/main.py --config src/config.json --doc-dir media

# 詳細ログ付きで実行
uv run src/main.py --config src/config.json --doc-file media/sample.html --verbose
```

### CPU処理の強制

CUDA環境でもCPU処理を強制する場合：

```bash
CUDA_VISIBLE_DEVICES='' DOCLING_DEVICE=cpu uv run src/main.py --config src/config.json --doc-file media/sample.pdf
```

## 構造

```bash
test-docling/
├── README.md
├── media
│   ├── sample.html     # サンプルのOCR対象ファイル
│   ├── sample.pdf      # サンプルのOCR対象ファイル
│   ├── simple.txt      # サンプルのOCR対象ファイル
│   └── test.txt        # サンプルのOCR対象ファイル
├── output
│   ├── sample.json     # サンプルの出力結果
│   ├── sample.md       # サンプルの出力結果
│   └── sample.txt      # サンプルの出力結果
├── pyproject.toml
├── src
│   ├── config.json     # 設定ファイル
│   └── main.py         # 主となる実行ファイル
└── uv.lock
```

## 設定ファイル

`src/config.json`で動作をカスタマイズできます：

```json
{
  "ocr_settings": {
    "use_ocr": true,
    "ocr_pipeline": "fast",
    "language": "auto"
  },
  "conversion_settings": {
    "export_formats": ["markdown", "json"],
    "include_images": true,
    "preserve_layout": true,
    "extract_tables": true
  },
  "output_settings": {
    "output_dir": "output",
    "create_subdirs": true,
    "overwrite_existing": false
  },
  "device_settings": {
    "use_cpu": true,
    "device": "cpu"
  }
}
```

## ヘルプ

```bash
uv run src/main.py --help
```

詳細な使用例は `examples.md` を参照してください。

## ライセンス

このプロジェクトは検証・テスト用途で作成されています。