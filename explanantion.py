Step	What Happens	Function
 1	PDF is uploaded by user	st.file_uploader()
 2	Text and tables are extracted	pdfplumber.open()
 3	Headers and table rows are analyzed	extract_section_header_from_text(), process_pdf_tables()
 4	Structured output is built	format_output()
 5	Output is shown on Streamlit app	display_results()

 Sample PDF Example Explained
Using this sample PDF, we can break the logic down using real data:

📄 PDF Snippet: test_pdf.pdf



🤖 What the Code Does:
Finds Section Header: 
3.6 List of Components / Assemblies with Inspection Criteria

Detects Main Heading Rows:
Looks for rows with a single number like 1, 2

Example:
1 INCOMING / RAW MATERIAL INSPECTION
2 BOUGHT OUT ITEMS

Captures Subheading Serials:
-Rows like 1.1, 2.1, 2.2, … are subheadings
-These get grouped under their respective section headers

Checks if Table Has Relevant Column:
-Only processes tables that contain a column with: Type of Check


🛠️ Output Example

📋 3.6 List of Components / Assemblies with Inspection Criteria
└── 1 INCOMING / RAW MATERIAL INSPECTION = Page number: 1
    Serials: 1.1
└── 2 BOUGHT OUT ITEMS = Page number: 1
    Serials: 2.1, 2.2, 2.3, 2.4
🔬 Logs Section (Colab-Style)


You also get backend logs like:
📄 Processing Page 1
🔍 Section Header: 3.6 List of Components / Assemblies with Inspection Criteria
✅ Table 1: Type column found.
📌 Main Section: 1_INCOMING / RAW MATERIAL INSPECTION
📌 Main Section: 2_BOUGHT OUT ITEMS

These logs are visible on Streamlit just like they were in Google Colab.
