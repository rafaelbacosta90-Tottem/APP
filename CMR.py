import streamlit as st
from supabase import create_client, Client
import datetime
import pandas as pd

# --- Configuração da Página ---
st.set_page_config(page_title="Portal de Licenças", page_icon="🔒", layout="wide")

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

def realizar_login():
    if st.session_state["usuario"] == st.secrets["ADMIN_USER"] and st.session_state["senha"] == st.secrets["ADMIN_PASS"]:
        st.session_state["autenticado"] = True
    else:
        st.error("Usuário ou senha incorretos.")

def realizar_logout():
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.title("🔒 Acesso Restrito")
        st.markdown("Insira suas credenciais para gerenciar as licenças.")
        with st.form("form_login"):
            st.text_input("Usuário", key="usuario")
            st.text_input("Senha", type="password", key="senha")
            st.form_submit_button("Entrar", on_click=realizar_login, use_container_width=True)
    st.stop() 

# --- Conexão com Supabase ---
@st.cache_resource
def init_connection():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_connection()

st.sidebar.title("Bem-vindo(a)")
st.sidebar.button("Sair / Logout", on_click=realizar_logout, type="primary", use_container_width=True)

st.title("Gestão de Licenças e IA")
st.markdown("---")

aba_dashboard, aba_cadastro, aba_admin, aba_acessos, aba_versoes = st.tabs([
    "📊 Dashboard", "➕ Nova Licença", "⚙️ Administração", "📡 Auditoria de Acessos", "🚀 Sistema & IA"
])

try:
    dados_licencas = supabase.table("licencas").select("*").order("id").execute().data
except Exception as e:
    st.error(f"Erro ao conectar com o banco de dados: {e}")
    dados_licencas = []

# --- ABA 1: DASHBOARD ---
with aba_dashboard:
    st.subheader("Visão Geral do SaaS")
    
    # Busca a telemetria das máquinas
    try:
        resp_acessos = supabase.table("acessos_clientes").select("usos_ia_hoje, editais_baixados").execute()
        dados_acessos = resp_acessos.data
    except:
        dados_acessos = []
        
    total_ia_hoje = 0
    total_editais_rede = 0
    
    if dados_acessos:
        df_acc = pd.DataFrame(dados_acessos)
        if "usos_ia_hoje" in df_acc.columns:
            total_ia_hoje = int(df_acc["usos_ia_hoje"].fillna(0).sum())
        if "editais_baixados" in df_acc.columns:
            total_editais_rede = int(df_acc["editais_baixados"].fillna(0).sum())

    if dados_licencas:
        df = pd.DataFrame(dados_licencas)
        total_lic = len(df)
        ativas = len(df[df["ativa"] == True])
        inativas = total_lic - ativas
        
        st.markdown("#### 👥 Licenças e Clientes")
        c1, c2, c3 = st.columns(3)
        c1.metric("Total de Licenças", total_lic)
        c2.metric("Licenças Ativas", ativas, delta="Operacionais")
        c3.metric("Licenças Inativas", inativas, delta="- Bloqueadas", delta_color="inverse")
        
        st.divider()
        
        st.markdown("#### 🚀 Engajamento e Consumo (Rede Global)")
        c4, c5 = st.columns(2)
        c4.metric("🤖 Análises com IA (Hoje)", total_ia_hoje, help="Quantidade total de editais lidos pela IA hoje, somando todos os seus clientes.")
        c5.metric("📄 Editais Sincronizados", f"{total_editais_rede:,}".replace(",", "."), help="Volume total de editais guardados de forma automática nas máquinas dos clientes.")
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
            limite_ia = st.number_input("Limite de Análises IA por Dia", min_value=1, max_value=500, value=10)
        with col2:
            data_expiracao = st.date_input("Data de Expiração", min_value=datetime.date.today())
            ativa = st.toggle("Ativar licença imediatamente?", value=True)
            
        if st.form_submit_button("💾 Salvar Licença", type="primary"):
            if len(cnpj) != 14: st.error("CNPJ inválido.")
            elif not hwid: st.error("HWID obrigatório.")
            else:
                supabase.table("licencas").insert({
                    "cnpj": cnpj, "hwid": hwid, "data_expiracao": str(data_expiracao), "ativa": ativa, "limite_ia_diario": limite_ia
                }).execute()
                st.success("✅ Licença cadastrada!")
                st.rerun()

