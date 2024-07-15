import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from nltk.probability import FreqDist
import string

# Download NLTK resources if not already downloaded
nltk.download('punkt')
nltk.download('stopwords')


def preprocess_text(text):
    # Tokenize the text into words
    tokens = word_tokenize(text.lower())

    # Remove punctuation
    tokens = [token for token in tokens if token not in string.punctuation]

    # Remove stopwords
    stop_words = set(stopwords.words('italian'))  # Assuming Italian language
    tokens = [token for token in tokens if token not in stop_words]

    # Stemming using PorterStemmer
    stemmer = PorterStemmer()
    tokens = [stemmer.stem(token) for token in tokens]

    return tokens


def calculate_jaccard_similarity(file1_path, file2_path):
    # Read the content of both files
    with open(file1_path, 'r', encoding='utf-8') as file1:
        text1 = file1.read()
    with open(file2_path, 'r', encoding='utf-8') as file2:
        text2 = file2.read()

    # Preprocess the texts
    words_text1 = preprocess_text(text1)
    words_text2 = preprocess_text(text2)

    # Convert to sets to find intersection and union
    set1 = set(words_text1)
    set2 = set(words_text2)

    # Calculate Jaccard similarity
    intersection_size = len(set1.intersection(set2))
    union_size = len(set1.union(set2))
    jaccard_similarity = intersection_size / union_size if union_size != 0 else 0

    return jaccard_similarity


if __name__ == '__main__':
    file1_path = "trascizione a mano.md"
    file2_path = "transcription.md"

    jaccard_similarity = calculate_jaccard_similarity(file1_path, file2_path)
    print(f"Jaccard Similarity between {file1_path} and {file2_path}: {jaccard_similarity:.4f}")
