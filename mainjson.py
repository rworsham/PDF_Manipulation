import pytesseract
from pdf2image import convert_from_path
import PyPDF2
import os
import json
import re


def extract_sections(text):

    section_patterns = {
        'INGREDIENTS': re.compile(r'INGREDIENTS\b'),
        'NUTRITION FACTS': re.compile(r'NUTRITION FACTS\b'),
        'INSTRUCTIONS': re.compile(r'INSTRUCTIONS\b'),
    }

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
            image_file = os.path.join(output_dir, f'page_{start_page + i + 1}.png')
            page.save(image_file, 'PNG')

            text = pytesseract.image_to_string(image_file)
            extracted_sections = extract_sections(text)

            page_data = {
                'page_number': start_page + i + 1,
                'text': text.strip(),
                'ingredients': extracted_sections.get('INGREDIENTS', '').strip(),
                'nutrition_facts': extracted_sections.get('NUTRITION FACTS', '').strip(),
                'instructions': extracted_sections.get('INSTRUCTIONS', '').strip(),
            }

            all_pages_data.append(page_data)

        start_page += batch_size

    with open(json_output_file, 'w', encoding='utf-8') as json_file:
        json.dump(all_pages_data, json_file, ensure_ascii=False, indent=4)

    print("Processing complete")


pdf_path = 'SHL_Cookbook_v3.pdf'
output_dir = 'pdf_images'
json_output_file = 'extracted_text800dpi.json'
batch_size = 4
dpi = 800

process_pdf_in_batches(pdf_path, output_dir, json_output_file, batch_size, dpi)
