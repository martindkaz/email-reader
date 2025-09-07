import json
import logging
import os
from pathlib import Path
from typing import Optional
import requests
from dotenv import load_dotenv

from docling.datamodel import vlm_model_specs
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    VlmPipelineOptions,
)
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.pipeline.vlm_pipeline import VlmPipeline

pdf_path = "tests/test_pdf.pdf"
output_json_path = "tests/docling_out_VLM.json"

###########
### Local VLM 
##########

pipeline_options = VlmPipelineOptions(
    generate_picture_images=True, 
    generate_page_images=True,
    images_scale=2.0, 
)
converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(
            pipeline_options=pipeline_options,
            pipeline_cls=VlmPipeline,
        ),
    }
)
result = converter.convert(pdf_path)

###########
### Remote VLM 
##########

from docling_core.types.doc.page import SegmentedPage

from docling.datamodel.pipeline_options_vlm_model import ApiVlmOptions, ResponseFormat

def gemini_vlm_options(model: str, prompt: str):
    load_dotenv()
    api_key = os.environ.get("WX_API_KEY")
    project_id = os.environ.get("WX_PROJECT_ID")

    options = ApiVlmOptions(
        url="https://us-south.ml.cloud.ibm.com/ml/v1/text/chat?version=2023-05-29",
        params=dict(
            model_id=model,
            project_id=project_id,
            parameters=dict(
                max_new_tokens=400,
            ),
        ),
        headers={
            "Authorization": "Bearer " + _get_iam_access_token(api_key=api_key),
        },
        prompt=prompt,
        timeout=300,
        response_format=ResponseFormat.MARKDOWN,
    )
    return options

pipeline_options = VlmPipelineOptions(
    enable_remote_services=True  # <-- this is required!
)
pipeline_options.vlm_options = gemini_vlm_options(
    model="gemini", prompt="OCR the full page to markdown, including annotating images and creating md tables. Your response needs to be only the markdown, no other commentary or the app waiting for your response will break - it expects only the markdown conversion result."
)
doc_converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(
            pipeline_options=pipeline_options,
            pipeline_cls=VlmPipeline,
        )
    }
)
result = doc_converter.convert(pdf_path)


###########
### Results 
##########

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