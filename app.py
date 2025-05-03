import streamlit as st
import random
import os
import time
import base64
from dotenv import load_dotenv

# Importa le funzioni personalizzate
from utils.templates import modify_template
from models.optimizer import extract_cv_data, optimize_cv_fields
from utils.cv_parser import read_pdf
from utils.job_parser import input_job_description
from utils.gemini_matcher import get_matching_score

#Impostazione colore dello spinner
st.markdown("""
    <style>
        .stSpinner > div > div {
            color: salmon !important;
        }
    </style>
""", unsafe_allow_html=True)

# Caricare l'immagine locale
image_path = "assets/transparent_logo.png"  # <-- il tuo file immagine

# Funzione per convertire l'immagine in base64
def get_base64_of_bin_file(file_path):
    with open(file_path, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

# Ottieni l'immagine codificata in base64
img_base64 = get_base64_of_bin_file(image_path)

# Leggi la query string per sapere su che pagina sei
query_params = st.query_params
page = query_params.get("page", "home")

# Stile CSS per l'effetto hover
st.markdown("""
    <style>
    .logo-hover {
        transition: transform 0.4s ease;
        cursor: pointer;
    }
    .logo-hover:hover {
        transform: scale(1.1);
    }
    </style>
""", unsafe_allow_html=True)

# Mostrare il logo cliccabile che cambia pagina interna
if page == "home":
    st.markdown(f'''
        <a href="?page=team" title="Clicca per conoscere il team!">
            <img class="logo-hover" src="data:image/png;base64,{img_base64}" width="230" />
        </a>
    ''', unsafe_allow_html=True)

# Funzione per impostare sfondo + migliorare leggibilità
def set_background(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
    background_style = f"""
    <style>
    .stApp {{
        background-image: url("data:image/jpg;base64,{encoded_string}");
        background-size: cover;
        background-attachment: fixed;
        background-position: center;
        background-repeat: no-repeat;
        background-color: #ffffff;
    }}

    /* Migliora leggibilità dei contenuti */
    header, footer, .css-18e3th9, .css-1d391kg {{
        background-color: rgba(255, 255, 255, 0.8); /* bianco semi-trasparente */
        color: #000000; /* testo nero */
    }}
    </style>
    """
    st.markdown(background_style, unsafe_allow_html=True)


# Imposta lo sfondo
set_background("assets/sfondo.jpg")

# Se siamo sulla pagina "team", mostra il Team
if page == "team":
    # Crea due colonne
    col1, col2 = st.columns([2, 5])  # Puoi cambiare i numeri per regolare le proporzioni

    # Nella prima colonna metti l'immagine
    with col1:
        st.image("assets/transparent_logo.png")                 

    # Nella seconda colonna metti il titolo
    with col2:    
        st.markdown(
            """
            <div style="height:150px; display:flex; align-items:center; margin-left: -40px;">
                <h1 style="margin:5;">Il Nostro Team</h1>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    st.image("assets/Immagine_CV_gruppo.jpeg")  # Mostra l'immagine del team
    st.subheader("Conosci chi ha creato CV Optimizer!")

    team_members = [
        {"name": "Katia Cannata", "role": "Creative Problem solver", "bio": "La donna dalle mille soluzioni."},
        {"name": "Alessandro Greco", "role": "Pacificatore", "bio": "Gestione conflitti e spacciatore di chiavi API."},
        {"name": "Giorgia Vitanza", "role": "Front woman", "bio": "Gestore versionamento github e guida spirituale del team."},
        {"name": "Giulia Scarfia", "role": "Motivatrice", "bio": "La nostra addetta alla grafica e al pensiero positivo."},
        {"name": "Erica Cutuli", "role": "Guardia svizzera", "bio": "Specialista in puntualizzazioni e correzioni non richieste."}
    ]
    
    for member in team_members:
        # Prima lettera separata
        first_letter = member['name'][0]
        rest_of_text = member['name'][1:]

        # Creazione dell'HTML con formattazione
        styled_text = f"""
        <h1 style="font-size: 40px;">
            <span style="color: #FF5733; font-weight: bold;">{first_letter}</span>{rest_of_text}
        </h1>
        """

            # Mostra il testo usando componenti HTML
        st.markdown(styled_text, unsafe_allow_html=True)
        
        st.markdown(f"**Ruolo:** {member['role']}")
        st.markdown(f"*{member['bio']}*")
        

    st.stop()  # Ferma l'esecuzione per non eseguire il resto

# Carica variabili d’ambiente
load_dotenv("api.env")
api_keys = [v for k, v in st.secrets.items() if k.startswith("API_KEY_")]
if not api_keys:
    raise ValueError("Nessuna chiave API_KEY_X trovata nei secrets")
api_key = random.choice(api_keys)

# Verifica che la chiave API sia presente
if api_key is None:
    st.error("API_KEY non trovata nel file api.env. Verifica il file.")

# Inizializzazione dello stato della sessione
if 'cv_json' not in st.session_state:
    st.session_state.cv_json = None
if 'cv_analyzed' not in st.session_state:
    st.session_state.cv_analyzed = False
if 'overall_match' not in st.session_state:
    st.session_state.overall_match = 0

# Frasi motivazionali
motivational_sentences = [
    "*🎯 Ogni CV è un passo verso il tuo sogno!*",
    "*🚀 Sii audace, il lavoro giusto ti sta aspettando!*",
    "*💼 Ogni dettaglio del tuo CV parla di te: rendilo memorabile.*",
    "*🧠 Talento e preparazione si incontrano in un CV perfetto.*",
    "*🌟 Il tuo futuro inizia con una buona presentazione di te stesso!*",
    "*🤖 Il tuo CV sta per evolversi con l’aiuto dell’AI!*",
    "*🛠️ Stiamo plasmando il tuo profilo con precisione algoritmica.*",
    "*📡 CV in fase di upgrade: segnale ottimo per il futuro!*"
]

st.title("📝 CV Optimizer")
st.subheader("Il tuo alleato per creare un curriculum perfetto, per il lavoro dei tuoi sogni!")

st.markdown(f"#### {random.choice(motivational_sentences)}")

# Istruzioni
st.markdown("### 📌 Come funziona?")
st.markdown(""" 
1. **Carica il tuo CV** in formato PDF.  
2. **Inserisci l'annuncio di lavoro** tramite testo o link da LinkedIn.  
3. **Analizza** la compatibilità tra il tuo profilo e l'annuncio.  
4. **Ottimizza** il CV e **scaricalo** pronto per la candidatura!
""")

st.info("⚠️ **IMPORTANTE** L'IA può commettere errori. Verifica sempre il tuo CV finale!")

# Caricamento file
st.session_state.uploaded_cv = st.file_uploader("📄 Carica il tuo CV", type=["PDF"])

text = ""
if st.session_state.uploaded_cv:
    text = read_pdf(st.session_state.uploaded_cv)
    st.session_state.uploaded_cv = True

# Inserimento descrizione lavoro
job_description = input_job_description()

col1, col2 = st.columns(2)

with col1:
    if st.button("🔍 Verifica compatibilità tra CV e annuncio") and st.session_state.uploaded_cv:
        if not text.strip():
            st.error("Il file caricato sembra vuoto.")
        else:
            with st.spinner("📊 Elaborazione in corso..."):
                st.session_state.cv_json = extract_cv_data(text)
                overall_match = get_matching_score(text, job_description)
                st.session_state.overall_match = overall_match
                if overall_match >= 0 and overall_match < 0.4:
                    st.warning("⚠️ CV poco adatto per questa posizione. Sconsigliamo di avviare l'ottimizzazione per questo annuncio.")
                else:
                    st.success(f"✅ Buona compatibilità tra CV e annuncio! Puoi procedere con l'ottimizzazione.")

                st.session_state.cv_analyzed = True

with col2:
    if st.session_state.cv_analyzed and st.session_state.uploaded_cv:
        if st.button("🚀 Ottimizza CV", type="primary"):
            if not job_description:
                st.error("Inserisci la descrizione della posizione lavorativa.")
            else:
                with st.spinner("✍️ Ottimizzazione in corso..."):
                    optimized_cv = optimize_cv_fields(st.session_state.cv_json, job_description)
                    progress_bar = st.progress(0)
                    for i in range(1, 101):
                        time.sleep(0.05)
                        progress_bar.progress(i)
                    format = modify_template(optimized_cv)
                    time.sleep(1)

                if isinstance(format, bytes):
                    st.success("✅ CV Ottimizzato!")
                    st.download_button(
                        "📥 Scarica CV Ottimizzato",
                        data=format,
                        file_name="CV_Ottimizzato.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
                    st.session_state.cv_analyzed = False
                    st.session_state.cv_json = None
                    st.session_state.overall_match = 0
                    st.session_state.uploaded_cv = None
                else:
                    st.error(format)
    else:
        st.warning("⚠️ Verifica compatibilità tra CV e annuncio di lavoro prima di ottimizzarlo.")
