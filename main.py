import streamlit as st
import os
from PIL import Image
import google.generativeai as genai
from dotenv import load_dotenv
import fitz  # PyMuPDF
import markdown
import html2text

load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

model = genai.GenerativeModel('gemini-pro-vision')

def get_gemini_response(input, image, prompt):
    response = model.generate_content([input, image[0], prompt])
    return response.text

def input_image_details(uploaded_file):
    if uploaded_file is not None:
        bytes_data = uploaded_file.getvalue()

        image_parts = [
            {
                "mime_type": uploaded_file.type,
                "data": bytes_data
            }
        ]

        return image_parts
    else:
        raise FileNotFoundError("No file uploaded")

def pdf_to_images(pdf_file):
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    images = []
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pix = page.get_pixmap()
        image_data = pix.tobytes("png")
        images.append(image_data)
    return images

def format_as_latex(markdown_text):
    latex_template = r"""
    \documentclass{{article}}
    \usepackage{{amsmath}}
    \usepackage{{graphicx}}
    \usepackage{{hyperref}}
    \title{{Transcribed Notes}}
    \author{{}}
    \date{{\today}}
    \begin{{document}}
    \maketitle
    \tableofcontents
    \newpage
    {content}
    \end{{document}}
    """
    # Convert markdown to LaTeX
    latex_content = md_to_latex(markdown_text)
    return latex_template.format(content=latex_content)

def md_to_latex(md_text):
    """Convert markdown text to LaTeX formatted text."""
    md_lines = md_text.split("\n")
    latex_lines = []
    for line in md_lines:
        if line.startswith("# "):
            latex_lines.append("\\section{" + line[2:] + "}")
        elif line.startswith("## "):
            latex_lines.append("\\subsection{" + line[3:] + "}")
        elif line.startswith("### "):
            latex_lines.append("\\subsubsection{" + line[4:] + "}")
        elif line.startswith("- "):
            latex_lines.append("\\item " + line[2:])
        elif line.startswith("**") and line.endswith("**"):
            latex_lines.append("\\textbf{" + line[2:-2] + "}")
        else:
            latex_lines.append(line)
    return "\n".join(latex_lines)

st.set_page_config(page_title="Handwritten Notes Transcription")

st.header('Handwritten Notes Transcription with Google Gemini')
input = st.text_input("Input prompt: ", key='input')
uploaded_file = st.file_uploader("Choose a PDF of handwritten notes", type=["pdf"])
output_format = st.radio("Choose output format:", ("Plain Text", "LaTeX", "Markdown"))
images = []
if uploaded_file is not None:
    images = pdf_to_images(uploaded_file)
    st.write(f"Uploaded PDF with {len(images)} pages")

submit = st.button("Transcribe Notes")

md_prompt = """
You have to transcribe the handwritten notes in the image. The system should accurately recognize 
and transcribe the text displayed in the image in Markdown format. 
The output should contain structured text with title, summary, chapters, paragraphs, subparagraphs, and so on.
"""

plain_text_prompt = """
You have to transcribe the handwritten notes in the image. The system should accurately recognize 
and transcribe the text displayed in the image in plain text format.
The output must be displayed in plain text with no markup or formatting.
"""

if submit and images:
    all_responses = []
    for image_data in images:
        image_parts = [{"mime_type": "image/png", "data": image_data}]
        current_prompt = plain_text_prompt if output_format == "Plain Text" else md_prompt
        response = get_gemini_response(current_prompt, image_parts, input)
        all_responses.append(response)

    full_transcription_md = "\n\n".join(all_responses)
    
    if output_format == "LaTeX":
        formatted_output = format_as_latex(full_transcription_md)
    elif output_format == "Plain Text":
        formatted_output = full_transcription_md
    else:
        formatted_output = full_transcription_md
    
    st.subheader("Transcription report: ")
    st.write(formatted_output)
    
    st.download_button(
        label="Download Transcription",
        data=formatted_output,
        file_name="transcription.tex" if output_format == "LaTeX" else "transcription.txt" if output_format == "Plain Text" else "transcription.md",
        mime="application/x-tex" if output_format == "LaTeX" else "text/plain" if output_format == "Plain Text" else "text/markdown"
    )
