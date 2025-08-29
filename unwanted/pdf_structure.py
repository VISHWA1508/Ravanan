import fitz  # PyMuPDF
import json

def extract_hierarchical_structure_by_font(pdf_file_path):
    """
    Extract PDF content and organize it hierarchically purely based on font sizes
    """
    doc = fitz.open(pdf_file_path)
    
    # Extract all text elements with their font info
    all_text_elements = []
    
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        blocks = page.get_text("dict")["blocks"]
        
        for block in blocks:
            if block["type"] == 0:  # text block
                for line in block["lines"]:
                    for span in line["spans"]:
                        font_name = span["font"]
                        font_size = round(span["size"], 1)
                        text = span["text"].strip()
                        
                        if text:  # Skip empty text
                            all_text_elements.append({
                                "font": font_name,
                                "font_size": font_size,
                                "text": text,
                                "page": page_num + 1
                            })
    
    doc.close()
    
    # Get unique font sizes and sort them in descending order (largest first)
    unique_font_sizes = sorted(set([elem["font_size"] for elem in all_text_elements]), reverse=True)
    
    # Assign hierarchy levels based on font size ranking
    hierarchy_mapping = {}
    level_names = ["main_division", "sub_division", "sub_sub_division", "another_sub_division", "content"]
    
    for i, font_size in enumerate(unique_font_sizes):
        if i < len(level_names) - 1:
            hierarchy_mapping[font_size] = level_names[i]
        else:
            hierarchy_mapping[font_size] = "content"
    
    # Build the hierarchical structure
    structured_content = []
    current_hierarchy = {
        "main": None,
        "sub": None,
        "sub_sub": None,
        "another_sub": None
    }
    
    for element in all_text_elements:
        level = hierarchy_mapping[element["font_size"]]
        
        if level == "main_division":
            # Start new main division
            current_hierarchy["main"] = {
                "type": "main_division",
                "font": element["font"],
                "font_size": element["font_size"],
                "title": element["text"],
                "page": element["page"],
                "sub_divisions": []
            }
            structured_content.append(current_hierarchy["main"])
            current_hierarchy["sub"] = None
            current_hierarchy["sub_sub"] = None
            current_hierarchy["another_sub"] = None
            
        elif level == "sub_division":
            if current_hierarchy["main"]:
                current_hierarchy["sub"] = {
                    "type": "sub_division",
                    "font": element["font"],
                    "font_size": element["font_size"],
                    "title": element["text"],
                    "page": element["page"],
                    "sub_sub_divisions": [],
                    "content": []
                }
                current_hierarchy["main"]["sub_divisions"].append(current_hierarchy["sub"])
                current_hierarchy["sub_sub"] = None
                current_hierarchy["another_sub"] = None
                
        elif level == "sub_sub_division":
            if current_hierarchy["sub"]:
                current_hierarchy["sub_sub"] = {
                    "type": "sub_sub_division",
                    "font": element["font"],
                    "font_size": element["font_size"],
                    "title": element["text"],
                    "page": element["page"],
                    "another_sub_divisions": [],
                    "content": []
                }
                current_hierarchy["sub"]["sub_sub_divisions"].append(current_hierarchy["sub_sub"])
                current_hierarchy["another_sub"] = None
                
        elif level == "another_sub_division":
            if current_hierarchy["sub_sub"]:
                current_hierarchy["another_sub"] = {
                    "type": "another_sub_division",
                    "font": element["font"],
                    "font_size": element["font_size"],
                    "title": element["text"],
                    "page": element["page"],
                    "content": []
                }
                current_hierarchy["sub_sub"]["another_sub_divisions"].append(current_hierarchy["another_sub"])
                
        elif level == "content":
            # Add content to the most specific current level
            content_item = {
                "font": element["font"],
                "font_size": element["font_size"],
                "text": element["text"],
                "page": element["page"]
            }
            
            # Find the most specific level to add content
            if current_hierarchy["another_sub"]:
                current_hierarchy["another_sub"]["content"].append(content_item)
            elif current_hierarchy["sub_sub"]:
                current_hierarchy["sub_sub"]["content"].append(content_item)
            elif current_hierarchy["sub"]:
                current_hierarchy["sub"]["content"].append(content_item)
            elif current_hierarchy["main"]:
                if "content" not in current_hierarchy["main"]:
                    current_hierarchy["main"]["content"] = []
                current_hierarchy["main"]["content"].append(content_item)
    
    return {
        "document_structure": structured_content,
        "font_hierarchy": {
            "font_size_levels": hierarchy_mapping,
            "unique_font_sizes": unique_font_sizes,
            "total_elements": len(all_text_elements)
        }
    }

def consolidate_content(data):
    """
    Consolidate content arrays into readable text and preserve details
    """
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            if key == "content" and isinstance(value, list) and value:
                # Consolidate text content
                consolidated_text = " ".join([item["text"] for item in value if "text" in item])
                result["content_text"] = consolidated_text
                result["content_details"] = value  # Keep original details
            elif isinstance(value, (list, dict)):
                result[key] = consolidate_content(value)
            else:
                result[key] = value
        return result
    elif isinstance(data, list):
        return [consolidate_content(item) for item in data]
    else:
        return data

# Usage
if __name__ == "__main__":
    pdf_file = "comprehensive_investment_framework.pdf"
    
    # Extract hierarchical structure based on font sizes
    hierarchical_data = extract_hierarchical_structure_by_font(pdf_file)
    
    # Consolidate content for readability
    consolidated_data = consolidate_content(hierarchical_data)
    
    # Save to JSON file
    with open("font_based_structure.json", "w", encoding="utf-8") as f:
        json.dump(consolidated_data, f, indent=2, ensure_ascii=False)
    
    # Print font hierarchy info
    print("Font Size Hierarchy:")
    for font_size, level in hierarchical_data["font_hierarchy"]["font_size_levels"].items():
        print(f"  Font Size {font_size}: {level}")
    
    print(f"\nTotal elements extracted: {hierarchical_data['font_hierarchy']['total_elements']}")
    print(f"Main divisions found: {len(hierarchical_data['document_structure'])}")
    
    # Print structure summary
    for i, main_div in enumerate(hierarchical_data["document_structure"]):
        print(f"\nMain Division {i+1} (Font: {main_div['font_size']}): {main_div['title'][:60]}...")
        if 'sub_divisions' in main_div:
            print(f"  └─ Sub-divisions: {len(main_div['sub_divisions'])}")
            for j, sub_div in enumerate(main_div['sub_divisions']):
                print(f"     └─ {j+1}. (Font: {sub_div['font_size']}) {sub_div['title'][:50]}...")
                if 'sub_sub_divisions' in sub_div and sub_div['sub_sub_divisions']:
                    print(f"        └─ Sub-sub-divisions: {len(sub_div['sub_sub_divisions'])}")
    
    print(f"\nStructured data saved to 'font_based_structure.json'")