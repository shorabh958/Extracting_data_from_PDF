!pip install streamlit
!pip install pdfplumber
!pip install -r requirements.txt

!curl https://loca.lt/mytunnelpassword

!streamlit run /content/app.py &>/content/logs.txt &

##pdf_path ="/content/QAP-POWER SUPPLY P15B 26 09 2016-01.pdf"
#pdf_path = "/content/dummy_data.pdf"
#pdf_path = "/content/QAP-POWER SUPPLY P15B 09.01.2017.pdf"
#pdf_path = "/content/QAP-POWER SUPPLY P15B 09.09.2016.pdf"
#pdf_path = "/content/QAP-POWER SUPPLY P15B 30.08.2016.pdf"
#pdf_path = '/content/test_pdf.pdf'
#pdf_path = '/content/01 QAP 100m IFB 01.pdf'
#pdf_path = '/content/INS Shivalik Retrofit QAP  ( Final copy ).pdf'

%%writefile app.py
import pdfplumber
import re
import io
import streamlit as st
#with pdfplumber.open(pdf_path) as pdf:
#  pass
from textwrap import shorten
from collections import defaultdict
from collections import OrderedDict


def clean_cell(cell):
    return cell.strip().replace('\n', ' ') if cell else ''

def has_type_column(table):
    if not table or len(table) < 2:
        return False
    for row in table[:4]:
        if row:
            for cell in row:
                if cell:
                    cell_lower = cell.lower()
                    if ('type' in cell_lower and ('check' in cell_lower or 'of' in cell_lower)) or \
                       cell_lower.strip() == 'type':
                        return True
    return False

def extract_section_header_from_text(text):
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
        match = re.match(r'^(\d+(\.\d+)+)\s+(.*)$', line)
        if match:
            sec_num = match.group(1)
            title = match.group(3).strip().rstrip(':')
            return f"{sec_num} {title}"
    return None

def is_main_heading(cell_text):
    return bool(cell_text and re.match(r'^\d+$', cell_text.strip()))

def is_subheading(cell_text):
    return bool(cell_text and re.match(r'^\d+\.\d+([A-Z]?)$', cell_text.strip()))

def extract_section_title_from_row(row, next_row=None):
    title = ""
    for i in range(1, min(len(row), 4)):
        part = clean_cell(row[i]) if row[i] else ''
        if part and len(part) > 3:
            title += part + " "
    if next_row:
        for i in range(1, min(len(next_row), 4)):
            part = clean_cell(next_row[i]) if next_row[i] else ''
            if part and len(part) > 3 and part not in title:
                title += part + " "
    title = title.strip()
    title = re.sub(r'\s+', ' ', title)
    return title.upper() if title else "UNKNOWN SECTION"

def process_pdf_tables(pdf_file):
    all_sections = OrderedDict()
    current_section_header = None
    debug_logs = ""

    with pdfplumber.open(pdf_file) as pdf:
        section_headers_by_page = {}
        for page_num, page in enumerate(pdf.pages, 1):
            text = page.extract_text() or ""
            header = extract_section_header_from_text(text)
            if header:
                section_headers_by_page[page_num] = header

    with pdfplumber.open(pdf_file) as pdf:
        current_main_section = None
        for page_num, page in enumerate(pdf.pages, 1):
            debug_logs += f"📄 Processing Page {page_num}\n"
            section_header = section_headers_by_page.get(page_num, current_section_header)
            if section_header:
                current_section_header = section_header
                debug_logs += f"🔍 Section Header: {current_section_header}\n"

            tables = page.extract_tables()
            for table_idx, table in enumerate(tables):
                if not has_type_column(table):
                    debug_logs += f"  ⏭️ Table {table_idx+1}: No 'Type' column found.\n"
                    continue
                debug_logs += f"  ✅ Table {table_idx+1}: 'Type' column found.\n"

                for i, row in enumerate(table):
                    if not row or len(row) < 2:
                        continue
                    first_cell = clean_cell(row[0])
                    next_row = table[i+1] if i+1 < len(table) else None
                    if is_main_heading(first_cell):
                        section_title = extract_section_title_from_row(row, next_row)
                        section_key = f"{first_cell}_{section_title}"
                        debug_logs += f"    📌 Main Section: {section_key}\n"
                        if section_key not in all_sections:
                            all_sections[section_key] = {
                                'section_header': current_section_header,
                                'main_number': first_cell,
                                'section_title': section_title,
                                'subheadings': [],
                                'pages': set()
                            }
                        all_sections[section_key]['pages'].add(page_num)
                        current_main_section = section_key
                    elif is_subheading(first_cell):
                        if not current_main_section:
                            continue
                        if first_cell not in all_sections[current_main_section]['subheadings']:
                            all_sections[current_main_section]['subheadings'].append(first_cell)
                        all_sections[current_main_section]['pages'].add(page_num)

    results = []
    for sec in all_sections.values():
        sub = sorted(sec['subheadings'], key=lambda x: [int(x.split('.')[0]), float(x.split('.')[1])])
        pages = sorted(sec['pages'])
        results.append({
            'section_header': sec['section_header'],
            'main_number': sec['main_number'],
            'section_title': sec['section_title'],
            'subheadings': sub,
            'pages': pages,
            'page_range': f"{min(pages)}-{max(pages)}" if len(pages) > 1 else str(pages[0])
        })

    return results, debug_logs


def display_results(results, debug_logs):
    if not results:
        st.error("❌ No matching sections found.")
        return

    # 🔝 First show the Colab-style log output at the top
    st.markdown("### 🧪 Debug Logs (Colab Style)")
    st.text_area("Logs", debug_logs, height=300)

    # 🔽 Then show the formatted sectioned output
    grouped = defaultdict(list)
    for res in results:
        grouped[res['section_header']].append(res)

    st.markdown("### 📋 QUALITY ASSURANCE PLAN STRUCTURE")
    for section_header, entries in grouped.items():
        st.markdown(f"#### 📋 {section_header}")
        for item in entries:
            st.markdown(f"**└── {item['main_number']} {item['section_title']}** = Page number: {item['page_range']}")
            if item['subheadings']:
                for i in range(0, len(item['subheadings']), 10):
                    chunk = item['subheadings'][i:i+10]
                    prefix = "  Serials: " if i == 0 else "    "
                    st.text(f"{prefix}{', '.join(chunk)}")
            else:
                st.text("  No subheadings found.")
        st.markdown("---")



st.title("📄 PDF Section & Table Extractor")
st.write("Upload a PDF and extract section-wise tables with 'Type of Check' columns.")

uploaded_file = st.file_uploader("📤 Upload PDF file", type=["pdf"])
if uploaded_file:
    st.success(f"Uploaded: {uploaded_file.name}")
    pdf_data = io.BytesIO(uploaded_file.read())
    results, logs = process_pdf_tables(pdf_data)
    display_results(results, logs)

!streamlit run app.py &> /content/logs.txt &
!npx localtunnel --port 8501

!npx localtunnel --port 8501

