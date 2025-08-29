#!/usr/bin/env python3
"""
OCR Document Processing Tool using Docling

This tool processes various document formats (PDF, DOCX, PPTX, HTML, etc.) 
using OCR and extracts text content.
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
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from JSON file."""
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
    """Get all supported files from a directory."""
    supported_extensions = config.get('supported_formats', [])
    files = []
    
    for ext in supported_extensions:
        pattern = f"**/*{ext}"
        files.extend(Path(directory).glob(pattern))
    
    return sorted(files)


def setup_converter(config: Dict[str, Any]) -> DocumentConverter:
    """Setup DocumentConverter based on configuration."""
    import os
    
    # Force CPU usage by setting environment variable
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    os.environ['DOCLING_DEVICE'] = 'cpu'
    
    # Create converter with default settings
    converter = DocumentConverter()
    
    return converter


def process_single_file(
    file_path: str, 
    config: Dict[str, Any], 
    converter: DocumentConverter,
    output_format: str = "markdown"
) -> Optional[str]:
    """Process a single document file."""
    try:
        logging.info(f"Processing: {file_path}")
        
        # Convert document
        result = converter.convert(file_path)
        
        if not result.document:
            logging.error(f"Failed to process document: {file_path}")
            return None
        
        # Export based on format
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
    """Save processed content to output file."""
    output_settings = config.get('output_settings', {})
    output_dir = Path(output_settings.get('output_dir', 'output'))
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate output filename
    input_file = Path(input_path)
    if output_format.lower() == "markdown":
        output_file = output_dir / f"{input_file.stem}.md"
    elif output_format.lower() == "json":
        output_file = output_dir / f"{input_file.stem}.json"
    else:
        output_file = output_dir / f"{input_file.stem}.txt"
    
    # Check if file exists and handle overwrite setting
    if output_file.exists() and not output_settings.get('overwrite_existing', False):
        counter = 1
        base_name = output_file.stem
        suffix = output_file.suffix
        while output_file.exists():
            output_file = output_dir / f"{base_name}_{counter}{suffix}"
            counter += 1
    
    # Save content
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        logging.info(f"Output saved to: {output_file}")
        return str(output_file)
    except Exception as e:
        logging.error(f"Error saving output: {str(e)}")
        return ""


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="OCR Document Processing Tool using Docling",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --config src/config.json --doc-file media/sample.pdf
  %(prog)s --config src/config.json --doc-file media/sample.pdf --format-to-markdown
  %(prog)s --config src/config.json --doc-dir media
  %(prog)s --config src/config.json --doc-file media/sample.docx --output-format json
        """
    )
    
    parser.add_argument(
        '--config',
        required=True,
        help='Path to configuration JSON file'
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--doc-file',
        help='Path to a single document file to process'
    )
    group.add_argument(
        '--doc-dir',
        help='Path to directory containing documents to process'
    )
    
    parser.add_argument(
        '--format-to-markdown',
        action='store_true',
        help='Output in markdown format (default)'
    )
    
    parser.add_argument(
        '--output-format',
        choices=['markdown', 'json', 'text'],
        default='markdown',
        help='Output format (default: markdown)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Load configuration
    config = load_config(args.config)
    
    # Setup converter
    converter = setup_converter(config)
    
    # Determine output format
    output_format = args.output_format
    if args.format_to_markdown:
        output_format = 'markdown'
    
    # Process documents
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
    
    # Process files with progress bar
    logging.info(f"Processing {len(files_to_process)} file(s)")
    
    successful = 0
    failed = 0
    
    for file_path in tqdm(files_to_process, desc="Processing documents"):
        content = process_single_file(str(file_path), config, converter, output_format)
        
        if content:
            output_path = save_output(content, str(file_path), config, output_format)
            if output_path:
                successful += 1
            else:
                failed += 1
        else:
            failed += 1
    
    # Summary
    logging.info(f"Processing complete. Successful: {successful}, Failed: {failed}")
    
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()