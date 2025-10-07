- clean up args setup on nonVLM pdf converter
- output arg for mdTable-to-bullets_converter

>> https://docling-project.github.io/docling/examples/export_figures/
    - answers multiple below
    - ? md with embedded example? 
- pipeline_options.generate_page_images doesn't work with any pipeline
    - page images into the result, PIL?
- VLM pipelines not saving all images, ex. keeps text only from the pie chart
    - but this is not a VLM decision - where library decides this? pdf parsing?
        - does it add to my prompt?

>> try Gemini, chatgpt code

- ? PictureDescriptionApiOptions

- nonVLM  better at tables edge cases
- nonVLM truncates/failsFull annotations, no warnings
    - ? and VLM
