import fitz
doc = fitz.open(r"R:\Phaiml\struc.pdf")
print(f"Pages: {len(doc)}")
for i, page in enumerate(doc):
    text = page.get_text()
    print(f"--- Page {i+1} text length: {len(text)} ---")
    if text.strip():
        print(text)
    else:
        # Try to extract images info
        imgs = page.get_images()
        print(f"  Images on page: {len(imgs)}")
        # Try OCR-like extraction with blocks
        blocks = page.get_text("blocks")
        print(f"  Text blocks: {len(blocks)}")
        for b in blocks:
            print(f"    Block: {b}")
        # Save page as image for viewing
        pix = page.get_pixmap(dpi=200)
        pix.save(f"R:\\Phaiml\\struc_page_{i+1}.png")
        print(f"  Saved as struc_page_{i+1}.png")
