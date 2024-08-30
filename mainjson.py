import pytesseract
from pdf2image import convert_from_path
from PIL import Image, ImageFilter, ImageEnhance
import numpy as np
import PyPDF2
import os
import json
import re


def enhance_image(image):
    # Apply adaptive thresholding to handle varying illumination
    np_image = np.array(image)
    threshold_image = np.where(np_image > np.median(np_image), 255, 0).astype(np.uint8)
    threshold_image = Image.fromarray(threshold_image)

    # Enhance contrast
    enhancer = ImageEnhance.Contrast(threshold_image)
    enhanced_image = enhancer.enhance(1.5)  # Adjust contrast factor as needed

    # Sharpen the image to make text edges more distinct
    sharpened_image = enhanced_image.filter(ImageFilter.SHARPEN)

    return sharpened_image


def extract_sections(text, section_patterns):
    sections = {key: '' for key in section_patterns}

    current_section = None
    last_pos = 0

    for section_name, pattern in section_patterns.items():
        matches = list(pattern.finditer(text))
        if matches:
            for match in matches:
                start = match.start()
                if last_pos < start:
                    if current_section:
                        sections[current_section] += text[last_pos:start].strip() + "\n"
                current_section = section_name
                last_pos = start

    if current_section:
        sections[current_section] += text[last_pos:].strip()

    return sections


def process_pdf_in_batches(pdf_path, output_dir, json_output_file, batch_size, dpi):
    os.makedirs(output_dir, exist_ok=True)

    start_page = 0
    print("Counting pages")
    with open(pdf_path, 'rb') as file:
        pdfreader = PyPDF2.PdfReader(file)
        total_pages = len(pdfreader.pages)

    print(f"Total Pages: {total_pages}")

    all_pages_data = []

    while start_page < total_pages:
        end_page = min(start_page + batch_size, total_pages)

        print(f"Processing pages {start_page + 1} to {end_page}")

        pages = convert_from_path(pdf_path, dpi, first_page=start_page + 1, last_page=end_page)

        print("Pages Processed")
        for i, page in enumerate(pages):
            # First pass: Grayscale for 'INSTRUCTIONS' and 'INGREDIENTS'
            grayscale_image = page.convert('L')
            grayscale_image_file = os.path.join(output_dir, f'page_{start_page + i + 1}_gray.png')
            grayscale_image.save(grayscale_image_file, 'PNG')

            # OCR for 'INSTRUCTIONS' and 'INGREDIENTS'
            gray_text = pytesseract.image_to_string(grayscale_image_file)
            gray_section_patterns = {
                'INSTRUCTIONS': re.compile(r'INSTRUCTIONS\b', re.IGNORECASE),
                'INGREDIENTS': re.compile(r'INGREDIENTS\b', re.IGNORECASE),
            }
            gray_extracted_sections = extract_sections(gray_text, gray_section_patterns)

            # Second pass: Enhanced for 'ADDITIONAL NOTES' and 'NUTRITION FACTS'
            enhanced_image = enhance_image(grayscale_image)
            enhanced_image_file = os.path.join(output_dir, f'page_{start_page + i + 1}_enhanced.png')
            enhanced_image.save(enhanced_image_file, 'PNG')

            # OCR for 'ADDITIONAL NOTES' and 'NUTRITION FACTS'
            enhanced_text = pytesseract.image_to_string(enhanced_image_file)
            enhanced_section_patterns = {
                'ADDITIONAL NOTES': re.compile(r'ADDITIONAL NOTES\b', re.IGNORECASE),
                'NUTRITION FACTS': re.compile(r'NUTRITION FACTS\b', re.IGNORECASE),
            }
            enhanced_extracted_sections = extract_sections(enhanced_text, enhanced_section_patterns)

            # Combine results
            page_data = {
                'page_number': start_page + i + 1,
                'text': gray_text.strip() + '\n' + enhanced_text.strip(),
                'ingredients': gray_extracted_sections.get('INGREDIENTS', '').strip(),
                'nutrition_facts': enhanced_extracted_sections.get('NUTRITION FACTS', '').strip(),
                'instructions': gray_extracted_sections.get('INSTRUCTIONS', '').strip(),
                'additional_notes': enhanced_extracted_sections.get('ADDITIONAL NOTES', '').strip(),
            }

            all_pages_data.append(page_data)

        start_page += batch_size

    with open(json_output_file, 'w', encoding='utf-8') as json_file:
        json.dump(all_pages_data, json_file, ensure_ascii=False, indent=4)

    print("Processing complete")


pdf_path = 'SHL_Cookbook_v3.pdf'
output_dir = 'pdf_images'
json_output_file = 'extracted_text800dpiv2.json'
batch_size = 4
dpi = 800

process_pdf_in_batches(pdf_path, output_dir, json_output_file, batch_size, dpi)