# --- ABA 3: ADMINISTRAÇÃO ---
with aba_admin:
    st.subheader("Lista e Edição de Licenças")
    if dados_licencas:
        st.dataframe(
            dados_licencas,
            column_config={
                "id": "ID", "cnpj": "CNPJ", "hwid": "HWID", "limite_ia_diario": "Limite IA/Dia",
                "data_expiracao": st.column_config.DateColumn("Expiração", format="DD/MM/YYYY"),
                "ativa": st.column_config.CheckboxColumn("Ativa?")
            }, hide_index=True, use_container_width=True
        )
        
        st.divider()
        st.subheader("Alterar Configurações do Cliente")
        lista_licencas = [f"{c['id']} - CNPJ: {c['cnpj']}" for c in dados_licencas]
        
        with st.container(border=True):
            col_a, col_b, col_c = st.columns([2, 1, 1])
            with col_a:
                selecao = st.selectbox("Selecione a Licença:", lista_licencas)
                id_selecionado = selecao.split(" - ")[0] if selecao else None
            with col_b:
                novo_status = st.radio("Status:", ["Ativa", "Inativa"], horizontal=True)
            with col_c:
                novo_limite = st.number_input("Novo Limite IA", min_value=1, value=10)
                
            if st.button("Aplicar Mudança", use_container_width=True):
                supabase.table("licencas").update({"ativa": (novo_status == "Ativa"), "limite_ia_diario": novo_limite}).eq("id", id_selecionado).execute()
                st.success("✅ Atualizado!")
                st.rerun()

# --- ABA 4: AUDITORIA DE ACESSOS ---
with aba_acessos:
    st.subheader("📡 Logs de Máquinas e Consumo de IA")
    if st.button("🔄 Atualizar Logs"): st.rerun()
        
    resp_acessos = supabase.table("acessos_clientes").select("*").order("data_ultimo_acesso", desc=True).execute()
    if resp_acessos.data:
        df_acessos = pd.DataFrame(resp_acessos.data)
        colunas_ordem = ["cnpj", "maquina", "versao_atual", "usos_ia_hoje", "editais_baixados", "data_ultimo_acesso"]
        df_acessos = df_acessos[[c for c in colunas_ordem if c in df_acessos.columns]]
        df_acessos["data_ultimo_acesso"] = pd.to_datetime(df_acessos["data_ultimo_acesso"]).dt.tz_localize(None) - pd.Timedelta(hours=3)
        
        st.dataframe(df_acessos, column_config={
            "cnpj": "CNPJ", "maquina": "Computador", "versao_atual": "Versão", 
            "usos_ia_hoje": "IA Usada Hoje", "editais_baixados": "Editais Processados",
            "data_ultimo_acesso": st.column_config.DatetimeColumn("Último Acesso App", format="DD/MM/YYYY HH:mm:ss")
        }, use_container_width=True, hide_index=True)

# --- ABA 5: VERSÕES E CHAVES DE IA ---
with aba_versoes:
    st.subheader("🚀 Gerenciador de Atualizações e Chaves de IA")
    dados_v = supabase.table("controle_versoes").select("*").eq("id", 1).single().execute().data
    
    if dados_v:
        with st.form("form_versoes"):
            st.markdown("**Atualizações (OTA)**")
            v_atual = st.text_input("Versão Atual (Mais Recente)", value=dados_v.get("versao_atual", ""))
            v_minima = st.text_input("Versão Mínima Obrigatória", value=dados_v.get("versao_minima_obrigatoria", ""))
            url_down = st.text_input("Link de Download Direto do .exe", value=dados_v.get("url_download", ""))
            
            st.markdown("---")
            st.markdown("**Inteligência Artificial (Global)**")
            c_dots = st.text_input("Chave API: DOTS (OpenRouter)", value=dados_v.get("chave_dots", ""), type="password")
            c_gemini = st.text_input("Chave API: Google Gemini (Fallback)", value=dados_v.get("chave_gemini", ""), type="password")
            
            if st.form_submit_button("💾 Salvar Configurações na Nuvem", type="primary"):
                supabase.table("controle_versoes").update({
                    "versao_atual": v_atual, "versao_minima_obrigatoria": v_minima, "url_download": url_down,
                    "chave_dots": c_dots, "chave_gemini": c_gemini
                }).eq("id", 1).execute()
                st.success("✅ Configurações e Chaves guardadas com segurança!")
                st.rerun()