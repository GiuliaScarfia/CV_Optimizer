import streamlit as st
import requests
from bs4 import BeautifulSoup
import re




# --- Job Description Input (Streamlit) ---
def clean_txt(testo):
    clean_text = BeautifulSoup(testo, "lxml").text
    return re.sub(r'\s+', ' ', clean_text).strip()

def download_text_from_url(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return clean_txt(response.text)
    except requests.exceptions.RequestException as e:
        st.error(f"Errore durante il recupero dell'URL: {e}")
        return None


def input_job_description():
    """
    Una sola casella di input: se è un link, scarica il testo; se è testo, lo usa direttamente.
    """

    user_input = st.text_area("👜 Inserisci il testo dell'annuncio o il LINK da LinkedIn:", height=150)

    if user_input:
        if is_link(user_input):
            # Se è un link, scarica il testo
            text = download_text_from_url(user_input)
        else:
            # Altrimenti è testo incollato
            text = user_input
        return text
    return ""

def is_link(text):
    """
    Ritorna True se il testo inserito è un link.
    """
    # Un semplice controllo se il testo è un URL
    return bool(re.match(r'https?://\S+', text))






