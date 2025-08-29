import fitz  # PyMuPDF
import json

def get_unique_fonts_and_text(pdf_file_path):
    """
    Extract unique (font, font_size) pairs and their associated text from PDF
    """
    doc = fitz.open(pdf_file_path)
    
    # Dictionary to store unique (font, size) combinations and their text
    unique_fonts = {}
    
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        blocks = page.get_text("dict")["blocks"]
        
        for block in blocks:
            if block["type"] == 0:  # text block
                for line in block["lines"]:
                    for span in line["spans"]:
                        font_name = span["font"]
                        font_size = round(span["size"], 1)  # round to 1 decimal
                        text = span["text"].strip()
                        
                        # Skip empty text
                        if not text:
                            continue
                            
                        # Create unique key
                        key = (font_name, font_size)
                        
                        # Add to dictionary
                        if key not in unique_fonts:
                            unique_fonts[key] = []
                        
                        # Avoid duplicate text for same font+size
                        if text not in unique_fonts[key]:
                            unique_fonts[key].append(text)
    
    doc.close()
    
    # Convert to desired format
    result = []
    for (font, size), texts in unique_fonts.items():
        result.append({
            "font": font,
            "font_size": size,
            "text": " ".join(texts)  # Join all texts for this font+size
        })
    
    return result

# Usage
if __name__ == "__main__":
    pdf_file = "comprehensive_investment_framework.pdf"
    
    unique_fonts = get_unique_fonts_and_text(pdf_file)
    
    # Print results as structured JSON
    print(json.dumps(unique_fonts, indent=2, ensure_ascii=False))

    with open("fonts_output.json", "w", encoding="utf-8") as f:
        json.dump(unique_fonts, f, indent=2, ensure_ascii=False)

