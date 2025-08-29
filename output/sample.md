# OCRテスト文書

## 概要

この文書は、Doclingライブラリを使用したOCRテストのためのサンプル文書です。

## 機能

- PDF文書の解析
- Word文書の処理
- PowerPoint文書の変換
- HTML文書の読み込み
- 画像ファイルからのテキスト抽出

## 対応形式

| 形式         | 拡張子   | OCR対応   |
|------------|-------|---------|
| PDF        | .pdf  | ✓       |
| Word       | .docx | ✓       |
| PowerPoint | .pptx | ✓       |
| HTML       | .html | ✓       |

## 使用方法

コマンドライン例:

```
uv run src/main.py --config src/config.json --doc-file media/sample.html
uv run src/main.py --config src/config.json --doc-dir media --output-format markdown
```

このサンプル文書により、HTMLからのテキスト抽出機能をテストできます。