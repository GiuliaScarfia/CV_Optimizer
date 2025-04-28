from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel
from typing import List, Dict, Any
import os
import json
from dotenv import load_dotenv
import logging

# Carica la chiave API dal file api.env
load_dotenv(dotenv_path="api.env")  # Carica il file api.env

# Ottieni la chiave API dal file .env
google_api_key = os.getenv("API_KEY")  # Modifica per cercare "API_KEY"

# Verifica se la chiave API è stata caricata correttamente
if google_api_key is None:
    raise ValueError("La chiave API non è stata trovata nel file api.env")

# Imposta la chiave API nell'ambiente
os.environ["GOOGLE_API_KEY"] = google_api_key


# ✅ Struttura Pydantic del CV
class TitoloStudio(BaseModel):
    data_conseguimento: str
    nome_istituto: str
    titolo: str
    desc_titolo: str


class EsperienzaLavorativa(BaseModel):
    periodo: str
    qualifica: str
    nome_società: str
    desc_esperienza: str


class CVModel(BaseModel):
    nome: str
    cognome: str
    posizione: str
    telefono: str
    email: str
    sito: str
    città: str
    obiettivo: str
    competenze: str
    lingue: str
    comunicazione: str
    hobby: str
    istruzione: List[TitoloStudio]
    esperienze: List[EsperienzaLavorativa]


# 🔧 Prompt per estrazione dati CV
PROMPT_TEMPLATE = """
Estrai le informazioni rilevanti dal seguente testo del CV e formattale esattamente secondo la struttura JSON richiesta.

– Utilizza i nomi dei campi **esattamente** come mostrato nel template.  
– Se alcuni campi sono assenti nel CV, lasciali come stringhe vuote "" o array vuoti [].  
– Per le sezioni 'Istruzione' ed 'Esperienze', includi **tutti gli entry** presenti nel CV (non solo uno).  
– Non tradurre o modificare i valori trovati nel CV.


Si prega di formattare il risultato come JSON, con questi campi specifici:
- **Nome** (stringa)
- **Cognome** (stringa)
- **Posizione** (stringa)
- **Telefono** (stringa)
- **Email** (stringa)
- **Sito** (stringa)
- **Città** (stringa)
- **Obiettivo** (stringa)
- **Competenze** (stringa)
- **Lingue** (stringa)
- **Comunicazione** (stringa)
- **Hobby** (stringa)
- **Esperienze** (lista di oggetti)
- **Istruzione** (lista di oggetti)

Contenuto del CV: {cv_text}
"""

# 🔧 Prompt per ottimizzazione campi specifici del CV
OPTIMIZE_FIELDS_TEMPLATE = """
Sei un esperto di curriculum e devi ottimizzare alcuni campi specifici del seguente CV per adattarlo alla posizione lavorativa indicata. Utilizza SEMPRE la lingua italiana.

Ecco i dati del CV in formato JSON:
{cv_json}

Ecco la descrizione della posizione lavorativa:
{job_description}

Ottimizza SOLO i seguenti campi, mantenendo invariati tutti gli altri:

1. **Posizione**: Rielabora il campo 'posizione' per riflettere con precisione il titolo della posizione lavorativa, utilizzando un linguaggio professionale e pertinente.
2. **Obiettivo**: Rielabora il campo 'obiettivo' in un testo di 35-50 parole, concentrandoti su come il candidato può soddisfare le esigenze della posizione senza includere nomi di aziende.
3. **Competenze**: Rielabora il campo 'competenze' in un elenco di massimo 5 elementi, selezionando e prioritizzando le competenze più rilevanti per la posizione, mantenendo coerenza e chiarezza.
4. **Lingue**: Rielabora il campo 'lingue' in un elenco di massimo 5 lingue, uniformando in un formato standard (es. "Inglese" anziché "english").
5. **Comunicazione**: Rielabora il campo 'comunicazione' in 40-50 parole, evidenziando le competenze personali più rilevanti per la posizione, utilizzando un linguaggio chiaro e professionale.
6. **Hobby**: Rielabora il campo 'hobby' in massimo 20 parole, descrivendo le passioni e gli interessi del candidato in modo discorsivo e in linea con la posizione.
7. **Esperienze**: Rielabora il campo 'esperienze' in un elenco di massimo 3 esperienze lavorative, mantenendo solo quelle più rilevanti per la posizione.  
   7.1. Uniforma i formati delle date e dei periodi lavorativi per garantire coerenza (es. anno, mese, durata).  
   7.2. Per ogni esperienza lavorativa, modifica la descrizione per renderla più pertinente alla posizione, utilizzando tra 10 e 20 parole per ciascuna.
8. **Istruzione**: Rielabora il campo 'istruzione' in un elenco di massimo 2 titoli di studio, mantenendo solo i più rilevanti per la posizione.  
   8.1. Uniforma i formati delle date per garantire coerenza (es. anno, mese, durata).  
   8.2. Per ogni titolo di studio, modifica la descrizione per renderla più pertinente alla posizione, utilizzando tra 10 e 20 parole.

Restituisci il risultato come un oggetto JSON con gli stessi campi dell'input, modificando SOLO quelli sopra indicati.
"""


