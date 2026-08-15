import pymupdf as fitz

doc = fitz.open("../Week-2/documents/sputnik-sweetheart.pdf")
print(f"Number of pages: {len(doc)}")

for i in [0, 5, 20]:
    text = doc[i].get_text()
    print(f"\n--- Page {i} ---")
    print(repr(text[:300]) if text else "EMPTY / None")