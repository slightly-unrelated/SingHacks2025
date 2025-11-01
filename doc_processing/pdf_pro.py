import fitz
import os

def pdf_to_png(pdf, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    out = []
    with fitz.open(pdf) as d:
        n, lp = d.page_count, d.load_page
        base = os.path.splitext(os.path.basename(pdf))[0]
        for i in range(n):
            f = os.path.join(out_dir, f"{base}_p{i}.png")
            lp(i).get_pixmap(matrix=fitz.Matrix(1, 1), alpha=False).save(f)
            out.append(f)
    return out


print(pdf_to_png("test.pdf", "doc_processing\\output_images"))