# Funzione principale per estrazione dati CV
def extract_cv_data(cv_text: str) -> dict:
    model = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0)
    
    logging.debug(f"Using model: gemini-1.5-pro")

    structured_model = model.with_structured_output(CVModel)
    prompt = PromptTemplate.from_template(PROMPT_TEMPLATE).format(cv_text=cv_text)

    logging.debug("Sending request to model...")
    try:
        cv_model = structured_model.invoke(prompt)
        if cv_model is None:
            raise ValueError("La risposta del modello è None.")
        logging.debug("Successfully received response from model")
        return cv_model.model_dump()
    except Exception as e:
        logging.error(f"Errore durante l'invocazione del modello: {e}")
        logging.info("Tentativo di approccio alternativo...")
        try:
            raw_response = model.invoke(prompt)
            content = raw_response.content
            if "\"json\"" in content:
                json_start = content.find("\"json\"") + 7
                json_end = content.find("\n", json_start)
                json_str = content[json_start:json_end].strip()

            elif "{" in content and "}" in content:
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                json_str = content[json_start:json_end].strip()
            else:
                json_str = content
            dati_json = json.loads(json_str)
            cv_struct = CVModel(**dati_json)
            return cv_struct.model_dump()
        except Exception as e:
            logging.error(f"Errore durante la validazione del JSON (approccio alternativo): {e}")
            return {}


# Funzione per ottimizzare campi specifici del CV
def optimize_cv_fields(cv_data: Dict[str, Any], job_description: str) -> dict:
    model = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0.2)
    logging.info(f"[INFO] Using model: gemini-1.5-pro for field optimization")

    structured_model = model.with_structured_output(CVModel)
    cv_json_str = json.dumps(cv_data, ensure_ascii=False, indent=2)

    prompt = PromptTemplate.from_template(OPTIMIZE_FIELDS_TEMPLATE).format(
        cv_json=cv_json_str,
        job_description=job_description
    )

    logging.info("[INFO] Sending optimization request to model...")
    logging.info(f"\n--- Prompt inviato al modello ---\n{prompt}\n")

    try:
        optimized_cv_model = structured_model.invoke(prompt)

        if optimized_cv_model is None:
            raise ValueError("[ERROR] La risposta del modello è None. Passaggio all'approccio alternativo.")

        logging.info("[✅ SUCCESS] Ottimizzazione completata dal modello strutturato.")
        return optimized_cv_model.model_dump()

    except Exception as e:
        logging.warning(f"[⚠️ WARNING] Errore durante l'ottimizzazione dei campi: {e}")
        logging.info("[INFO] Tentativo di approccio alternativo...")

        try:
            raw_response = model.invoke(prompt)
            content = raw_response.content
            logging.info(f"\n--- Risposta grezza del modello ---\n{content}\n")

            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                json_str = content[json_start:json_end].strip()
            elif "{" in content and "}" in content:
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                json_str = content[json_start:json_end].strip()
            else:
                json_str = content.strip()

            dati_json = json.loads(json_str)
            optimized_cv = CVModel(**dati_json)
            logging.info("[✅ SUCCESS] Approccio alternativo riuscito.")
            return optimized_cv.model_dump()

        except Exception as alt_e:
            logging.error(f"[❌ FALLBACK FAILED] Errore durante la validazione del JSON (approccio alternativo): {alt_e}")
            logging.info("[INFO] Restituzione dei dati originali senza ottimizzazione.")
            return cv_data
