import streamlit as st
from streamlit_pdf_viewer import pdf_viewer
import os
from PIL import Image
import google.generativeai as genai
from dotenv import load_dotenv
import fitz  # PyMuPDF
import markdown
from markdownify import markdownify as md
from concurrent.futures import ThreadPoolExecutor, as_completed
import pypandoc


#################################################################
##################### ENVIRONMENT VARIABLES #####################
#################################################################

# Load environment variables from a .env file
load_dotenv()

# Maximum number of workers for the ThreadPoolExecutor
max_workers = 10



#################################################################
########################### FUNCTIONS ###########################
#################################################################

# Configure the genai library with an API key obtained from the environment variables
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Initialize a generative model using the 'gemini-pro-vision' model
model = genai.GenerativeModel('gemini-pro-vision')

def get_gemini_response(input, image):
    """
    Generates a response using the Gemini model.

    Args:
        input (str): The input text.
        image (list): A list of images.

    Returns:
        str: The generated response.
    """
    response = model.generate_content([input, image[0]])
    return response.text

def input_image_details(uploaded_file):
    """
    Extracts image details from an uploaded file.

    Args:
        uploaded_file (file-like object): The uploaded file object.

    Returns:
        list: A list containing a dictionary with the MIME type and data of the uploaded file.

    Raises:
        FileNotFoundError: If no file is uploaded.
    """
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
    """
    Convert a PDF file into a list of images.

    Args:
        pdf_file (file): The PDF file to be converted.

    Returns:
        list: A list of image data in PNG format.
    """
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    images = []
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pix = page.get_pixmap()
        image_data = pix.tobytes("png")
        images.append(image_data)
    return images

def md_to_latex(md_content):
    """
    Convert Markdown content to LaTeX format.

    Args:
        md_content (str): The Markdown content to be converted.

    Returns:
        str: The full LaTeX content.

    """
    latex_preamble = r"""\documentclass[a4paper, openright]{report}
\usepackage[a4paper,top=3cm,bottom=3cm,left=3cm,right=3cm]{geometry}
\usepackage[fontsize=13pt]{scrextend}
\usepackage[english,italian]{babel}
\usepackage[fixlanguage]{babelbib}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{lipsum}
\usepackage{rotating}
\usepackage{fancyhdr}
\usepackage{amssymb}
\usepackage{amsmath}
\usepackage{amsthm}
\usepackage{graphicx}
\usepackage{subcaption}
\usepackage[dvipsnames]{xcolor}
\usepackage{listings}
\usepackage{hyperref}
\title{Transcribed Notes}
\author{}
\date{\today}
\usepackage[normalem]{ulem}
\usepackage{titlesec}
\usepackage{array}
\pagestyle{fancy}
\fancyhf{}
\lhead{\rightmark}
\rhead{\textbf{\thepage}}
\fancyfoot{}
\setlength{\headheight}{15.6pt}
\fancypagestyle{plain}{ 
\fancyfoot{}
\fancyhead{}
\renewcommand{\headrulewidth}{0pt}
}
\lstdefinestyle{codeStyle}{ 
    commentstyle=\color{teal},
    keywordstyle=\color{Magenta},
    numberstyle=\tiny\color{gray},
    stringstyle=\color{violet},
    basicstyle=\ttfamily\footnotesize,
    breakatwhitespace=false,     
    breaklines=true,                 
    captionpos=b,                    
    keepspaces=true,                 
    numbers=left,                    
    numbersep=5pt,                  
    showspaces=false,                
    showstringspaces=false,
    showtabs=false,
    tabsize=2
}
\lstset{style=codeStyle}
\lstdefinestyle{longBlock}{ 
    commentstyle=\color{teal},
    keywordstyle=\color{Magenta},
    numberstyle=\tiny\color{gray},
    stringstyle=\color{violet},
    basicstyle=\ttfamily\tiny,
    breakatwhitespace=false,         
    breaklines=true,                 
    captionpos=b,                    
    keepspaces=true,                 
    numbers=left,                    
    numbersep=5pt,                  
    showspaces=false,                
    showstringspaces=false,
    showtabs=false,                  
    tabsize=2
}
\lstset{style=codeStyle}
\lstset{aboveskip=20pt,belowskip=20pt}
\definecolor{mycolor}{RGB}{0, 112, 192}
\hypersetup{ 
    colorlinks,
    linkcolor=mycolor,
    citecolor=mycolor
}
\newtheorem{definition}{Definition}[section]
\newtheorem{theorem}{Theorem}[section]
\providecommand*\definitionautorefname{Definition}
\providecommand*\theoremautorefname{Theorem}
\providecommand*\listingautorefname{Listing}
\providecommand*\lstnumberautorefname{Line}
\raggedbottom
\begin{document}
\maketitle
    """
    latex_body = pypandoc.convert_text(md_content, 'latex', format='md')
    latex_postamble = r"""
\end{document}
    """
    full_latex_content = latex_preamble + latex_body + latex_postamble
    return full_latex_content

