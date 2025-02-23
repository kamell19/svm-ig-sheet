import joblib
import pandas as pd
import numpy as np
import math
from textblob import Word
from sklearn.preprocessing import StandardScaler
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Load the trained model
svm_model = joblib.load('svmig_model.pkl')
scaler = joblib.load('scaler.pkl')  # Load StandardScaler
vocab = joblib.load('tfidf_vocab.pkl')  # Load vocabulary
# Load selected features based on IG
selected_features = joblib.load('selected_features.pkl')

# Google Sheets Authentication
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name('skripsi19-451508-4a42a85c8fb5.json', scope)
client = gspread.authorize(creds)

# Open the Google Sheet by URL
sheet = client.open_by_key("1uehUBPr3x3ek0sJC5-C1ee_InfRoj1yh")
worksheet = sheet.get_worksheet(0)

# Load data from Google Sheets into a pandas DataFrame
data = worksheet.get_all_records()
df = pd.DataFrame(data)

# Function to clean text
def clean_text(text):
    if pd.isna(text):  # Handle NaN
        return ''
    words = text.split()
    words = [word for word in words if not word.startswith(('http', '@', '#'))]
    text = ' '.join(words)
    text = ''.join(char if char.isalpha() or char.isspace()
                   else ' ' for char in text)
    text = ' '.join(text.split())
    return text.lower()

# Tokenization function
def tokenization(text):
    return text.split()


# Stopword removal
stop_words = {
    'and', 'or', 'but', 'so', 'because', 'if', 'while', 'with', 'at', 'by',
    'for', 'to', 'of', 'in', 'on', 'a', 'an', 'the', 'is', 'it', 'this',
    'that', 'these', 'those', 'i', 'we', 'you', 'he', 'she', 'they', 'me',
    'him', 'her', 'them', 'my', 'our', 'your', 'his', 'their', 'its', 'be',
    'am', 'are', 'was', 'were', 'been', 'can', 'will', 'would', 'could',
    'should', 'do', 'did', 'does', 'have', 'has', 'had'
}


def remove_stopwords(token_list):
    return [word for word in token_list if word.lower() not in stop_words]

# Lemmatization


def lemmatize_text(tokens):
    return [Word(word).lemmatize() for word in tokens]

# Function to preprocess review text


def preprocess_review(review):
    cleaned = clean_text(review)
    tokens = tokenization(cleaned)
    tokens = remove_stopwords(tokens)
    lemmatized = lemmatize_text(tokens)
    return lemmatized

# Function to predict the review sentiment


def svm_predict(text):
    preprocessed_text = preprocess_review(text)

    # Gunakan vocabulary yang sama dari training
    text_tfidf = np.zeros((1, len(vocab)))
    for term in preprocessed_text:
        if term in vocab:
            idx = vocab.index(term)
            text_tfidf[0, idx] = 1  # Menggunakan frekuensi biner

    # Hanya pilih fitur yang dipilih saat training (berdasarkan Information Gain)
    reduced_text_tfidf = text_tfidf[:, [vocab.index(
        f) for f in selected_features if f in vocab]]

    # Pastikan jumlah fitur setelah seleksi sesuai dengan training
    if reduced_text_tfidf.shape[1] != len(selected_features):
        raise ValueError(
            f"Jumlah fitur prediksi ({reduced_text_tfidf.shape[1]}) tidak sesuai dengan jumlah fitur training ({len(selected_features)})")

    # Standardisasi menggunakan scaler yang sama
    text_tfidf_scaled = scaler.transform(reduced_text_tfidf)

    # Prediksi menggunakan model SVM
    prediction = svm_model.predict(text_tfidf_scaled)[0]
    return prediction

# Function to retrieve list of drugs
def get_all_drugs():
    return sorted(df['urlDrugName'].dropna().unique())

# Function to retrieve drug side effects
def get_drug_info(drug_name):
    filtered_df = df[df["urlDrugName"].str.contains(
        drug_name, case=False, na=False)]
    return filtered_df[["urlDrugName", "condition", "sideEffects", "sideEffectsReview", "commentsReview"]]

# Function to add new drug data to Google Sheets
def add_new_drug_data(urlDrugName, condition, sideEffects, sideEffectsReview, commentsReview):
    # Add new row of drug data to the sheet
    new_data = [urlDrugName, condition, sideEffects, sideEffectsReview, commentsReview]
    worksheet.append_row(new_data)
    return "Drug data added successfully!"
