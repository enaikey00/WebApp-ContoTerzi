import streamlit as st
from datetime import date, datetime
import duckdb
import uuid

# Set DB path
db_path = "./Database/contoTerzi.duckdb"

def readOfferta():
    #st.subheader("Inserimento Nuova Offerta") # already in Inserimento.py

    st.markdown("### Cliente")
    nome_cliente = st.text_input("Nome Cliente")
    nazione = st.text_input("Nazione")
    regione = st.text_input("Regione")

    st.markdown("---")

    st.markdown("### Sales")
    agente = st.text_input("Agente")
    referente_commerciale_interno = st.text_input("Referente Commerciale Interno")

    st.markdown("---")

    st.markdown("### Lavorazione")
    durata_effettiva = st.text_input("Durata Effettiva (es: 30:00 - 30 ore)")
    durata_da_fatturare = st.text_input("Durata da Fatturare (es: 45:00 - 45 ore)")
    numero_pezzi = st.number_input("Numero di pezzi da inserire successivamente", min_value=0, step=1)

    st.session_state.numero_pezzi = numero_pezzi

    st.markdown("---")

    st.markdown("### Offerta")
    data_offerta = st.date_input("Data Offerta", value=date.today())
    stato = st.multiselect(
        "Stato",
        options=["Aperta", "Persa", "In Arrivo", "In Lavorazione", "Ordine", "Comparativa", "Altro"],
        default=["Aperta"], placeholder="Qual'è lo stato dell'offerta?", max_selections=1,
    )[0] #otherwise it returns a list: [stato]
    tipologia = st.multiselect(
        "Tipologia interna-esterna",
        options=["Interna", "Esterna"],
        default=["Interna"], placeholder="Tipologia interna o esterna", max_selections=1,
    )[0]
    costo_no_iva = st.number_input("Costo No IVA", min_value=0.0, step=0.01)
    costo_con_iva = st.number_input("Costo Con IVA", min_value=0.0, step=0.01)
    attrezzaggio_incluso_nel_totale_no_iva = st.number_input("Attrezzaggio già incluso (No IVA)", min_value=0.0, step=0.01)
    attrezzaggio = st.text_input("Attrezzaggio")
    attr_tipo = st.text_input("Attr. Tipo")


    keys = ["nome_cliente", "nazione", "regione", "agente", "referente_commerciale_interno",
            "durata_effettiva", "durata_da_fatturare", "numero_pezzi", "data_offerta", 
            "stato", "tipologia", "costo_no_iva", "costo_con_iva", 
            "attrezzaggio_incluso_nel_totale_no_iva", "attrezzaggio", "attr_tipo"]
    values = [nome_cliente, nazione, regione, agente, referente_commerciale_interno,
            durata_effettiva, durata_da_fatturare, numero_pezzi, data_offerta, 
            stato, tipologia, costo_no_iva, costo_con_iva, 
            attrezzaggio_incluso_nel_totale_no_iva, attrezzaggio, attr_tipo]
    offertaFeatures = { k:v for (k,v) in zip(keys, values)}

    return offertaFeatures

def readPezzo():

    quantità = st.number_input("Quantità", min_value=0.0, step=1.0, key="quantità_input", value=0.0)
    particolare = st.text_input("Particolare")
    operatore = st.text_input("Operatore")
    peso = st.number_input("Peso", min_value=0.0, step=1.0, value=0.0)
    equilibratura = st.text_input("Equilibratura")
    data_di_lavorazione = st.date_input("Data di lavorazione", value=date.today())
    macchina = st.text_input("Macchina") # multiselect?
    classe = st.text_input("Classe") # multiselect?
    rpm = st.number_input("RPM", min_value=0.0, step=1.0, key="rpm_input", value=0.0)

    # Store variables for later summary
    keys = ["quantità", "particolare", "operatore", "peso", "equilibratura", "data_di_lavorazione", "macchina", "classe", "rpm"]
    values = [quantità, particolare, operatore, peso, equilibratura, data_di_lavorazione, macchina, classe, rpm]
    pezzoFeatures = { k:v for (k,v) in zip(keys, values)}

    return pezzoFeatures

