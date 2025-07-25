import streamlit as st
import duckdb
import uuid
from datetime import date

# --- Functions ---
## Read from Clienti table
def get_clienti_sample(con, limit=5):
    query = f"SELECT * FROM cliente LIMIT {limit}"
    return con.execute(query).fetchdf()

st.set_page_config(page_title="Visualizzazione", layout="centered")
st.title("Visualizza i Dati nel Database")
st.subheader(f"Cerca...") 

db_path = "../Database/contoTerzi.duckdb"
DATE_COLUMN = "data_offerta"

#with duckdb.connect(db_path, read_only=True) as con:
#    df = get_clienti_sample(con, limit=5)
#    st.write("Clienti", df.T)

# --- UI Widgets ---
with st.sidebar:
    st.header("🔎 Filtri")

    # Connect temporarily to get list of tables
    with duckdb.connect(db_path, read_only=True) as con:
        tables = con.execute("SHOW TABLES").fetchdf()["name"].tolist()

    selected_table = st.selectbox("📁 Seleziona una tabella", tables)

    limit = st.number_input("🔢 Numero di righe da mostrare", min_value=1, value=10)

    # Optional Date Filter
    apply_date_filter = st.checkbox("📅 Filtra per data", value=False)
    if apply_date_filter:

        if selected_table == "pezzo":
            date_choice = st.radio("Filtra per data di", ["Offerta", "Lavorazione"], horizontal=True, index=None)
            date_field = "offerta.data_offerta" if date_choice == "Offerta" else "pezzo.data_di_lavorazione"
        else:
            #date_choice = st.checkbox("📅 Filtra per data di offerta", value=False)
            date_field = "offerta.data_offerta"

        if date_field:
            start_date = st.date_input("Da", value=date(2024, 1, 1), key="start")
            end_date = st.date_input("A", value=date.today(), key="end")
            limit = "NULL OFFSET NULL" # no limit

    # Sort Order
    sort_order = st.radio("📈 Ordina per data", ["Decrescente", "Crescente"], horizontal=True)
    order_sql = "DESC" if sort_order == "Decrescente" else "ASC"



# --- Query Building ---
# Define join conditions based on selected table
join_clause = ""
if selected_table == "cliente":
    join_clause = f"JOIN offerta ON cliente.cliente_id = offerta.cliente_id"
elif selected_table == "sales":
    join_clause = f"JOIN offerta ON sales.sales_id = offerta.sales_id"
elif selected_table == "lavorazione":
    join_clause = f"JOIN offerta ON lavorazione.lavorazione_id = offerta.lavorazione_id"
elif selected_table == "pezzo":
    join_clause = f"""
        JOIN lavorazione ON lavorazione.lavorazione_id = pezzo.lavorazione_id
        JOIN offerta ON offerta.lavorazione_id = pezzo.lavorazione_id
    """

# WHERE clause is applied only if user enables the filter and the join path exists
where_clause = ""
if apply_date_filter:
    where_clause = f"WHERE {date_field} BETWEEN '{start_date}' AND '{end_date}'"

# Final query
query = f"""
    SELECT { selected_table + ".* ," + "offerta.data_offerta" if selected_table != 'offerta' else selected_table + ".*"} FROM {selected_table if selected_table != 'offerta' else 'offerta'}
    {join_clause}
    {where_clause}
    ORDER BY { 'offerta.data_offerta' } {order_sql}
    LIMIT {limit}
"""



# --- Query Execution ---
try:
    with duckdb.connect(db_path, read_only=True) as con:
        df = con.execute(query).fetchdf()
        if limit is "NULL OFFSET NULL":
            st.subheader(f"📄 Tabella: `{selected_table}` — tutte le righe")
        else:
            st.subheader(f"📄 Tabella: `{selected_table}` — {limit} righe")
        st.dataframe(df)
        #st.caption(f"Query eseguita: \n {query.strip()}")

except Exception as e:
    st.error(f"❌ Errore durante la lettura della tabella: {e}")

# use query, params to avoid sql injection
