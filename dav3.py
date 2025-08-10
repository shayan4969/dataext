import streamlit as st
import pdfplumber
import io
import pandas as pd
from PIL import Image

st.set_page_config(page_title="Datasheet Extractor", page_icon="📄", layout="wide")
st.title("DATASHEET INFORMATION")

uploaded_file = st.file_uploader("Upload component datasheet (PDF)", type=["pdf"])

# ---------------- Function to extract tables with titles ----------------
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

            # Guess table title from text above first cell
            first_cell_text = str(table_clean[0][0]) if table_clean else ""
            title = None
            if first_cell_text:
                for idx, line in enumerate(lines):
                    if first_cell_text in line:
                        if idx > 0:
                            title = lines[idx - 1].strip()
                        break

            # Skip if no proper title
            if not title or title.strip() == "":
                continue

            results.append((page_num, title, table_clean))
    return results

# ---------------- Function to extract images ----------------
def extract_images(pdf, start_page=5):
    results = []
    for page_num, page in enumerate(pdf.pages, start=1):
        if page_num < start_page:
            continue

        for img_obj in page.images:
            try:
                x0, top, x1, bottom = img_obj["x0"], img_obj["top"], img_obj["x1"], img_obj["bottom"]
                cropped_img = page.within_bbox((x0, top, x1, bottom)).to_image(resolution=150)
                pil_img = cropped_img.image
                results.append((page_num, pil_img))
            except Exception as e:
                print(f"Failed to extract image on page {page_num}: {e}")
    return results

# ---------------- Main App Logic ----------------
if uploaded_file:
    with pdfplumber.open(io.BytesIO(uploaded_file.read())) as pdf:
        tables_with_titles = extract_tables_with_titles(pdf, start_page=5)
        images_with_pages = extract_images(pdf, start_page=5)

        # ---------- Display tables ----------
        if tables_with_titles:
            for idx, (page_num, title, table) in enumerate(tables_with_titles):
                st.markdown(f"### 📄 Page {page_num}: {title}")

                # Create DataFrame
                df = pd.DataFrame(table[1:], columns=table[0])

                # Deduplicate column names if repeated
                df.columns = pd.io.parsers.ParserBase({'names': df.columns})._maybe_dedup_names(df.columns)

                st.dataframe(df, use_container_width=True)

                # CSV download with guaranteed unique key
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label=f"Download '{title}' as CSV",
                    data=csv,
                    file_name=f"{title.replace(' ', '_')}.csv",
                    mime="text/csv",
                    key=f"download_btn_{idx}"  # Always unique
                )
        else:
            st.warning("No titled tables found from page 5 onwards.")

        # ---------- Display images ----------
        if images_with_pages:
            st.subheader("🖼 Extracted Images & Graphs")
            for idx, (page_num, img) in enumerate(images_with_pages):
                st.markdown(f"**Page {page_num}**")
                st.image(img, use_column_width=True)
        else:
            st.warning("No images found from page 5 onwards.")
