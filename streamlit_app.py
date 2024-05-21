import streamlit as st
import pandas as pd
import sqlite3
from PIL import Image
import os
from streamlit_authenticator import Authenticate
import bcrypt
import re

# Conectar ao banco de dados (ou criar se não existir)
conn = sqlite3.connect('carros.db')
cursor = conn.cursor()

senha = "senha_de_teste"  # Senha em texto plano
salt = bcrypt.gensalt()
hashed_password = bcrypt.hashpw(senha.encode('utf-8'), salt)

# Criar tabela de usuários se não existir
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        password TEXT
    )
''')

# Inserir usuário inicial para teste (remover ou modificar em produção)
cursor.execute('''
    INSERT INTO users (name, email, password) 
    VALUES (?, ?, ?)
''', ("Seu Nome", "seu_email@exemplo.com", hashed_password.decode('utf-8')))
conn.commit()

# Diretório para armazenar as fotos
UPLOAD_DIRECTORY = "uploads"
if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)

# Criar tabela de carros se não existir (com coluna para o caminho da foto e email do usuário)
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

def _is_bcrypt_hash(hash_string):
    bcrypt_regex = re.compile(r"^\$2[aby]\$\d+\$.{53}$")
    return bool(bcrypt_regex.match(hash_string.decode('utf-8')))

# Configuração de autenticação
cursor.execute("SELECT name, email, password FROM users") 
data = cursor.fetchall()
credentials = {
    "names": {user[1]: user[0] for user in data},
    "usernames": {user[1]: {"name": user[0], "email": user[1], "password": user[2]} for user in data},
    "passwords": {user[1]: user[2] for user in data}
}

authenticator = Authenticate(
    credentials,
    "cookie_name",  
    "key",          
    cookie_expiry_days=30  
)

# Inicializar o estado de login e página
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'page' not in st.session_state:  
    st.session_state.page = "login"
if 'show_registration' not in st.session_state:
    st.session_state.show_registration = False

# Página de login
name, authentication_status, username = authenticator.login(
    fields=[
        {"title": "Login de Usuário"},
        {"name": "username", "label": "Email"},
        {"name": "password", "label": "Senha", "type": "password"}
    ],
)

if authentication_status:
    st.session_state.logged_in = True
    st.session_state.user_email = username  # Definir email do usuário no session state
    st.session_state.page = "disponiveis"
    st.experimental_rerun()
elif authentication_status == False:
    st.error('Username/password is incorrect')

if st.session_state.page == "login":
    st.title("Login")

    if not st.session_state.show_registration:
        if authentication_status == None:
            # Opção de login
            st.subheader("Login")
            name, authentication_status, username = authenticator.login(
                fields=[
                    {"name": "username", "label": "Email"},
                    {"name": "password", "label": "Senha", "type": "password"}
                ],
            )
            if authentication_status:
                st.write(f'Bem-vindo *{name}*')
                st.session_state.page = "disponiveis"
                st.experimental_rerun()
            elif authentication_status == False:
                st.error('Username/password is incorrect')
        # Botão para mostrar o formulário de cadastro
        if st.button("Ainda não tenho cadastro"):
            st.session_state.show_registration = True
            st.rerun()
    else:
        st.subheader("Criar Nova Conta")
        with st.form("cadastro_form"):
            nome = st.text_input("Nome")
            email = st.text_input("Email")
            senha = st.text_input("Senha", type="password")
            confirma_senha = st.text_input("Confirmar Senha", type="password")

            if st.form_submit_button("Criar Conta"):
                if senha != confirma_senha:
                    st.error("As senhas não coincidem")
                elif any(email == user[1] for user in data):
                    st.error("Email já cadastrado")
                else:
                    # Criptografar a senha com bcrypt
                    salt = bcrypt.gensalt()
                    hashed_password = bcrypt.hashpw(senha.encode('utf-8'), salt)

                    # Inserir o novo usuário no banco de dados
                    cursor.execute('''
                        INSERT INTO users (name, email, password)
                        VALUES (?, ?, ?)
                    ''', (nome, email, hashed_password.decode('utf-8')))
                    conn.commit()
                    st.success("Conta criada com sucesso!")
                    st.session_state.show_registration = False  # Voltar para a página de login
                    st.rerun()


# Restante do aplicativo (visível apenas se o usuário estiver logado)
if st.session_state.logged_in:
    st.write(f'Bem-vindo *{name}*')
    st.title('Compartilhamento de Estoque de Carros')

    # Menu lateral
    st.sidebar.title("Menu")
    page_options = ["Disponíveis", "Meus Carros"]
    page_placeholder = st.sidebar.empty()
    page = page_placeholder.radio("Selecione a página:", page_options)

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
                    st.rerun()
