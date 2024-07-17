import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def read_file(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        return file.read()


def calculate_similarity(file1_path, file2_path):
    # Leggi il contenuto dei file
    text1 = read_file(file1_path)
    text2 = read_file(file2_path)

    # Crea un oggetto TfidfVectorizer
    vectorizer = TfidfVectorizer()

    # Trasforma i testi in vettori TF-IDF
    tfidf_matrix = vectorizer.fit_transform([text1, text2])

    # Calcola la similarità coseno tra i due vettori
    cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])

    return cosine_sim[0][0]


# Percorsi dei file .md
file1_path = 'trascizione a mano.md'
file2_path = 'transcription.md'

# Verifica se i file esistono
if os.path.exists(file1_path) and os.path.exists(file2_path):
    similarity = calculate_similarity(file1_path, file2_path)
    print(f"La similarità tra i due file è: {similarity:.2f}")
else:
    print("Uno o entrambi i file non esistono.")