def get_custom_prompt(format):
    """
    Returns a custom prompt based on the specified format.

    Parameters:
        format (str): The desired format of the prompt. Can be "Markdown" or any other format.

    Returns:
        str: The custom prompt based on the specified format.

    Raises:
        None

    Example:
        >>> get_custom_prompt("Markdown")
        'You have to transcribe the handwritten notes in the image. 
        The system should accurately recognize and transcribe the text displayed in the image 
        in Markdown format. The output should contain structured text with title, chapters, paragraphs, subparagraphs, and so on.'

        >>> get_custom_prompt("Plain Text")
        'You have to transcribe the handwritten notes in the image. 
        The system should accurately recognize and transcribe the text displayed in the image 
        in plain text format. The output must be displayed in plain text with no markup or formatting.'
    """
    base_prompt = '''
You have to transcribe the handwritten notes in the image. 
The system should accurately recognize 
and transcribe the text displayed in the image '''
    if format == "Markdown" or format == "LaTeX":
        return f'''{base_prompt} in Markdown format. 
The output should contain structured text with title, chapters, paragraphs, subparagraphs, and so on.
        '''
    else:
        return f'''{base_prompt} in plain text format.
The output must be displayed in plain text with no markup or formatting.
        '''

def get_echanced_text_prompt(format, input_text):
    """
    Generates a prompt for enhancing a given text.

    Args:
        format (str): The desired format for the enhanced text. Can be "Markdown", "LaTeX", or any other format.
        input_text (str): The text to be enhanced.

    Returns:
        str: The generated prompt for enhancing the text.

    Raises:
        None

    """
    base_prompt = f'''
You have to enhance this text:

\'\'\'
{input_text}
\'\'\'

in {format} format. Don't repeat what is displayed in the image,
which however can provide you more context about the text to enhance.
The system should accurately enhance the text, correct any errors, 
and provide additional information or context to the text
    '''
    if format == "Markdown" or format == "LaTeX":
        return f'''{base_prompt}.
The output can contain some structured text in {format} format.
        '''
    else:
        return f'''{base_prompt} in plain text format.
The output must be displayed in plain text with no markup or formatting.
        '''

def get_image_index(input_text):
    """
    Returns the index of the first occurrence of the input_text in the list of all_responses.

    Parameters:
    input_text (str): The text to search for in the list of all_responses.

    Returns:
    int: The index of the first occurrence of the input_text in the list of all_responses. If no match is found, returns 0.
    """
    for i, response in enumerate(st.session_state.all_responses):
        if input_text in response:
            return i
    return 0

def process_file():
    """
    Process the file by converting images to text using a ThreadPoolExecutor.

    The function converts images to text using a ThreadPoolExecutor with a maximum number of workers specified by `max_workers`.
    The format of the converted text is determined by the `format_selected` session state variable.
    The converted text is stored in the `output` session state variable.

    Returns:
        None
    """
    st.session_state.format_selected = "Plain Text" if st.session_state.plain_text_convert else "Markdown" if st.session_state.markdown_convert else "LaTeX"
    tasks = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for i, image_data in enumerate(st.session_state.images):
            image_parts = [{"mime_type": "image/png", "data": image_data}]
            task = executor.submit(get_gemini_response, get_custom_prompt(st.session_state.format_selected), image_parts)
            tasks[i] = task

    st.session_state.all_responses = [None] * len(st.session_state.images)
    for i in tasks:
        future = tasks[i]
        result = future.result()
        st.session_state.all_responses[i] = result

    st.session_state.output = "\n\n".join(st.session_state.all_responses)

    if st.session_state.format_selected == "LaTeX":
        st.session_state.output = md_to_latex(st.session_state.output)



#################################################################
########################### INTERFACE ###########################
#################################################################

