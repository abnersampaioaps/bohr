import streamlit as st
import pandas as pd
import sqlite3

# Conectar ao banco de dados (ou criar se não existir)
conn = sqlite3.connect('carros.db')
cursor = conn.cursor()

# Criar tabela se não existir
cursor.execute('''
    CREATE TABLE IF NOT EXISTS carros (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        marca TEXT,
        modelo TEXT,
        ano INTEGER,
        preco REAL,
        quilometragem INTEGER
    )
''')

# Estado para controlar a visibilidade do formulário
if 'show_form' not in st.session_state:
    st.session_state.show_form = False

# Botão "+" flutuante
st.markdown(
    """
    <style>
        .stButton button {
            background-color: red;
            color: white;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            font-size: 24px;
            position: fixed;
            bottom: 20px;
            right: 20px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

if st.button("+"):
    st.session_state.show_form = True

# Carregar dados do banco de dados
query = "SELECT * FROM carros"
df = pd.read_sql_query(query, conn)

# Exibir dados
st.subheader("Carros Disponíveis:")
st.dataframe(df)

# Formulário (visível apenas se show_form for True)
if st.session_state.show_form:
    with st.form("novo_carro_form"):
        st.subheader("Adicionar Novo Carro")
        marca = st.text_input("Marca")
        modelo = st.text_input("Modelo")
        ano = st.number_input("Ano", min_value=1900, max_value=2024, value=2023, step=1)
        preco = st.number_input("Preço", min_value=0, value=10000, step=100)
        quilometragem = st.number_input("Quilometragem", min_value=0, value=0, step=1000)

        if st.form_submit_button("Adicionar Carro"):
            cursor.execute('''
                INSERT INTO carros (marca, modelo, ano, preco, quilometragem)
                VALUES (?, ?, ?, ?, ?)
            ''', (marca, modelo, ano, preco, quilometragem))
            conn.commit()
            st.session_state.show_form = False 
            st.experimental_rerun() 

# Filtros (opcional)
# ... (código para adicionar filtros na barra lateral, se necessário)
