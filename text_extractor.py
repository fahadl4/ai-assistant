
from docling.document_converter import DocumentConverter

converter = DocumentConverter()

result = converter.convert("file-sample_1MB.docx")

markdown = result.document.export_to_markdown()

print("\n========== OCR RESULT ==========\n")
print(markdown)

import base64
from pathlib import Path
from docling.document_converter import DocumentConverter

# Create a folder for extracted images
output_dir = Path("extracted_images")
output_dir.mkdir(exist_ok=True)

# Converter for OCR
image_converter = DocumentConverter()

for index, picture in enumerate(result.document.pictures, start=1):

    if not picture.image:
        print(f"Picture {index}: No image data available")
        continue

    uri = str(picture.image.uri)

    # Separate Base64 data from the data URI
    image_data = uri.split(",", 1)[1]

    # Decode Base64 into actual image bytes
    image_bytes = base64.b64decode(image_data)

    # Save the image
    image_path = output_dir / f"picture_{index}.png"
    image_path.write_bytes(image_bytes)

    print(f"\n========== PICTURE {index} OCR ==========")

    # Run OCR on the extracted image
    image_result = image_converter.convert(str(image_path))

    print(image_result.document.export_to_markdown())