import streamlit as st
import os
from PIL import Image
import google.generativeai as genai
from dotenv import load_dotenv
import fitz  # PyMuPDF
import markdown
from markdownify import markdownify as md
from concurrent.futures import ThreadPoolExecutor, as_completed
import re

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
def format_as_latex(content):
    latex_template = r'''
    % Document type. Using twoside implies that chapters always start on the first page to the left, possibly leaving a blank page in the previous chapter. 
        \documentclass[a4paper, openright]{{report}}

        % Margin dimensions
        \usepackage[a4paper,top=3cm,bottom=3cm,left=3cm,right=3cm]{{geometry}} 
        % Font size
        \usepackage[fontsize=13pt]{{scrextend}}
        % Text language
        \usepackage[english,italian]{{babel}}
        % Bibliography language
        \usepackage[fixlanguage]{{babelbib}}
        % Text encoding
        \usepackage[utf8]{{inputenc}} 
        % Text encoding
        \usepackage[T1]{{fontenc}}
        % Generates dummy text. Useful 
        % to understand how the 
        % text would be formatted on 
        % the page before writing a paragraph
        \usepackage{{lipsum}}
        % Rotate images
        \usepackage{{rotating}}
        % Modify page headers 
        \usepackage{{fancyhdr}}               

        % Mathematical libraries
        \usepackage{{amssymb}}
        \usepackage{{amsmath}}
        \usepackage{{amsthm}}         

        % Use of images
        \usepackage{{graphicx}}
        \usepackage{{subcaption}}
        % Use of colors
        \usepackage[dvipsnames]{{xcolor}}         
        % Use of code listings
        \usepackage{{listings}}          
        % Insert hyperlinks between various text elements 
        \usepackage{{hyperref}}     
        % Various types of underlining
        \usepackage[normalem]{{ulem}}

        % Hide title
        \usepackage{{titlesec}}

        \usepackage{{array}}

        % -----------------------------------------------------------------

        % Modify header style
        \pagestyle{{fancy}}
        \fancyhf{{}}
        \lhead{{\rightmark}}
        \rhead{{\textbf{{\thepage}}}}
        \fancyfoot{{}}
        \setlength{{\headheight}}{{15.6pt}}

        % Remove page number at chapter beginnings
        \fancypagestyle{{plain}}{{ 
        \fancyfoot{{}}
        \fancyhead{{}}
        \renewcommand{{\headrulewidth}}{{0pt}}
        }}
        
        % Code style
        \lstdefinestyle{{codeStyle}}{{ 
            % Comment color
            commentstyle=\color{{teal}},
            % Keyword color
            keywordstyle=\color{{Magenta}},
            % Line number style
            numberstyle=\tiny\color{{gray}},
            % String color
            stringstyle=\color{{violet}},
            % Text size and style
            basicstyle=\ttfamily\footnotesize,
            % newline only at whitespace
            breakatwhitespace=false,     
            % newline yes/no
            breaklines=true,                 
            % Caption position, top/bottom 
            captionpos=b,                    
            % Preserve spaces in code, useful for indentation
            keepspaces=true,                 
            % Where to display line numbers
            numbers=left,                    
            % Distance between line numbers and code
            numbersep=5pt,                  
            % Show spaces or not
            showspaces=false,                
            % Show spaces within strings
            showstringspaces=false,
            % Show tabs
            showtabs=false,
            % Tab size
            tabsize=2
        }} \lstset{{style=codeStyle}}

        % Code style for larger blocks, where smaller text is needed (e.g., inserting code with very long lines). To use this style instead of the previous one, use 

        % \lstset{{style=longBlock}}
        %  % insert code...
        % \lstset{{style=codeStyle}}

        % The second command allows you to return to the previous style 
        \lstdefinestyle{{longBlock}}{{ 
            commentstyle=\color{{teal}},
            keywordstyle=\color{{Magenta}},
            numberstyle=\tiny\color{{gray}},
            stringstyle=\color{{violet}},
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
        }} \lstset{{style=codeStyle}}

        % Uncommenting the following command includes sources from Bibliography.bib that are not directly cited with the \cite command
        % \nocite{{*}}

        % Margins before and after code blocks, for more spacing
        \lstset{{aboveskip=20pt,belowskip=20pt}}

        % Change reference colors
        \definecolor{{mycolor}}{{RGB}}{{0, 112, 192}}
        \hypersetup{{ 
            colorlinks,
            linkcolor=mycolor,
            citecolor=mycolor
        }}

        % Added definitions, theorems, line, and listings
        \newtheorem{{definition}}{{Definition}}[section]
        \newtheorem{{theorem}}{{Theorem}}[section]
        \providecommand*\definitionautorefname{{Definition}}
        \providecommand*\theoremautorefname{{Theorem}}
        \providecommand*\listingautorefname{{Listing}}
        \providecommand*\lstnumberautorefname{{Line}}

        \raggedbottom

        % -----------------------------------------------------------------
        \begin{{document}}
        \tableofcontents
        \setcounter{{chapter}}{{0}}
        {content}
        \end{{document}}
    '''
    # Add the content to the template
    return latex_template.format(content=content)


def process_result(result):
    # Usa una regex per estrarre il contenuto tra \begin{document} e \end{document}
    content = re.search(r'\\begin{document}(.*?)\\end{document}', result, re.DOTALL)
    if content:
        return content.group(1).strip()
    else:
        return result

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

def get_custom_prompt(format):
    base_prompt = '''
        You have to transcribe the handwritten notes in the image. 
        The system should accurately recognize 
        and transcribe the text displayed in the image '''
    if format == "Markdown":
        return f'''{base_prompt}
            in Markdown format. 
            The output should contain structured text with title, chapters, paragraphs, subparagraphs, and so on.
        '''
    elif format == "Plain Text":
        return f'''{base_prompt} 
            as plain text.
        '''
    elif format == "LaTeX":
        template = f'''{base_prompt}
            in LaTeX format. 
            The output should contain structured text with chapters, sections, subsections, paragraphs, subparagraphs.
            THe output can contain tables, figures, and equations.
            The output should not include images.
            The output should not include any references to additional files.
        '''
        return template
    else:
        return base_prompt


input_prompt = get_custom_prompt(output_format)
if submit and images:
    # Prepara i dati per le chiamate parallele
    tasks = {}
    with ThreadPoolExecutor(max_workers=len(images)) as executor:
        for i, image_data in enumerate(images):
            image_parts = [{"mime_type": "image/png", "data": image_data}]
            # Programma l'esecuzione della funzione e memorizza l'oggetto Future
            task = executor.submit(get_gemini_response, get_custom_prompt(output_format), image_parts, input)
            tasks[i] = task

    # Recupera i risultati in modo asincrono mantenendo l'ordine
    all_responses = [None] * len(images)  # Crea una lista con la lunghezza delle immagini
    for i in tasks:
        future = tasks[i]
        result = future.result()
        all_responses[i] = process_result(result)  # Memorizza il risultato nella posizione corretta

    output = "\n\n".join(all_responses)

    if output_format == "LaTeX":
        formatted_output = format_as_latex(output)
    else:
        formatted_output = output
    
    st.subheader("Transcription report: ")
    st.write(formatted_output)
    
    st.download_button(
        label="Download Transcription",
        data=formatted_output,
        file_name="transcription.tex" if output_format == "LaTeX" else "transcription.txt" if output_format == "Plain Text" else "transcription.md",
        mime="application/x-tex" if output_format == "LaTeX" else "text/plain" if output_format == "Plain Text" else "text/markdown"
    )