# Insert data into DB
def insertIntoDB(offertaFeatures, pezziList):
    # Set DB path
    #db_path = "../Database/contoTerzi.duckdb"

    # Unpack dictionary for Offerta
    d = offertaFeatures
    keys, values = tuple(d.keys()), tuple(d.values())

    cliente = d.get("nome_cliente") # values[0]
    nazione = d.get("nazione")
    regione = d.get("regione")
    agente = d.get("agente")
    referente_commerciale_interno = d.get("referente_commerciale_interno")
    durata_effettiva = d.get("durata_effettiva")
    durata_da_fatturare = d.get("durata_da_fatturare")
    data_offerta = d.get("data_offerta")
    stato = d.get("stato")
    tipologia_interna_esterna = d.get("tipologia")
    costo_no_iva = d.get("costo_no_iva")

    costo_con_iva = d.get("costo_con_iva")
    attrezzaggio_incluso_nel_totale_no_iva = d.get("attrezzaggio_incluso_nel_totale_no_iva")
    attrezzaggio = d.get("attrezzaggio")
    attr_tipo = d.get("attr_tipo")

    # Unpack list for Pezzo(i)
    for pezzo in pezziList:

        # each pezzo is a dict,
        # take all the pezzo features
        quantità = list().append(pezzo.get("quantità"))
        particolare = pezzo.get("particolare")
        operatore = pezzo.get("operatore")
        peso = pezzo.get("peso")
        equilibratura = pezzo.get("equilibratura")
        data_di_lavorazione = pezzo.get("data_di_lavorazione")
        macchina = pezzo.get("macchina")
        classe = pezzo.get("classe")
        rpm = pezzo.get("rpm")
        # Note: instead of a list for each feature, we could put the cycle in the con.execute block that
        # inserts the value into the DB. I'd like, though, to separate the two.

    try:
        # Generate UUIDs
        cliente_id = str(uuid.uuid4())[:8]
        sales_id = str(uuid.uuid4())[:8]
        lavorazione_id = str(uuid.uuid4())[:8]
        offerta_id = str(uuid.uuid4())[:8]

        with duckdb.connect(db_path, read_only=False) as con:

            try: 
                con.execute("BEGIN TRANSACTION")

                con.execute("""
                    INSERT INTO cliente (cliente_id, cliente, nazione, regione)
                    VALUES (?, ?, ?, ?)
                """, (cliente_id, cliente, nazione, regione))

                con.execute("""
                    INSERT INTO sales (sales_id, agente, referente_commerciale_interno)
                    VALUES (?, ?, ?)
                """, (sales_id, agente, referente_commerciale_interno))

                con.execute("""
                    INSERT INTO lavorazione (lavorazione_id, durata_effettiva, durata_da_fatturare)
                    VALUES (?, ?, ?)
                """, (lavorazione_id, durata_effettiva, durata_da_fatturare))

                con.execute("""
                    INSERT INTO offerta (
                        offerta_id, cliente_id, sales_id, lavorazione_id,
                        data_offerta, stato, tipologia_interna_esterna,
                        costo_no_iva, costo_con_iva,
                        attrezzaggio_già_incluso_nel_totale_no_iva,
                        attrezzaggio, attr_tipo
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    offerta_id, cliente_id, sales_id, lavorazione_id,
                    data_offerta, stato, tipologia_interna_esterna,
                    costo_no_iva, costo_con_iva,
                    attrezzaggio_incluso_nel_totale_no_iva, attrezzaggio, attr_tipo
                ))
                for pezzo in pezziList:
                    # Unpack list for Pezzo(i)

                    # each pezzo is a dict,
                    # take all the pezzo features
                    quantità = pezzo.get("quantità")
                    particolare = pezzo.get("particolare")
                    operatore = pezzo.get("operatore")
                    peso = pezzo.get("peso")
                    equilibratura = pezzo.get("equilibratura")
                    data_di_lavorazione = pezzo.get("data_di_lavorazione")
                    macchina = pezzo.get("macchina")
                    classe = pezzo.get("classe")
                    rpm = pezzo.get("rpm")

                    con.execute("""
                        INSERT INTO pezzo (lavorazione_id, quantità, particolare, operatore, 
                            peso, equilibratura, data_di_lavorazione, macchina, classe, rpm
                            )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (lavorazione_id, quantità, particolare, operatore, 
                            peso, equilibratura, data_di_lavorazione, macchina, classe, rpm))                

                con.execute("COMMIT")
                st.success(f"✅ Offerta inserted with ID: {offerta_id}")

            except Exception as e:
                st.error(f"❌ Failed to insert data: {e}. Performing a Rollback.")
                con.execute("ROLLBACK")

    except Exception as e:
        st.error(f"❌ Failed to connect to DB or other issue: {e}")

# does this uses query,params to avoid sql injection?

def updateDB(df, edited_df, offerta_id):
    # Set DB path
    #db_path = "../Database/contoTerzi.duckdb"
    
    # Original DF and Edited one
    original = df.iloc[0]
    modified = edited_df.iloc[0]

    updates = []
    params = []

    for col in df.columns:
        if original[col] != modified[col]:
            updates.append(f"{col} = ?")
            params.append(modified[col])

    if updates:
        params.append(offerta_id)
        update_query = f"""
            UPDATE offerta
            SET {', '.join(updates)}
            WHERE offerta_id = ?
        """
        try:
            with duckdb.connect(db_path, read_only=False) as con:
                con.execute(update_query, params)
            st.success("✅ Modifiche salvate con successo.")
        except Exception as e:
            st.error(f"❌ Errore durante l'aggiornamento: {e}")
    else:
        st.info("ℹ️ Nessuna modifica rilevata.")

# Note:
# Gestire il db_path con os.environ e config.yml ??