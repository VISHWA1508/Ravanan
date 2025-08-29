import json

def extract_all_sections_comprehensive(hierarchical_data):
    """
    Extract ALL sections, subsections, and their nested sub-divisions recursively
    """
    result_sections = []
    
    def extract_nested_content(item, level=0):
        """Recursively extract content from nested structures"""
        content = {
            "title": item.get("title", "").strip(),
            "description": item.get("content_text", "")[:200] + "..." if item.get("content_text") else ""
        }
        
        # Extract methodology, key questions, visualization from sub_sub_divisions
        methodology_items = []
        key_questions = []
        visualization_text = ""
        nested_subsections = []
        
        if "sub_sub_divisions" in item:
            for ssd in item["sub_sub_divisions"]:
                ssd_title = ssd.get("title", "").lower()
                ssd_content = ssd.get("content_text", "")
                
                if "methodology" in ssd_title:
                    method_lines = ssd_content.replace(". ", ".\n").split("\n")
                    methodology_items = [
                        line.strip().rstrip(".")
                        for line in method_lines 
                        if line.strip() and len(line.strip()) > 10
                    ][:8]
                        
                elif "key questions" in ssd_title:
                    question_lines = ssd_content.replace("?", "?\n").split("\n")
                    key_questions = [
                        line.strip()
                        for line in question_lines
                        if line.strip().endswith("?")
                    ][:8]
                        
                elif "visualization" in ssd_title:
                    visualization_text = ssd_content[:200] + "..." if len(ssd_content) > 200 else ssd_content
                    
                else:
                    # This is a nested subsection, extract it recursively
                    nested_item = extract_nested_content(ssd, level + 1)
                    if nested_item["title"]:
                        nested_subsections.append(nested_item)
        
        # Handle sub_divisions within current item (for deeper nesting)
        if "sub_divisions" in item:
            for sub_div in item["sub_divisions"]:
                nested_item = extract_nested_content(sub_div, level + 1)
                if nested_item["title"]:
                    nested_subsections.append(nested_item)
        
        # Add extracted components
        if methodology_items:
            content["methodology"] = methodology_items
        if key_questions:
            content["key_questions"] = key_questions
        if visualization_text:
            content["visualization"] = visualization_text
        if nested_subsections:
            content["subsections"] = nested_subsections
            
        return content
    
    # Process main divisions
    for main in hierarchical_data:
        main_title = main.get("title", "").strip()
        
        # Skip non-numbered main divisions
        if not any(char.isdigit() for char in main_title) or "framework" in main_title.lower():
            continue
            
        section_obj = {
            "section_name": main_title,
            "subsections": []
        }
        
        # Process all sub_divisions recursively
        if "sub_divisions" in main:
            for sub in main["sub_divisions"]:
                subsection_data = extract_nested_content(sub)
                if subsection_data["title"]:
                    section_obj["subsections"].append(subsection_data)
        
        # Only add sections that have content
        if section_obj["subsections"]:
            result_sections.append(section_obj)
    
    return result_sections

def generate_complete_framework_extraction():
    """
    Generate the complete extraction with proper nesting
    """
    # Load your JSON data
    with open('structured_pdf_content.json', "r", encoding="utf-8") as f:
        import json
        hierarchical_data = json.load(f)
    
    # Extract all sections with full nesting
    all_sections = extract_all_sections_comprehensive(hierarchical_data)
    
    # Final output
    extraction_output = {
        "extraction_info": {
            "pdf_file": "comprehensive_investment_framework.pdf",
            "total_sections": len(all_sections),
            "extraction_date": "2025-08-19",
            "framework_type": "Complete Top-Down and Bottom-Up Investment Analysis",
            "nesting_levels": "Full recursive extraction"
        },
        "sections": all_sections
    }
    
    return extraction_output

# Usage
complete_framework = generate_complete_framework_extraction()

# Save results
with open("complete_investment_framework.json", "w", encoding="utf-8") as f:
    import json
    json.dump(complete_framework, f, indent=2, ensure_ascii=False)

print(f"📊 Extracted {len(complete_framework['sections'])} main sections")
print(f"📋 With full nested hierarchy including all sub-divisions")
