import google.generativeai as genai
import logging
import os
from dotenv import load_dotenv
import random

# Carica variabili d'ambiente
load_dotenv("api.env")

try:
    # Estrai tutte le chiavi che iniziano con API_KEY_
    api_keys = [v for k, v in os.environ.items() if k.startswith("API_KEY_")]

    if not api_keys:
        raise RuntimeError("🚫 Nessuna chiave API disponibile nel file .env o nei secrets di Streamlit.")

    # Seleziona una chiave a caso
    api_key = random.choice(api_keys)
    print(f"Chiave API selezionata: {api_key[:8]}...")  # debug non visibile in Streamlit, solo log console

    # Configura Gemini
    genai.configure(api_key=api_key)

except RuntimeError as e:
    st.error("⚠️ Tutte le chiavi API sono esaurite o assenti.")
    st.warning("Il sistema ha raggiunto il limite massimo di richieste. Riprova più tardi o contatta l’amministratore.")
    st.stop()

except Exception as e:
    st.error("❌ Errore imprevisto nella configurazione delle API Gemini.")
    st.exception(e)
    st.stop()

def get_matching_score(cv_text: str, job_description: str) -> float:
    """
    Invia il testo del CV e dell'annuncio di lavoro a Gemini e restituisce uno score di compatibilità.
    
    cv_text: Il testo del curriculum vitae.
    job_description: Il testo dell'annuncio di lavoro.
    
    Restituisce uno score di compatibilità tra 0 e 1 come float.
    """
    try:
        # Creazione del prompt per Gemini
        prompt = f"""
        Dato il seguente curriculum vitae e descrizione del lavoro, restituisci esclusivamente uno score di compatibilità tra 0 e 1, senza alcuna altra parola o descrizione.

        Curriculum Vitae:
        {cv_text}

        Descrizione del Lavoro:
        {job_description}
        """

        # Chiamata a Gemini per generare il contenuto
        response = genai.GenerativeModel("gemini-1.5-pro").generate_content(prompt)

        # Estrazione dello score dalla risposta (assumiamo che sia solo un numero)
        score = response.text.strip()

        # Verifica che la risposta sia un numero e converti a float
        try:
            score = float(score)
        except ValueError:
            raise ValueError(f"Impossibile convertire la risposta in numero: {score}")

        return score

    except Exception as e:
        logging.error(f"Errore durante la richiesta a Gemini: {e}")
        return 0.0  # Restituisce uno score di 0 in caso di errore
