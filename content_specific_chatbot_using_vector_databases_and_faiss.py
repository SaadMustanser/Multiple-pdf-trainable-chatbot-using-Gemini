# -*- coding: utf-8 -*-
"""Content Specific Chatbot using Vector Databases and FAISS.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1f1vKyITE1dci4m4lA4HXbc8jZxzefgwM
"""

from google.colab import drive
drive.mount('/content/drive')

!pip install -q PyMuPDF sentence-transformers faiss-cpu

import fitz  # PyMuPDF
import os
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

# Initialize the SentenceTransformer model
embedder = SentenceTransformer('paraphrase-MiniLM-L6-v2')

# Function to embed text in batches
def embed_pdfs_in_batches(pdf_files, batch_size=50):
    all_chunks = []
    all_chunk_embeddings = []

    for i in range(0, len(pdf_files), batch_size):
        batch_files = pdf_files[i:i + batch_size]
        batch_chunks = []

        for pdf_file in batch_files:
            doc = fitz.open(pdf_file)
            for page in doc:
                text = page.get_text()
                if text.strip():
                    batch_chunks.append(text)

        batch_embeddings = embedder.encode(batch_chunks, convert_to_tensor=True)
        all_chunks.extend(batch_chunks)
        all_chunk_embeddings.append(np.array(batch_embeddings))

    return all_chunks, np.vstack(all_chunk_embeddings)

# Define the directory where your PDFs are stored
pdf_directory = "/content/drive/MyDrive/BooksandResume"

# List all PDF files in the directory
pdf_files = [os.path.join(pdf_directory, f) for f in os.listdir(pdf_directory) if f.endswith('.pdf')]

# Process all PDFs in batches
all_chunks, all_chunk_embeddings = embed_pdfs_in_batches(pdf_files, batch_size=50)

for word, embedding in zip(all_words, all_word_embeddings):
    print(f"Word: {word}\nEmbedding: {embedding}\n")

# Initialize FAISS index
d = all_chunk_embeddings.shape[1]  # Dimension of embeddings
index = faiss.IndexFlatL2(d)
index.add(all_chunk_embeddings)

!pip install -q -U google-generativeai



import google.generativeai as genai
import textwrap
from IPython.display import display, Markdown
from google.colab import userdata

def to_markdown(text):
    text = text.replace('•', '  *')
    return Markdown(textwrap.indent(text, '> ', predicate=lambda _: True))

# Used to securely store your API key
GOOGLE_API_KEY = userdata.get('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)

# Select the model
model_name = 'gemini-1.5-flash'
model = genai.GenerativeModel(model_name)

def get_gemini_response(prompt, context):
    try:
        combined_prompt = f"Context:\n{context}\n\nQuestion:\n{prompt}"
        response = model.generate_content(combined_prompt)
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

def retrieve_relevant_chunks(query, k=5):
    query_embedding = embedder.encode([query], convert_to_tensor=True)
    query_embedding = np.array(query_embedding)
    #print(query_embedding).shape

    distances, indices = index.search(query_embedding, k)
    relevant_chunks = [all_chunks[idx] for idx in indices[0]]

    return relevant_chunks

def chat():
    print("Chatbot: Hello! How can I help you today?")
    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            print("Chatbot: Goodbye!")
            break
        # Retrieve relevant chunks
        relevant_chunks = retrieve_relevant_chunks(user_input)
        #print(relevant_chunks)
        context = "\n\n".join(relevant_chunks)
        # Generate response from the model using the PDF context
        response_text = get_gemini_response(user_input, context)
        display(to_markdown(response_text))

if __name__ == "__main__":
    chat()

