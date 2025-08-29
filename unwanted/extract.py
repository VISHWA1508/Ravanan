import json
import re

def parse_methodology_enhanced(text):
    """Enhanced methodology parsing to handle merged text properly"""
    if not text:
        return []
    
    # Clean up PDF artifacts
    text = text.replace('&amp;', '&').replace('•', '\n•').replace('◦', '\n◦')
    
    # Split on various patterns that indicate new methodology items
    split_patterns = [
        r'\n+',                    # Line breaks
        r'(?<=\.)\s+(?=[A-Z])',   # After period + space + capital letter
        r'(?<=[a-z])\s+(?=[A-Z][a-z]+:)',  # Before "Word:" patterns
        r'(?<=:)\s+(?=[A-Z])',    # After colon + space + capital
        r'(?<=approach)\s+',      # After "approach"
        r'(?<=framework)\s+',     # After "framework" 
        r'(?<=strategy)\s+',      # After "strategy"
    ]
    
    # Apply all split patterns
    parts = [text]
    for pattern in split_patterns:
        new_parts = []
        for part in parts:
            new_parts.extend(re.split(pattern, part))
        parts = new_parts
    
    # Clean and filter methodology items
    items = []
    for part in parts:
        cleaned = part.strip().rstrip('.').strip()
        
        # Skip if too short, too long, or invalid
        if (len(cleaned) < 10 or len(cleaned) > 150 or
            not cleaned or
            re.match(r'^[•\d\.\-: ]+$', cleaned) or
            cleaned.lower().startswith(('key questions', 'visualization'))):
            continue
        
        # Merge very short adjacent items
        if items and len(cleaned) < 30 and len(items[-1]) < 80:
            items[-1] = items[-1] + ', ' + cleaned.lower()
        else:
            items.append(cleaned)
        
        # Limit to prevent overflow
        if len(items) >= 10:
            break
    
    return items

def parse_key_questions_enhanced(text):
    """Enhanced key questions parsing"""
    if not text:
        return []
    
    # Find sentences ending with question marks
    question_pattern = r'[^?.!]+\?'
    matches = re.findall(question_pattern, text)
    
    cleaned = []
    for q in matches:
        q_clean = q.strip().replace('\n', ' ').replace('  ', ' ')
        
        # Filter substantial questions
        if (len(q_clean) > 20 and 
            q_clean.count(' ') >= 4 and
            not q_clean.startswith(('•', '1.', '2.')) and 
            q_clean not in cleaned):
            cleaned.append(q_clean)
            
        if len(cleaned) >= 8:
            break
    
    return cleaned

def extract_nested_content_fixed(item, level=0):
    """Fixed recursive content extraction with better methodology parsing"""
    content = {
        'title': item.get('title', '').strip(),
        'description': (item.get('content_text', '')[:200] + '...') if item.get('content_text') else ''
    }
    
    methodology_items = []
    key_questions = []
    visualization_text = ''
    nested_subsections = []
    
    # Process sub_divisions
    if 'sub_divisions' in item:
        for sd in item['sub_divisions']:
            sd_title = sd.get('title', '').lower()
            sd_text = sd.get('content_text', '')
            
            if 'methodology' in sd_title:
                methodology_items = parse_methodology_enhanced(sd_text)
            elif 'question' in sd_title:
                key_questions = parse_key_questions_enhanced(sd_text)
            elif 'visualization' in sd_title:
                visualization_text = (sd_text[:200] + '...') if len(sd_text) > 200 else sd_text
            else:
                nested_content = extract_nested_content_fixed(sd, level + 1)
                if (nested_content and nested_content.get('title') and 
                    nested_content.get('title').lower() not in ['methodology:', 'key questions:', 'visualization:']):
                    nested_subsections.append(nested_content)
    
    # Process sub_sub_divisions (This was the missing part!)
    if 'sub_sub_divisions' in item:
        for ssd in item['sub_sub_divisions']:
            ssd_title = ssd.get('title', '').lower()
            ssd_text = ssd.get('content_text', '')
            
            if 'methodology' in ssd_title:
                methodology_items = parse_methodology_enhanced(ssd_text)
            elif 'question' in ssd_title:
                key_questions = parse_key_questions_enhanced(ssd_text)
            elif 'visualization' in ssd_title:
                visualization_text = (ssd_text[:200] + '...') if len(ssd_text) > 200 else ssd_text
            else:
                nested_content = extract_nested_content_fixed(ssd, level + 2)
                if nested_content and nested_content.get('title'):
                    nested_subsections.append(nested_content)
    
    # Only add if content exists and is valid
    if methodology_items:
        content['methodology'] = methodology_items
    if key_questions:
        content['key_questions'] = key_questions
    if visualization_text:
        content['visualization'] = visualization_text
    if nested_subsections:
        content['subsections'] = nested_subsections
    
    return content

