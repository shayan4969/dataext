import streamlit as st
import pdfplumber
import io
import pandas as pd
from PIL import Image

st.set_page_config(page_title="Datasheet Extractor", page_icon="📄", layout="wide")
st.title("📄 All Tables + Images Extractor (Start from Page 5, No Unknown Titles)")

uploaded_file = st.file_uploader("Upload component datasheet (PDF)", type=["pdf"])

def extract_tables_with_titles(pdf, start_page=5):
    results = []
    for page_num, page in enumerate(pdf.pages, start=1):
        if page_num < start_page:
            continue

        text = page.extract_text() or ""
        lines = text.split("\n") if text else []
        tables = page.extract_tables()

        if not tables:
            continue

        for table in tables:
            table_clean = [[cell if cell else "" for cell in row] for row in table if row]

            first_cell_text = str(table_clean[0][0]) if table_clean else ""
            title = None
            if first_cell_text:
                for idx, line in enumerate(lines):
                    if first_cell_text in line:
                        if idx > 0:
                            title = lines[idx - 1].strip()
                        break

            if not title or title.strip() == "":
                continue

            results.append((page_num, title, table_clean))
    return results

def extract_images(pdf, start_page=5):
    results = []
    for page_num, page in enumerate(pdf.pages, start=1):
        if page_num < start_page:
            continue

        for img_obj in page.images:
            try:
                img_bbox = (img_obj["x0"], img_obj["top"], img_obj["x1"], img_obj["bottom"])
                cropped_img = page.within_bbox(img_bbox).to_image(resolution=150)
                pil_img = cropped_img.image
                results.append((page_num, pil_img))
            except Exception as e:
                print(f"Failed to extract image on page {page_num}: {e}")
    return results

if uploaded_file:
    with pdfplumber.open(io.BytesIO(uploaded_file.read())) as pdf:
        tables_with_titles = extract_tables_with_titles(pdf, start_page=5)
        images_with_pages = extract_images(pdf, start_page=5)

        if tables_with_titles:
            for page_num, title, table in tables_with_titles:
                st.markdown(f"### 📄 Page {page_num}: {title}")
                df = pd.DataFrame(table[1:], columns=table[0])  # Use first row as header
                st.dataframe(df, use_container_width=True)  # Wide mode table
        else:
            st.warning("No titled tables found from page 5 onwards.")

        if images_with_pages:
            st.subheader("🖼 Extracted Images & Graphs")
            for page_num, img in images_with_pages:
                st.markdown(f"**Page {page_num}**")
                st.image(img, use_column_width=True)
        else:
            st.warning("No images found from page 5 onwards.")
