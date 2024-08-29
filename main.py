import pytesseract
from pdf2image import convert_from_path
import PyPDF2
import os


def process_pdf_in_batches(pdf_path, output_dir, text_output_file, batch_size=10, dpi=600):
    os.makedirs(output_dir, exist_ok=True)


    start_page = 0
    print("count pages")
    file = open('SHL_Cookbook_v3.pdf',
                'rb')

    pdfreader = PyPDF2.PdfReader(file)

    total_pages = len(pdfreader.pages)

    print(f"Total Pages: {total_pages}")

    print("count pages fin")

    with open(text_output_file, 'w', encoding='utf-8') as text_file:
        while start_page < total_pages:
            end_page = min(start_page + batch_size, total_pages)

            print(f"Processing pages {start_page + 1} to {end_page}")

            pages = convert_from_path(pdf_path, dpi, first_page=start_page + 1, last_page=end_page)

            print("Pages Processed")
            for i, page in enumerate(pages):
                image_file = os.path.join(output_dir, f'page_{start_page + i + 1}.png')
                page.save(image_file, 'PNG')

                text = pytesseract.image_to_string(image_file)

                text_file.write(f"\n\n{'=' * 80}\n")
                text_file.write(f"Page {start_page + i + 1}\n")
                text_file.write(f"{'=' * 80}\n\n")
                text_file.write(text)
                text_file.write("\n")

            start_page += batch_size

    print("Processing complete")


# Parameters
pdf_path = 'SHL_Cookbook_v3.pdf'
output_dir = 'pdf_images'
text_output_file = 'extracted_text.txt'
batch_size = 10
dpi = 200

process_pdf_in_batches(pdf_path, output_dir, text_output_file, batch_size, dpi)