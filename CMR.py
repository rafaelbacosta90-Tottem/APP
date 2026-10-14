import streamlit as st
from supabase import create_client, Client
import datetime
import pandas as pd

# --- Configuração da Página ---
st.set_page_config(page_title="Portal de Licenças", page_icon="🔒", layout="wide")

# --- Sistema de Autenticação ---
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

def realizar_login():
    if st.session_state["usuario"] == st.secrets["ADMIN_USER"] and st.session_state["senha"] == st.secrets["ADMIN_PASS"]:
        st.session_state["autenticado"] = True
    else:
        st.error("Usuário ou senha incorretos.")

def realizar_logout():
    st.session_state["autenticado"] = False

# Tela de Login
if not st.session_state["autenticado"]:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.title("🔒 Acesso Restrito")
        st.markdown("Insira suas credenciais para gerenciar as licenças.")
        with st.form("form_login"):
            st.text_input("Usuário", key="usuario")
            st.text_input("Senha", type="password", key="senha")
            st.form_submit_button("Entrar", on_click=realizar_login, use_container_width=True)
    st.stop() # Interrompe a execução do resto do código se não estiver logado

# --- Conexão com Supabase ---
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

# --- Interface Principal (Logado) ---
st.sidebar.title("Bem-vindo(a)")
st.sidebar.button("Sair / Logout", on_click=realizar_logout, type="primary", use_container_width=True)

st.title("Gestão de Licenças de Software")
st.markdown("---")

# Abas de navegação principal
aba_dashboard, aba_cadastro, aba_admin = st.tabs(["📊 Dashboard", "➕ Nova Licença", "⚙️ Administração"])

# Busca todos os dados uma vez para usar nas abas
try:
    resposta = supabase.table("licencas").select("*").order("id").execute()
    dados_licencas = resposta.data
except Exception as e:
    st.error(f"Erro ao conectar com o banco de dados: {e}")
    dados_licencas = []

# --- ABA 1: DASHBOARD ---
with aba_dashboard:
    if dados_licencas:
        df = pd.DataFrame(dados_licencas)
        total = len(df)
        ativas = len(df[df["ativa"] == True])
        inativas = total - ativas
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total de Licenças", total)
        col2.metric("Licenças Ativas", ativas, delta="Operacionais")
        col3.metric("Licenças Inativas", inativas, delta="- Bloqueadas", delta_color="inverse")
    else:
        st.info("Nenhuma licença cadastrada para gerar os gráficos.")

# --- ABA 2: CADASTRO ---
with aba_cadastro:
    st.subheader("Registrar Novo Cliente/Máquina")
    
    with st.form("form_cadastro", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            cnpj = st.text_input("CNPJ (Apenas números)", max_chars=14)
            hwid = st.text_input("HWID (Identificador da Máquina)")
        with col2:
            data_expiracao = st.date_input("Data de Expiração", min_value=datetime.date.today())
            ativa = st.toggle("Ativar licença imediatamente?", value=True)
            
        st.write("")
        submit = st.form_submit_button("💾 Salvar Licença", type="primary")
        
        if submit:
            if not cnpj.isdigit() or len(cnpj) != 14:
                st.error("Por favor, insira um CNPJ válido com 14 números.")
            elif not hwid:
                st.error("O HWID é obrigatório para vincular a licença à máquina.")
            else:
                try:
                    nova_licenca = {
                        "cnpj": cnpj,
                        "hwid": hwid,
                        "data_expiracao": str(data_expiracao),
                        "ativa": ativa
                    }
                    supabase.table("licencas").insert(nova_licenca).execute()
                    st.success(f"✅ Licença para o CNPJ {cnpj} cadastrada com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao salvar no banco de dados: {e}")

# --- ABA 3: ADMINISTRAÇÃO ---
with aba_admin:
    st.subheader("Lista e Edição de Licenças")
    
    if not dados_licencas:
        st.info("Nenhuma licença cadastrada ainda.")
    else:
        # Tabela principal atualizada com os novos campos
        st.dataframe(
            dados_licencas,
            column_config={
                "id": "ID",
                "cnpj": "CNPJ",
                "hwid": "HWID",
                "nome_maquina": "Computador",
                "ultima_validacao": st.column_config.DatetimeColumn("Última Validação", format="DD/MM/YYYY HH:mm"),
                "data_expiracao": st.column_config.DateColumn("Expiração", format="DD/MM/YYYY"),
                "ativa": st.column_config.CheckboxColumn("Ativa?"),
                "created_at": None # Oculta a data de criação para não poluir a tela
            },
            hide_index=True,
            use_container_width=True
        )
        
        st.divider()
        
        # Área de edição e bloqueio
        st.subheader("Alterar Status / Bloquear Acesso")
        
        lista_licencas = [f"{c['id']} - CNPJ: {c['cnpj']} (HWID: {c['hwid']})" for c in dados_licencas]
        
        with st.container(border=True):
            col_a, col_b, col_c = st.columns([2, 2, 1])
            
            with col_a:
                selecao = st.selectbox("Selecione a Licença para alterar:", lista_licencas)
                id_selecionado = selecao.split(" - ")[0] if selecao else None
                
            with col_b:
                novo_status = st.radio("Novo Status da Licença:", ["Ativa", "Inativa"], horizontal=True)
                
            with col_c:
                st.write("")
                if st.button("Aplicar Mudança", use_container_width=True):
                    status_bool = True if novo_status == "Ativa" else False
                    supabase.table("licencas").update({"ativa": status_bool}).eq("id", id_selecionado).execute()
                    st.success("✅ Status atualizado!")
                    st.rerun()