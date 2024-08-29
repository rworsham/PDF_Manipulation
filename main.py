import pytesseract
from pdf2image import convert_from_path
import PyPDF2
import os
import csv

def process_pdf_in_batches(pdf_path, output_dir, csv_output_file, batch_size, dpi):
    os.makedirs(output_dir, exist_ok=True)

    start_page = 0
    print("Counting pages")
    file = open(pdf_path, 'rb')

    pdfreader = PyPDF2.PdfReader(file)

    total_pages = len(pdfreader.pages)

    print(f"Total Pages: {total_pages}")

    print("Counting pages finished")

    with open(csv_output_file, 'w', newline='', encoding='utf-8') as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(['Page Number', 'Extracted Text'])

        while start_page < total_pages:
            end_page = min(start_page + batch_size, total_pages)

            print(f"Processing pages {start_page + 1} to {end_page}")

            pages = convert_from_path(pdf_path, dpi, first_page=start_page + 1, last_page=end_page)

            print("Pages Processed")
            for i, page in enumerate(pages):
                image_file = os.path.join(output_dir, f'page_{start_page + i + 1}.png')
                page.save(image_file, 'PNG')

                text = pytesseract.image_to_string(image_file)

                csv_writer.writerow([f'Page {start_page + i + 1}', text])

            start_page += batch_size

    print("Processing complete")

# Parameters
pdf_path = 'SHL_Cookbook_v3.pdf'
output_dir = 'pdf_images'
csv_output_file = 'extracted_text.csv'
batch_size = 5
dpi = 400

process_pdf_in_batches(pdf_path, output_dir, csv_output_file, batch_size, dpi)