# Set page config first
st.set_page_config(page_title="Plūma - Handwritten Notes Transcription", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for the Streamlit app
st.markdown(
    """
    <style>
    body {
        background-color: #316989; /* Colore di sfondo */
        color: #316989;            /* Colore del testo */
        font-family: 'sans serif'; /* Font */
    }
    .stButton>button {
        background-color: #CB3E3E;  /* Colore di sfondo */
        color: white;                /* Colore del testo */
        border-radius: 5px;          /* Angoli arrotondati */
        transition: background-color 0.3s;  /* Effetto di transizione */
        font-family: 'sans serif'; /* Font */
    }
    .stButton>button:hover {
        background-color: #F0A5A5;   /* Colore di sfondo al passaggio del mouse */
        font-family: 'sans serif'; /* Font */
    }
    .stTextArea {
        background-color: #316989;  /* Colore di sfondo della Text Area */
        color: #316989;              /* Colore del testo */
        border: 2px solid #316989;  /* Colore del bordo */
        border-radius: 5px;
        font-family: 'sans serif'; /* Font */
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Session state to store the uploaded file
def initialize_session_state():
    if 'uploaded_file' not in st.session_state:
        st.session_state.uploaded_file = None
    if 'st.session_state.result_box' not in st.session_state:
        st.session_state.result_box = ""
    if 'st.session_state.input_box' not in st.session_state:
        st.session_state.input_box = ""
    if 'enhanced_text' not in st.session_state:
        st.session_state.enhanced_text = ""
    if "plain_text_convert" not in st.session_state:
        st.session_state.plain_text_convert = False
    if "markdown_convert" not in st.session_state:
        st.session_state.markdown_convert = False
    if "latex_convert" not in st.session_state:
        st.session_state.latex_convert = False
    if "enhanced_button" not in st.session_state:
        st.session_state.enhanced_button = False
    if "format_selected" not in st.session_state:
        st.session_state.format_selected = ""
    if "images" not in st.session_state:
        st.session_state.images = []
    if "result_box" not in st.session_state:
        st.session_state.result_box = ""
    if "input_box" not in st.session_state:
        st.session_state.input_box = ""
    if "output" not in st.session_state:
        st.session_state.output = ""
    if "all_responses" not in st.session_state:
        st.session_state.all_responses = []
    if "pdf_ref" not in st.session_state:
        st.session_state.pdf_ref = None

# Initialize session state
initialize_session_state()

# Title and header
st.title("Plūma")

l, r = st.columns(2)
with l:
    # Allow users to upload a PDF file containing handwritten notes
    st.session_state.uploaded_file = st.file_uploader(r"Choose a PDF of handwritten notes", type=["pdf"])
    # Conversion buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        st.session_state.plain_text_convert = st.button("Convert to Plain Text")
    with col2:
        st.session_state.markdown_convert = st.button("Convert to Markdown")
    with col3:
        st.session_state.latex_convert = st.button("Convert to LaTeX")
    # Check if a file is uploaded and display the number of pages in the PDF
    if st.session_state.uploaded_file is not None:
        st.session_state.images = pdf_to_images(st.session_state.uploaded_file)
        st.write(f"Uploaded PDF with {len(st.session_state.images)} pages")
    st.text("")
    st.text("")
    st.text("")
    st.text("")
with r:
    if st.session_state.uploaded_file is not None:
        # Display the uploaded PDF file
        pdf_viewer(input=st.session_state.uploaded_file.getvalue(), height=400)


# Check if the user has clicked any conversion button and there are images to process
if (st.session_state.plain_text_convert or st.session_state.markdown_convert or st.session_state.latex_convert) and st.session_state.images:
    # Process the uploaded file
    process_file()
    st.session_state.plain_text_convert = False
    st.session_state.markdown_convert = False
    st.session_state.latex_convert = False

# Container for displaying the result and input boxes
st.subheader("Conversion Result")
st.session_state.result_box = st.text_area("Converted file", value=st.session_state.output, height=400)

# Display the enhanced text and save changes button
left, right = st.columns(2)
with left:
    st.session_state.enhanced_button = st.button("Enhance Text")
with right:
    st.button("Save changes")

# Display the input and enhanced text boxes
left_column, right_column = st.columns(2)
with left_column:
    st.session_state.input_box = st.text_area("Text to enhance", height=400)
    # Check if the user has clicked the "Enhance Text" button
    if st.session_state.enhanced_button:
        # Get the enhanced text prompt based on the selected format and input text
        try:
            st.session_state.enhanced_text = get_gemini_response( \
                get_echanced_text_prompt(st.session_state.format_selected, st.session_state.input_box), \
                [{"mime_type": "image/png", "data": st.session_state.images[get_image_index(st.session_state.input_box)]}])
        except Exception as e:
            st.error("No images have been uploaded")
        st.session_state.enhanced_button = False
with right_column:
    st.text_area("Enhanced text", value=st.session_state.enhanced_text, height=400, disabled=True)

# Download button for the transcription
st.download_button(
    label="Download Transcription",
    data=st.session_state.result_box,
    file_name="transcription.tex" if st.session_state.format_selected == "LaTeX" else "transcription.txt" if st.session_state.format_selected == "Plain Text" else "transcription.md",
    mime="application/x-tex" if st.session_state.format_selected == "LaTeX" else "text/plain" if st.session_state.format_selected == "Plain Text" else "text/markdown"
)
st.write("Save changes made to the transcription before downloading it!")