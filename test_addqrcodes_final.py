import os
import fitz  # PyMuPDF
from reportlab.lib.pagesizes import A3, landscape
from reportlab.lib.units import cm
import re

def sort_files_numerically(files):
    def numerical_sort(value):
        parts = re.split(r'(\d+)', value)
        return [int(part) if part.isdigit() else part for part in parts]
    return sorted(files, key=numerical_sort)

def add_qr_codes_to_a3(input_folder, output_folder, title_name, output_pdf_name, batch_size=294):
    # Define the size of each QR code (2.0 cm x 2.0 cm)
    qr_size = 2.0 * cm

    # Get a list of all PDF files in the input folder and sort them numerically
    pdf_files = sort_files_numerically([f for f in os.listdir(input_folder) if f.endswith('.pdf')])

    intermediate_pdfs = []

    # Calculate the number of QR codes that fit in one row and one column
    num_cols = int(landscape(A3)[0] // qr_size)
    num_rows = int(landscape(A3)[1] // qr_size)

    # Loop through each batch and create separate intermediate PDFs
    for batch_num, i in enumerate(range(0, len(pdf_files), batch_size)):
        # Create a new PDF for this batch
        batch_output_pdf = os.path.join(input_folder, f'intermediate_batch_{batch_num}.pdf')
        intermediate_pdfs.append(batch_output_pdf)
        output_pdf_doc = fitz.open()

        # Initialize position counters
        x_pos = 0
        y_pos = 1.7 * cm  # Leave space at the top of the page

        # Create a new page for the A3 paper in landscape mode
        page = output_pdf_doc.new_page(width=landscape(A3)[0], height=landscape(A3)[1])

        # Insert text in the top-right corner of the A3 page
        insert_text_top_right(page, title_name, qr_size)
        
        batch = pdf_files[i:i+batch_size]
        for pdf_file in batch:
            # Read the QR code PDF file
            qr_pdf_path = os.path.join(input_folder, pdf_file)
            if not os.path.exists(qr_pdf_path):
                print(f"File not found: {qr_pdf_path}")
                continue
            try:
                with fitz.open(qr_pdf_path) as qr_pdf_doc:
                    # Extract the first page of the QR code PDF
                    qr_page = qr_pdf_doc[0]
                    
                    # Define the rectangle where the QR code will be placed
                    rect = fitz.Rect(x_pos, y_pos, x_pos + qr_size, y_pos + qr_size)

                    # Place the QR code on the A3 page within the grid square
                    page.show_pdf_page(rect, qr_pdf_doc, 0)

                    # Update position counters
                    x_pos += qr_size
                    if x_pos + qr_size > landscape(A3)[0]:
                        # Move to the next row
                        x_pos = 0
                        y_pos += qr_size

                        # If we reach the bottom of the page, create a new page
                        if y_pos + qr_size > landscape(A3)[1] + 2.0 * cm:  # Want to start new page at next line
                            draw_grid_lines(page, num_cols, num_rows, qr_size)
                            page = output_pdf_doc.new_page(width=landscape(A3)[0], height=landscape(A3)[1])
                            insert_text_top_right(page, title_name, qr_size)  # Insert text in the new page
                            x_pos = 0
                            y_pos = 1.7 * cm # Must be same as the top value

            except Exception as e:
                print(f"Error opening {qr_pdf_path}: {e}")
                continue

        # Draw grid lines on the last page
        draw_grid_lines(page, num_cols, num_rows, qr_size)
        output_pdf_doc.save(batch_output_pdf)
        output_pdf_doc.close()

    # Merge all intermediate PDFs into the final output
    final_output_pdf_path = os.path.join(output_folder, output_pdf_name)
    merge_pdfs(intermediate_pdfs, final_output_pdf_path)

    # Remove intermediate PDFs
    for intermediate_pdf in intermediate_pdfs:
        os.remove(intermediate_pdf)

def insert_text_top_right(page, title_name, qr_size):
    # Coordinates for the top-right corner, leaving space at the top
    top_right_x = landscape(A3)[0] - 8.0 * cm  # Adjust to be close to the edge
    top_right_y = 1.0 * cm  # Adjust for space from the top

    # Add the text at the calculated position
    page.insert_text((top_right_x, top_right_y), title_name, fontsize=20, rotate=0)

def draw_grid_lines(page, num_cols, num_rows, qr_size):
    for i in range(num_cols + 1):
        x = i * qr_size # Draw vertical lines
        page.draw_line(fitz.Point(x, 1.7 * cm), fitz.Point(x, landscape(A3)[1] - 0 * cm))  # Leave space at top and bottom
    for j in range(num_rows + 1):
        y = j * qr_size
        page.draw_line(fitz.Point(0, y - 0.3 * cm), fitz.Point(landscape(A3)[0], y - 0.3 * cm))  # Draw horizontal lines

def merge_pdfs(input_pdfs, output_pdf):
    output_pdf_doc = fitz.open()

    for input_pdf in input_pdfs:
        with fitz.open(input_pdf) as pdf:
            for page in pdf:
                output_pdf_doc.insert_pdf(pdf, from_page=0, to_page=pdf.page_count - 1)

    output_pdf_doc.save(output_pdf)
    output_pdf_doc.close()
