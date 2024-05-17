import streamlit as st
import pandas as pd
import sqlite3
from PIL import Image
import os

# Diretório para armazenar as fotos
UPLOAD_DIRECTORY = "uploads"
if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)

# Conectar ao banco de dados (ou criar se não existir)
conn = sqlite3.connect('carros.db')
cursor = conn.cursor()

# Criar tabela se não existir (com coluna para o caminho da foto e email do usuário)
cursor.execute('''
    CREATE TABLE IF NOT EXISTS carros (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        marca TEXT,
        modelo TEXT,
        ano INTEGER,
        preco REAL,
        quilometragem INTEGER,
        foto_path TEXT,
        user_email TEXT
    )
''')
conn.commit()  

# Estado para controlar o login e a página atual
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'page' not in st.session_state:
    st.session_state.page = "login"

# Função para verificar o login (substitua por sua lógica de autenticação real)
def check_login(email, senha):
    return email == "usuario@exemplo.com" and senha == "senha123"

# Página de login
if st.session_state.page == "login":
    st.title("Login")
    email = st.text_input("Email")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if check_login(email, senha):
            st.session_state.logged_in = True
            st.session_state.user_email = email  # Armazenar o email do usuário
            st.session_state.page = "disponiveis"
            st.experimental_rerun()
        else:
            st.error("Email ou senha incorretos")

# Restante do aplicativo (visível apenas se o usuário estiver logado)
if st.session_state.logged_in:
    # Menu lateral
    st.sidebar.title("Menu")
    page = st.sidebar.radio("Selecione a página:", ["Disponíveis", "Meus Carros"])

    # Lógica para cada página
    if page == "Disponíveis":
        # Carregar todos os dados do banco de dados
        query = "SELECT * FROM carros"
        df = pd.read_sql_query(query, conn)

        # Exibir os carros com as fotos
        st.subheader("Carros Disponíveis:")
        for index, row in df.iterrows():
            col1, col2 = st.columns([1, 2])
            with col1:
                if row['foto_path']:
                    st.image(Image.open(row['foto_path']), caption=f"{row['marca']} {row['modelo']}", use_column_width=True)
                else:
                    st.write("Sem foto disponível")
            with col2:
                st.write(f"**Marca:** {row['marca']}")
                st.write(f"**Modelo:** {row['modelo']}")
                st.write(f"**Ano:** {row['ano']}")
                st.write(f"**Preço:** R$ {row['preco']:.2f}")
                st.write(f"**Quilometragem:** {row['quilometragem']} km")

    elif page == "Meus Carros":
        # Carregar os carros do usuário do banco de dados
        query = "SELECT * FROM carros WHERE user_email = ?"
        df = pd.read_sql_query(query, conn, params=(st.session_state.user_email,))

        # Exibir os carros do usuário
        st.subheader("Meus Carros:")
        for index, row in df.iterrows():
            # ... (código para exibir os carros com fotos)
    
    # Formulário para adicionar novo carro
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

    if st.session_state.show_form:
        with st.form("novo_carro_form"):
            st.subheader("Adicionar Novo Carro")
            marca = st.text_input("Marca")
            modelo = st.text_input("Modelo")
            ano = st.number_input("Ano", min_value=1900, max_value=2024, value=2023, step=1)
            preco = st.number_input("Preço", min_value=0, value=10000, step=100)
            quilometragem = st.number_input("Quilometragem", min_value=0, value=0, step=1000)
            foto = st.file_uploader("Foto do Carro", type=["jpg", "png", "jpeg"])

            if st.form_submit_button("Adicionar Carro"):
                if foto is not None:
                    # Salvar a foto no diretório de uploads
                    foto_path = os.path.join(UPLOAD_DIRECTORY, foto.name)
                    with open(foto_path, "wb") as f:
                        f.write(foto.getbuffer())
                else:
                    foto_path = None  # Se não houver foto, armazenar None

                # Inserir dados no banco de dados (incluindo o caminho da foto)
                cursor.execute('''
                    INSERT INTO carros (marca, modelo, ano, preco, quilometragem, foto_path, user_email)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (marca, modelo, ano, preco, quilometragem, foto_path, st.session_state.user_email))
                conn.commit()
                st.session_state.show_form = False 
                st.experimental_rerun() 
