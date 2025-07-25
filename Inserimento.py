import streamlit as st
from datetime import date, datetime
import time
import pandas as pd
from utils import readOfferta, readPezzo, insertIntoDB

# --- Functions ---
## Missing fields check
def areFieldsMissing(fieldsToCheck: dict):
    missing_fields = []
    for name, value in fieldsToCheck.items():
        if value is None or (isinstance(value, str) and value.strip() == "") \
        or isinstance(value, float) and value == 0 or isinstance(value, int) and value == 0:
            missing_fields.append(name.replace("_", " ").capitalize())
    return missing_fields

## Valid time check
def is_valid_time(time_str):
    try:
        hours, minutes = map(int, time_str.split(":"))
        return hours >= 0 and 0 <= minutes < 60
    except:
        return False

# Reset session state
def resetSession():
    # Delete all the items in Session state
    for key in st.session_state.keys():
        del st.session_state[key]
    # Restore initial page setting (offerta_form)
    st.rerun()

# --- Main code ---

if "offertaForm_isSubmitted" not in st.session_state:
    st.session_state.offertaForm_isSubmitted = False

if "offertaFeatures" not in st.session_state:
    st.session_state.offertaFeatures = dict() # dict con le features dell'offerta

if "pezzoFeatures" not in st.session_state:
    st.session_state.pezzoFeatures = dict() # dict con le features del pezzo

if "numero_pezzi" not in st.session_state:
    st.session_state.numero_pezzi = 0

if "pezzo_corrente" not in st.session_state:
    st.session_state.pezzo_corrente = 0

if "pezzi_list" not in st.session_state:
    st.session_state.pezzi_list = list() # lista di dizionari, ognuno un pezzo con le sue features


st.set_page_config(page_title="Offerta Entry Dashboard", layout="centered")
st.title("📋 Inserimento Offerta")

st.markdown("---")

# Se il form non è stato compilato
if not st.session_state.offertaForm_isSubmitted:

    # Form Offerta
    with st.form("offerta_form"):
        st.subheader("Inserimento Nuova Offerta")
        # st.input objects are in a utils.py function for clarity
        st.session_state.offertaFeatures = readOfferta()

        # Submit form
        submitted = st.form_submit_button("📤 Insert Offerta")

        # Se il form è "inviato" (button clicked) allora controlla i dati inseriti
        if submitted:
            missing_fields = areFieldsMissing(st.session_state.offertaFeatures)

            durata_effettiva = st.session_state.offertaFeatures.get("durata_effettiva")
            durata_da_fatturare = st.session_state.offertaFeatures.get("durata_da_fatturare")
            if durata_effettiva:
                if not is_valid_time(durata_effettiva):
                    missing_fields.append("Durata Effettiva (formato HH:MM)")
            if durata_da_fatturare:
                if not is_valid_time(durata_da_fatturare):
                    missing_fields.append("Durata da Fatturare (formato HH:MM)")

            # Stampa i dati mancanti (if any)
            if missing_fields:
                st.error("Missing or invalid fields: " + ", ".join(missing_fields))
            else:
                st.session_state.offertaForm_isSubmitted = True
                #st.session_state.numero_pezzi = numero_pezzi
                st.rerun()

else:

    st.success(f"✅ Adesso puoi inserire i dati relativi ai pezzi.")
    #st.balloons()
    
    st.title("📋 Inserimento Pezzi")
    st.markdown("---")

    # Check if all pieces are inserted
    if st.session_state.pezzo_corrente < st.session_state.numero_pezzi:

        with st.form(key="pezzo_form"+str(st.session_state.pezzo_corrente)):

            st.subheader(f"Pezzo {st.session_state.pezzo_corrente + 1}/{st.session_state.numero_pezzi}")
            # st.input objects are in a utils.py function for clarity
            st.session_state.pezzoFeatures = readPezzo()

            # Submit form
            submitted = st.form_submit_button("➕ Inserisci Pezzo")

            if submitted:
                missing = areFieldsMissing(st.session_state.pezzoFeatures)

                if missing:
                    st.error("Missing or invalid fields: " + ", ".join(missing))
                else:
                    st.session_state.pezzi_list.append(st.session_state.pezzoFeatures)

                    st.session_state.pezzo_corrente += 1
                    st.rerun()

    else:
        # All data inserted. Print success, show summary
        st.success(f"✅ Hai inserito tutti i {st.session_state.numero_pezzi} pezzi.")
        st.markdown("---")
        st.subheader("🧾 Dati inseriti:")
        df = pd.DataFrame.from_dict(st.session_state.offertaFeatures, orient='index')
        st.write("Offerta", df.T)

        for n in range(st.session_state.numero_pezzi):
            df = pd.DataFrame.from_dict(st.session_state.pezzi_list[n], orient='index')
            st.write(f"Pezzo {n}", df.T)

        #st.write("Offerta", st.session_state.offertaFeatures)
        #st.write("Pezzi", st.session_state.pezzi_list)


        insert, reset, _ = st.columns([6,6,5])

        with insert:
            if st.button("Inserisci offerta nel Database"):
                with st.spinner("Inserimento nel Database...", show_time=True):
                    time.sleep(5)
                    # try-except is already in the function insertIntoDB !
                    try:
                        insertIntoDB(st.session_state.offertaFeatures, st.session_state.pezzi_list)
                        #st.success("Inserita!", icon=":material/check:", width="stretch")
                    except Exception as e:
                        st.error(f"❌ Failed to insert data: {e}")

        with reset:
            if st.button("Reset Session"):
                with st.spinner("Resetting session...", show_time=True):
                    time.sleep(5)
                    resetSession() # try-except?