def extract_all_sections_fixed(hierarchical_data):
    """Main extraction function with enhanced methodology parsing"""
    sections = []
    
    for main in hierarchical_data:
        title = main.get('title', '').strip()
        
        # Only process numbered main sections
        if not any(c.isdigit() for c in title) or 'framework' in title.lower():
            continue
            
        section_obj = {
            'section_name': title,
            'subsections': []
        }
        
        # Process sub_divisions with enhanced parsing
        if 'sub_divisions' in main:
            for sd in main['sub_divisions']:
                content = extract_nested_content_fixed(sd)
                if content and content.get('title'):
                    section_obj['subsections'].append(content)
        
        # Only add sections with meaningful content
        if section_obj['subsections']:
            sections.append(section_obj)
    
    return sections

def generate_complete_extraction():
    """Complete extraction pipeline with error handling"""
    try:
        # Load your JSON data - UPDATE THIS PATH TO YOUR FILE
        with open('structured_pdf_content.json', "r", encoding="utf-8") as f:
            hierarchical_data = json.load(f)
        
        # Extract with enhanced parsing
        all_sections = extract_all_sections_fixed(hierarchical_data)
        
        # Create output
        extraction_output = {
            "extraction_info": {
                "pdf_file": "comprehensive_investment_framework.pdf",
                "total_sections": len(all_sections),
                "extraction_date": "2025-08-19",
                "framework_type": "Enhanced Investment Analysis Framework",
                "parsing_version": "v3.0_fixed_nested"
            },
            "sections": all_sections
        }
        
        return extraction_output
        
    except FileNotFoundError:
        print("❌ Error: 'structured_pdf_content.json' file not found")
        print("💡 Make sure your JSON file is in the same directory or update the file path")
        return None
    except json.JSONDecodeError:
        print("❌ Error: Invalid JSON format in input file")
        return None
    except Exception as e:
        print(f"❌ Error during extraction: {e}")
        return None

# Usage
if __name__ == "__main__":
    print("🔧 Starting enhanced framework extraction with nested subdivision fix...")
    
    enhanced_framework = generate_complete_extraction()
    
    if enhanced_framework:
        # Save results
        with open("fixed_investment_framework.json", "w", encoding="utf-8") as f:
            json.dump(enhanced_framework, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Successfully extracted {len(enhanced_framework['sections'])} sections")
        print("📁 Saved to: fixed_investment_framework.json")
        
        # Sample output verification
        if enhanced_framework['sections']:
            sample_section = enhanced_framework['sections'][0]
            print(f"\n📊 Sample Section: {sample_section['section_name']}")
            if sample_section['subsections']:
                sample_sub = sample_section['subsections'][0]
                print(f"   📋 Sample Subsection: {sample_sub.get('title', 'No title')}")
                if 'methodology' in sample_sub:
                    print(f"   ✅ Methodology items: {len(sample_sub['methodology'])}")
                    print(f"   📝 First methodology: {sample_sub['methodology'][0][:100]}...")
                if 'key_questions' in sample_sub:
                    print(f"   ❓ Key questions: {len(sample_sub['key_questions'])}")
                    print(f"   🔍 First question: {sample_sub['key_questions'][0][:100]}...")
    else:
        print("❌ Extraction failed. Please check your input file.")
