import streamlit as st
import duckdb
from datetime import date
import pandas as pd
import time
from utils import updateDB

# --- Functions ---

# Reset session state
def resetSession():
    # Delete all the items in Session state
    for key in st.session_state.keys():
        del st.session_state[key]
    # Restore initial page setting (offerta_form)
    st.rerun()

# --- Main code ---
st.set_page_config(page_title="Modifica", layout="centered")
st.title("🛠 Modifica i Dati nel Database")
st.subheader("🔍 Cerca un'offerta")

db_path = "../Database/contoTerzi.duckdb"
#DATE_COLUMN = "data_offerta"

if "ex" not in st.session_state:
    st.session_state.ex = pd.DataFrame()

if "offertaLoaded" not in st.session_state:
    st.session_state.offertaLoaded = pd.DataFrame()

# Campi per filtrare le offerte (almeno uno va inserito)
col1, col2 = st.columns(2)

with col1:
    #st.header("Col 1")
    data_offerta = st.date_input("Data Offerta", value=None) # or year, month, day separately?
    agente = st.text_input("Agente")
    referente_commerciale_interno = st.text_input("Referente Commerciale Interno")

with col2:
    #st.header("Col 2")
    nome_cliente = st.text_input("Nome Cliente")
    nazione = st.text_input("Nazione")
    regione = st.text_input("Regione")

# --- Build WHERE clause dynamically ---
# Build filters
filters = []
params = []

if data_offerta:
    filters.append("offerta.data_offerta = ?")
    params.append(str(data_offerta))
if agente:
    filters.append("sales.agente = ?")
    params.append(agente)
if referente_commerciale_interno:
    filters.append("sales.referente_commerciale_interno = ?")
    params.append(referente_commerciale_interno)
if nome_cliente:
    filters.append("cliente.cliente = ?")
    params.append(nome_cliente)
if nazione:
    filters.append("cliente.nazione = ?")
    params.append(nazione)
if regione:
    filters.append("cliente.regione = ?")
    params.append(regione)

where_clause = "WHERE " + " AND ".join(filters) if filters else ""

# Search button: Disable/Enable button dynamically
search_button = st.button("Cerca", use_container_width=True, disabled=len(filters) == 0)

# --- Build query ---
query = f"""
    SELECT offerta.*, cliente.*, lavorazione.*, sales.*, pezzo.*
    FROM offerta
    LEFT JOIN cliente ON offerta.cliente_id = cliente.cliente_id
    LEFT JOIN sales ON sales.sales_id = offerta.sales_id
    LEFT JOIN lavorazione ON lavorazione.lavorazione_id = offerta.lavorazione_id
    LEFT JOIN pezzo ON pezzo.lavorazione_id = lavorazione.lavorazione_id
    
    {where_clause}
    ORDER BY offerta.data_offerta DESC
    LIMIT 100
"""

# --- Query Execution ---
# Query 1: look in the DB
if search_button:
    try:
        with duckdb.connect(db_path, read_only=True) as con:
            df = con.execute(query, params).fetchdf()

        if df.empty:
            st.warning("🔍 Nessun risultato trovato con questi criteri.")
        else:
            st.success(f"✅ Trovate {len(df)} righe.")
            # Exclude columns whose name includes 'id' but not offerta_id
            to_exclude = ["sales_id","cliente_id","lavorazione_id","pezzo_id"]
            st.session_state.ex = df[[col for col in df.columns if "id" not in col or "offerta" in col]]
            #st.dataframe(st.session_state.ex)

    except Exception as e:
        st.error(f"❌ Errore nella query: {e}")
        st.text(f"Query generata:\n{query}\nParams:\n{params}")

if not st.session_state.ex.empty:
    st.dataframe(st.session_state.ex)
    # Now, insert offerta_id to select the record to modify
    offerta_id = st.text_input("ID dell'offerta", placeholder="Inserisci l'ID dell'offerta per modificarla")

    # Query 2: modify
    # Step 2: Button to retrieve the record
    if st.button("Carica Offerta"):
        
        with duckdb.connect(db_path, read_only=True) as con:
            query = """
                SELECT offerta_id, data_offerta, costo_no_iva, stato, attrezzaggio_già_incluso_nel_totale_no_iva
                FROM offerta
                WHERE offerta_id = ?
            """
            df = con.execute(query, [offerta_id]).fetchdf()

        if df.empty:
            st.warning("❌ Nessuna offerta trovata con questo ID.")
        else:
            st.success("✅ Offerta trovata! Modifica i campi qui sotto.")
            st.session_state.offertaLoaded = df

if not st.session_state.offertaLoaded.empty:

    df = st.session_state.offertaLoaded
    df.loc[:,"data_offerta"] = pd.to_datetime(df.loc[:,"data_offerta"]) #cast to datetime
    edited_df = st.data_editor(
        df,
        num_rows="fixed",
        use_container_width=True,
        key="edit_offerta",
        column_config={
        "offerta_id":st.column_config.Column(disabled=True),
        "data_offerta":st.column_config.DateColumn(),
        "stato":st.column_config.SelectboxColumn(options=["Aperta", "Persa", "In Arrivo", "In Lavorazione", "Ordine", "Comparativa", "Altro"])}
    )

    # Compare and update
    save, reset, _ = st.columns([6,6,7])
    with save:
        if st.button("Salva modifiche"):
            with st.spinner("Salvataggio...", show_time=True):
                time.sleep(5)
                updateDB(df, edited_df, offerta_id)

    with reset:
        if st.button("Reset Session"):
            with st.spinner("Resetting session...", show_time=True):
                time.sleep(5)
                resetSession()

# Note:
# 1. Aggiungere opzione per cercare in base a offerta_id
# 2. Usare più funzioni? Una classe?
# 3. aggiungere le colonne che l'utente potrebbe voler modificare (con relative JOIN); 
#    metterle poi nel column_config del st.data_editor; 
#    aggiungere validazione dell'input (forse già eseguita dagli oggetti st.column_config.InputObject() come SelectboxColumn)
