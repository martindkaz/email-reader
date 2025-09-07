from pathlib import Path
from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import PdfFormatOption

pdf_path = "tests/test_pdf.pdf"
output_json_path = "tests/docling_out_nonVLM.json"

# Configure pipeline options 
pipeline_options = PdfPipelineOptions()
pipeline_options.images_scale = 2.0  # Image resolution scale (required for image retention)
pipeline_options.generate_page_images = True  # Generate full page images
pipeline_options.generate_picture_images = True  # Extract embedded pictures/figures
pipeline_options.do_ocr = True  # Enable OCR if needed
pipeline_options.do_table_structure = True  # Extract table structures
pipeline_options.do_picture_classification = True
pipeline_options.do_picture_description = True

# Create converter with PDF format options
converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)

# Convert the document
result = converter.convert(pdf_path)

print(f"\n=� Document statistics:")
print(f"   Pages: {len(result.document.pages)}")
if hasattr(result.document, 'tables'):
    print(f"   Tables: {len(result.document.tables)}")
if hasattr(result.document, 'pictures'):
    print(f"   Pictures: {len(result.document.pictures)}")

from docling_core.types.doc import ImageRefMode

# Save as JSON with referenced images (images saved as separate files)
result.document.save_as_json(
    output_json_path,
    image_mode=ImageRefMode.REFERENCED
)

# Also save as markdown for readability
markdown_path = output_json_path.replace('.json', '.md')
result.document.save_as_markdown(
    markdown_path,
    image_mode=ImageRefMode.REFERENCED
)







