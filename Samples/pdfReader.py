from pypdf import PdfReader

reader = PdfReader("../Week-2/documents/sputnik-sweetheart.pdf")
print(f"Number of pages: {len(reader.pages)}")

for i in [0, 5, 20]:  # spot-check a few pages, not just the first
    text = reader.pages[i].extract_text()
    print(f"\n--- Page {i} ---")
    print(repr(text[:300]) if text else "EMPTY / None")