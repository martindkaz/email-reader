"""CLI utilities to exercise Docling's PDF conversion pipeline without VLM features."""

import argparse
from pathlib import Path

from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import PdfFormatOption
from docling_core.types.doc import ImageRefMode

DEFAULT_PDF_PATH = Path("tests/test_pdf.pdf")
DEFAULT_JSON_PATH = Path("tests/docling_out_nonVLM.json")
DEFAULT_MARKDOWN_PATH = Path("tests/docling_out_nonVLM.md")
DEFAULT_TABLES_PATH = Path("table_only.md")


def build_converter() -> DocumentConverter:
    """Instantiate a DocumentConverter configured like the original script."""
    pipeline_options = PdfPipelineOptions()
    pipeline_options.images_scale = 2.0  # High-res images for retention
    pipeline_options.generate_page_images = True
    pipeline_options.generate_picture_images = True
    pipeline_options.do_ocr = True
    pipeline_options.do_table_structure = True
    pipeline_options.do_picture_classification = True
    pipeline_options.do_picture_description = True

    return DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )


def print_document_structure(result) -> None:
    """Print basic document statistics and the hierarchical item tree."""
    print("\n=> Document statistics:")
    print(f"   Pages: {len(result.document.pages)}")
    if hasattr(result.document, "tables"):
        print(f"   Tables: {len(result.document.tables)}")
    if hasattr(result.document, "pictures"):
        print(f"   Pictures: {len(result.document.pictures)}")

    for item, level in result.document.iterate_items(with_groups=True, traverse_pictures=True):
        type_name = item.__class__.__name__
        label = getattr(item, "label", None)
        label_str = getattr(label, "name", str(label)) if label is not None else ""
        prefix = "  " * level
        suffix = f" [{label_str}]" if label_str else ""
        print(f"{prefix}- {type_name}{suffix}")


def save_document_json(result, output_path: Path) -> None:
    """Persist the converted document as JSON with referenced images."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.document.save_as_json(str(output_path), image_mode=ImageRefMode.REFERENCED)
    print(f"JSON saved to {output_path}")


def save_document_markdown(result, output_path: Path) -> None:
    """Persist the converted document as markdown with referenced images."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.document.save_as_markdown(str(output_path), image_mode=ImageRefMode.REFERENCED)
    print(f"Markdown saved to {output_path}")


def save_tables_markdown(result, output_path: Path) -> None:
    """Write only table items into a markdown file."""
    tables = getattr(result.document, "tables", [])
    if not tables:
        print("No tables detected in the document.")
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for idx, table in enumerate(tables, start=1):
            handle.write(f"### Table {idx}\n\n")
            handle.write(table.export_to_markdown(doc=result.document))
            handle.write("\n\n")
    print(f"Table markdown saved to {output_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Docling non-VLM PDF utilities. Choose a single action per run."
    )
    parser.add_argument(
        "action",
        choices=("structure", "json", "markdown", "tables"),
        help="Function to execute after converting the PDF.",
    )
    parser.add_argument(
        "--pdf",
        type=Path,
        default=DEFAULT_PDF_PATH,
        help=f"Path to the PDF input file (default: {DEFAULT_PDF_PATH}).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional output path used by 'json', 'markdown', or 'tables' actions.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    pdf_path = args.pdf
    if not pdf_path.is_file():
        raise FileNotFoundError(f"PDF input not found: {pdf_path}")

    converter = build_converter()
    result = converter.convert(str(pdf_path))

    if args.action == "structure":
        print_document_structure(result)
        return

    output_override = args.output
    if args.action == "json":
        target = output_override or DEFAULT_JSON_PATH
        save_document_json(result, target)
    elif args.action == "markdown":
        target = output_override or DEFAULT_MARKDOWN_PATH
        save_document_markdown(result, target)
    elif args.action == "tables":
        target = output_override or DEFAULT_TABLES_PATH
        save_tables_markdown(result, target)


if __name__ == "__main__":
    main()
