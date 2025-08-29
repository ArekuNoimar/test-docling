#!/usr/bin/env python3
"""
Doclingを使用したOCR文書処理ツール

このツールは様々な文書形式（PDF、DOCX、PPTX、HTMLなど）を
OCRを使用して処理し、テキスト内容を抽出します。
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any

from docling.document_converter import DocumentConverter
from tqdm import tqdm


def setup_logging(verbose: bool = False) -> None:
    """ログ設定を構成する。
    
    Args:
        verbose (bool): Trueの場合、詳細出力用にログレベルをDEBUGに設定。
                       Falseの場合、標準出力用にINFOに設定。
    
    Returns:
        None
        
    Behavior:
        タイムスタンプ、レベル、メッセージ形式でグローバルログシステムを設定する。
        以降の全てのログ出力でこの設定が使用される。
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def load_config(config_path: str) -> Dict[str, Any]:
    """JSONファイルから設定を読み込む。
    
    Args:
        config_path (str): JSON設定ファイルのパス。
    
    Returns:
        Dict[str, Any]: OCR設定、変換オプション、出力設定、デバイス設定を含む
                       設定辞書。
    
    Raises:
        SystemExit: 設定ファイルが見つからない場合、または無効なJSONが含まれている場合。
    
    Behavior:
        JSON設定ファイルを読み込み、解析する。ファイルが存在しないか
        不正なJSONを含む場合、エラーメッセージをログに記録してプログラムを終了する。
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error(f"Configuration file not found: {config_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in configuration file: {e}")
        sys.exit(1)


def get_supported_files(directory: str, config: Dict[str, Any]) -> List[Path]:
    """ディレクトリからサポートされているファイルを全て取得する。
    
    Args:
        directory (str): ファイル検索対象のディレクトリパス。
        config (Dict[str, Any]): ファイル拡張子のリスト（例：['.pdf', '.docx']）を
                                含む'supported_formats'を含む設定辞書。
    
    Returns:
        List[Path]: ディレクトリ内で再帰的に見つかったサポート対象拡張子を持つ
                   全ファイルのPathオブジェクトのソート済みリスト。
    
    Behavior:
        設定で定義されたサポート対象ファイル拡張子にマッチするファイルを
        指定ディレクトリ内で再帰的に検索する。サポートされているファイルが
        見つからない場合は空のリストを返す。
    """
    supported_extensions = config.get('supported_formats', [])
    files = []
    
    for ext in supported_extensions:
        pattern = f"**/*{ext}"
        files.extend(Path(directory).glob(pattern))
    
    return sorted(files)


def setup_converter(config: Dict[str, Any]) -> DocumentConverter:
    """設定に基づいてDocumentConverterを設定する。
    
    Args:
        config (Dict[str, Any]): 設定辞書（現在はコンバーター設定に使用されていないが、
                               将来のカスタマイズ用に利用可能）。
    
    Returns:
        DocumentConverter: 様々な文書形式の処理準備が整った設定済みの
                          Docling DocumentConverterインスタンス。
    
    Behavior:
        環境変数を設定してCUDAを無効化し、CPU処理を強制する。
        CPU処理用に最適化されたデフォルト設定でDocumentConverterを作成して返す。
        これにより異なるハードウェア構成間で一貫した動作を保証する。
    """
    import os
    
    # 環境変数を設定してCPU使用を強制
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    os.environ['DOCLING_DEVICE'] = 'cpu'
    
    # デフォルト設定でコンバーターを作成
    converter = DocumentConverter()
    
    return converter


def process_single_file(
    file_path: str, 
    config: Dict[str, Any], 
    converter: DocumentConverter,
    output_format: str = "markdown"
) -> Optional[str]:
    """Docling OCRを使用して単一の文書ファイルを処理する。
    
    Args:
        file_path (str): 処理する文書ファイルのパス。
        config (Dict[str, Any]): 設定辞書（現在は処理で未使用）。
        converter (DocumentConverter): 文書処理用のDoclingコンバーターインスタンス。
        output_format (str): 出力形式 - 'markdown'（デフォルト）、'json'、または'text'。
    
    Returns:
        Optional[str]: 指定された形式での処理済み文書内容の文字列。
                      処理に失敗した場合はNoneを返す。
    
    Behavior:
        1. DoclingでOCRとレイアウト解析を行い文書を変換
        2. テキスト、表、画像、構造要素を抽出
        3. 指定された形式でエクスポート：
           - markdown: ヘッダー、リスト、表を含む構造化形式
           - json: メタデータを含む完全な文書モデルのJSON
           - text: プレーンテキスト内容のみ
        4. エラーを適切に処理し、処理状況をログに記録
    """
    try:
        logging.info(f"Processing: {file_path}")
        
        # Doclingの高度なOCRとレイアウト解析を使用して文書を変換
        result = converter.convert(file_path)
        
        if not result.document:
            logging.error(f"Failed to process document: {file_path}")
            return None
        
        # 形式に基づいてエクスポート
        if output_format.lower() == "markdown":
            content = result.document.export_to_markdown()
        elif output_format.lower() == "json":
            content = result.document.model_dump_json(indent=2)
        else:
            content = result.document.export_to_text()
        
        return content
        
    except Exception as e:
        logging.error(f"Error processing {file_path}: {str(e)}")
        return None


def save_output(
    content: str, 
    input_path: str, 
    config: Dict[str, Any], 
    output_format: str = "markdown"
) -> str:
    """処理済みコンテンツを自動命名とファイル名衝突処理付きで出力ファイルに保存する。
    
    Args:
        content (str): 保存する処理済み文書内容。
        input_path (str): 元の入力ファイルパス（出力ファイル名生成に使用）。
        config (Dict[str, Any]): 次の項目を含むoutput_settingsを含む設定：
                                - output_dir: 出力ファイル用ディレクトリ
                                - overwrite_existing: 既存ファイルを上書きするかどうか
        output_format (str): ファイル拡張子を決定する形式 - 'markdown'（.md）、
                           'json'（.json）、または'text'（.txt）。
    
    Returns:
        str: 保存された出力ファイルのパス、保存に失敗した場合は空文字列。
    
    Behavior:
        1. 出力ディレクトリが存在しない場合は作成
        2. 入力ファイル名と出力形式に基づいてファイル名を生成
        3. 番号を追加（_1、_2など）してファイル名衝突を処理
        4. UTF-8エンコーディングで内容を保存
        5. 具体的なエラーメッセージで成功または失敗をログに記録
    """
    output_settings = config.get('output_settings', {})
    output_dir = Path(output_settings.get('output_dir', 'output'))
    
    # 出力ディレクトリが存在しない場合は作成
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 形式に基づいて出力ファイル名を生成
    input_file = Path(input_path)
    if output_format.lower() == "markdown":
        output_file = output_dir / f"{input_file.stem}.md"
    elif output_format.lower() == "json":
        output_file = output_dir / f"{input_file.stem}.json"
    else:
        output_file = output_dir / f"{input_file.stem}.txt"
    
    # 上書きが無効な場合はファイル名衝突を処理
    if output_file.exists() and not output_settings.get('overwrite_existing', False):
        counter = 1
        base_name = output_file.stem
        suffix = output_file.suffix
        while output_file.exists():
            output_file = output_dir / f"{base_name}_{counter}{suffix}"
            counter += 1
    
    # UTF-8エンコーディングで内容を保存
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        logging.info(f"Output saved to: {output_file}")
        return str(output_file)
    except Exception as e:
        logging.error(f"Error saving output: {str(e)}")
        return ""


def main():
    """Docling OCR文書処理ツールのメインエントリーポイント。
    
    Args:
        None（argparseによりコマンドライン引数を使用）
    
    Returns:
        None（成功時はステータスコード0、失敗時は1で終了）
    
    Behavior:
        1. 設定ファイルと入力ファイル用のコマンドライン引数を解析
        2. 詳細レベルに基づいてログを設定
        3. JSONファイルから設定を読み込み
        4. CPU処理でDocling DocumentConverterを初期化
        5. 引数に基づいて単一ファイルまたはディレクトリ内ファイルを処理
        6. OCRを使用して文書を変換し、指定された形式でエクスポート
        7. 進捗追跡付きで結果を出力ディレクトリに保存
        8. 処理統計を報告し、適切なステータスコードで終了
    """
    parser = argparse.ArgumentParser(
        description="Doclingを使用したOCR文書処理ツール",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  %(prog)s --config src/config.json --doc-file media/sample.pdf
  %(prog)s --config src/config.json --doc-file media/sample.pdf --format-to-markdown
  %(prog)s --config src/config.json --doc-dir media
  %(prog)s --config src/config.json --doc-file media/sample.docx --output-format json
        """
    )
    
    parser.add_argument(
        '--config',
        required=True,
        help='設定JSONファイルのパス'
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--doc-file',
        help='処理する単一文書ファイルのパス'
    )
    group.add_argument(
        '--doc-dir',
        help='処理する文書を含むディレクトリのパス'
    )
    
    parser.add_argument(
        '--format-to-markdown',
        action='store_true',
        help='Markdown形式で出力（デフォルト）'
    )
    
    parser.add_argument(
        '--output-format',
        choices=['markdown', 'json', 'text'],
        default='markdown',
        help='出力形式（デフォルト: markdown）'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='詳細ログを有効化'
    )
    
    args = parser.parse_args()
    
    # ログ設定
    setup_logging(args.verbose)
    
    # 設定読み込み
    config = load_config(args.config)
    
    # コンバーター設定
    converter = setup_converter(config)
    
    # 出力形式決定
    output_format = args.output_format
    if args.format_to_markdown:
        output_format = 'markdown'
    
    # 文書処理
    files_to_process = []
    
    if args.doc_file:
        if not Path(args.doc_file).exists():
            logging.error(f"File not found: {args.doc_file}")
            sys.exit(1)
        files_to_process = [Path(args.doc_file)]
    
    elif args.doc_dir:
        if not Path(args.doc_dir).exists():
            logging.error(f"Directory not found: {args.doc_dir}")
            sys.exit(1)
        files_to_process = get_supported_files(args.doc_dir, config)
        if not files_to_process:
            logging.warning(f"No supported files found in: {args.doc_dir}")
            sys.exit(0)
    
    # 進捗バー付きでファイル処理
    logging.info(f"Processing {len(files_to_process)} file(s)")
    
    successful = 0
    failed = 0
    
    for file_path in tqdm(files_to_process, desc="文書処理中"):
        content = process_single_file(str(file_path), config, converter, output_format)
        
        if content:
            output_path = save_output(content, str(file_path), config, output_format)
            if output_path:
                successful += 1
            else:
                failed += 1
        else:
            failed += 1
    
    # 処理結果まとめ
    logging.info(f"Processing complete. Successful: {successful}, Failed: {failed}")
    
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()