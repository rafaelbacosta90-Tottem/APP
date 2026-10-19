import streamlit as st
from supabase import create_client, Client
import datetime
import pandas as pd
import urllib.parse
import re

# --- Configuração da Página ---
st.set_page_config(page_title="Portal de Gestão SaaS", page_icon="🏢", layout="wide")

# --- Estilização Customizada Opcional ---
st.markdown("""
    <style>
    .stMetric {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

def realizar_login():
    if st.session_state["usuario"] == st.secrets["ADMIN_USER"] and st.session_state["senha"] == st.secrets["ADMIN_PASS"]:
        st.session_state["autenticado"] = True
    else:
        st.error("Usuário ou senha incorretos.")

def realizar_logout():
    st.session_state["autenticado"] = False

# --- Tela de Login Melhorada ---
if not st.session_state["autenticado"]:
    st.markdown("<br><br><br>", unsafe_allow_html=True) # Espaçamento superior
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        with st.container(border=True): # Design em Card para o Login
            st.title("🔒 Acesso Restrito")
            st.markdown("Insira suas credenciais para gerenciar o sistema SaaS.")
            st.divider()
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

# --- Menu Lateral ---
with st.sidebar:
    st.title("Bem-vindo(a)")
    st.markdown("Painel de Controle Administrativo")
    st.divider()
    st.button("Sair / Logout", on_click=realizar_logout, type="primary", use_container_width=True)

# --- Cabeçalho Principal ---
st.title("🏢 Gestão de Clientes, Licenças e Ferramentas")
st.markdown("---")

aba_dashboard, aba_clientes, aba_ferramentas, aba_licencas, aba_vencimentos, aba_acessos, aba_versoes = st.tabs([
    "📊 Dashboard", "👥 Clientes", "🛠️ Ferramentas", "🔑 Licenças (Máquinas)", "⏰ Vencimentos", "📡 Auditoria", "🚀 Sistema"
])

# Buscas globais
try:
    dados_clientes = supabase.table("clientes").select("*").execute().data
    dados_licencas = supabase.table("licencas").select("*").order("id").execute().data
    dados_ferramentas = supabase.table("ferramentas").select("*").order("id").execute().data
except Exception as e:
    st.error(f"Erro ao conectar com o banco de dados: {e}")
    dados_clientes, dados_licencas, dados_ferramentas = [], [], []

# ==========================================
# ABA 1: DASHBOARD
# ==========================================
with aba_dashboard:
    st.subheader("📊 Visão Geral do SaaS")
    
    # Puxa os dados atualizados da telemetria
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

    df_cli = pd.DataFrame(dados_clientes) if dados_clientes else pd.DataFrame()
    df_lic = pd.DataFrame(dados_licencas) if dados_licencas else pd.DataFrame()
    
    try:
        modulos_ativos = len(supabase.table("licencas_ferramentas").select("id").eq("ativa", True).execute().data)
    except:
        modulos_ativos = 0
        
    st.markdown("#### 👥 Carteira de Clientes e Instalações")
    c1, c2, c3 = st.columns(3)
    with c1:
        with st.container(border=True):
            st.metric("Empresas Clientes", len(df_cli))
    with c2:
        with st.container(border=True):
            st.metric("Total de Máquinas (PCs)", len(df_lic))
    with c3:
        with st.container(border=True):
            st.metric("Módulos Ativos (Geral)", modulos_ativos)
    
    st.divider()
    
    st.markdown("#### 🚀 Engajamento e Volume da Rede")
    c4, c5 = st.columns(2)
    with c4:
        with st.container(border=True):
            st.metric("🤖 Análises com IA (Hoje)", total_ia_hoje, help="Soma de todas as análises feitas pelas máquinas hoje.")
    with c5:
        with st.container(border=True):
            st.metric("📥 Total de Editais Baixados", f"{total_editais_rede:,}".replace(",", "."), help="Soma histórica de todos os editais encontrados e baixados por todos os seus clientes em conjunto.")

# ==========================================
# ABA 2: GESTÃO DE CLIENTES (CRM)
# ==========================================
with aba_clientes:
    st.subheader("🏢 Carteira de Clientes e Consumo")
    
    try:
        acc_data = supabase.table("acessos_clientes").select("cnpj, editais_baixados").execute().data
        if acc_data and not df_cli.empty:
            df_soma = pd.DataFrame(acc_data).groupby("cnpj")["editais_baixados"].sum().reset_index()
            df_cli_display = pd.merge(df_cli, df_soma, on="cnpj", how="left")
            df_cli_display["editais_baixados"] = df_cli_display["editais_baixados"].fillna(0).astype(int)
        else:
            df_cli_display = df_cli.copy()
            if not df_cli_display.empty: df_cli_display["editais_baixados"] = 0
    except:
        df_cli_display = df_cli.copy()
        if not df_cli_display.empty: df_cli_display["editais_baixados"] = 0

    if not df_cli_display.empty:
        st.dataframe(
            df_cli_display,
            column_config={
                "cnpj": "CNPJ", "razao_social": "Razão Social", 
                "contato_nome": "Contato", "telefone": "WhatsApp", "email": "E-mail",
                "editais_baixados": st.column_config.NumberColumn("Editais Baixados", help="Total de editais encontrados e processados por este cliente"),
                "data_cadastro": st.column_config.DatetimeColumn("Cadastrado", format="DD/MM/YYYY")
            }, hide_index=True, use_container_width=True,
            column_order=["cnpj", "razao_social", "contato_nome", "telefone", "editais_baixados", "data_cadastro"]
        )
    else:
        st.info("Nenhum cliente cadastrado ainda.")

    st.divider()

    col_cad, col_edit = st.columns(2)
    
    with col_cad:
        with st.container(border=True): # Agrupamento visual
            st.subheader("➕ Novo Cliente")
            with st.form("form_cliente", clear_on_submit=True):
                cnpj = st.text_input("CNPJ (Apenas números)", max_chars=14)
                razao_social = st.text_input("Razão Social / Nome Fantasia")
                contato_nome = st.text_input("Pessoa de Contato")
                telefone = st.text_input("WhatsApp (Ex: 5511999999999)")
                email = st.text_input("E-mail Financeiro/Suporte")
                
                if st.form_submit_button("💾 Salvar Novo Cliente", type="primary", use_container_width=True):
                    if len(cnpj) != 14: st.error("CNPJ inválido.")
                    elif not razao_social: st.error("Razão Social é obrigatória.")
                    else:
                        try:
                            supabase.table("clientes").insert({
                                "cnpj": cnpj, "razao_social": razao_social, 
                                "contato_nome": contato_nome, "telefone": telefone, "email": email
                            }).execute()
                            st.success("✅ Cliente salvo com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro: Este CNPJ já pode estar cadastrado. ({e})")
                        
    with col_edit:
        with st.container(border=True): # Agrupamento visual
            st.subheader("✏️ Editar Cliente")
            if dados_clientes:
                lista_clientes_edit = [f"{c['cnpj']} - {c.get('razao_social', 'Sem Nome')}" for c in dados_clientes]
                cliente_escolha = st.selectbox("Selecione o Cliente:", [""] + lista_clientes_edit)
                
                if cliente_escolha:
                    cnpj_editar = cliente_escolha.split(" - ")[0]
                    cliente_atual = next((item for item in dados_clientes if item["cnpj"] == cnpj_editar), None)
                    
                    with st.form("form_editar_cliente"):
                        novo_nome = st.text_input("Razão Social", value=cliente_atual.get("razao_social", ""))
                        novo_contato = st.text_input("Pessoa de Contato", value=cliente_atual.get("contato_nome", ""))
                        novo_tel = st.text_input("WhatsApp", value=cliente_atual.get("telefone", ""))
                        novo_email = st.text_input("E-mail", value=cliente_atual.get("email", ""))
                        
                        if st.form_submit_button("💾 Atualizar Dados", type="primary", use_container_width=True):
                            supabase.table("clientes").update({
                                "razao_social": novo_nome,
                                "contato_nome": novo_contato,
                                "telefone": novo_tel,
                                "email": novo_email
                            }).eq("cnpj", cnpj_editar).execute()
                            st.success("✅ Cliente atualizado com sucesso!")
                            st.rerun()
            else:
                st.info("Cadastre um cliente primeiro para poder editá-lo.")

# ==========================================
# ABA 3: GESTÃO DE FERRAMENTAS
# ==========================================
with aba_ferramentas:
    c_cad_fer, c_lista_fer = st.columns([1, 2])
    with c_cad_fer:
        with st.container(border=True):
            st.subheader("➕ Nova Ferramenta")
            with st.form("form_ferramenta", clear_on_submit=True):
                nome_fer = st.text_input("Nome do Módulo/Ferramenta")
                if st.form_submit_button("💾 Cadastrar", type="primary", use_container_width=True):
                    if nome_fer:
                        supabase.table("ferramentas").insert({"nome": nome_fer}).execute()
                        st.success("✅ Ferramenta adicionada!")
                        st.rerun()
    with c_lista_fer:
        with st.container(border=True):
            st.subheader("🛠️ Ferramentas Disponíveis")
            if dados_ferramentas:
                st.dataframe(pd.DataFrame(dados_ferramentas), hide_index=True, use_container_width=True)

# ==========================================
# ABA 4: GESTÃO DE LICENÇAS (MÁQUINAS E MÓDULOS)
# ==========================================
with aba_licencas:
    if not dados_clientes or not dados_ferramentas:
        st.warning("⚠️ Cadastre pelo menos um Cliente e uma Ferramenta para gerar licenças.")
    else:
        with st.container(border=True):
            st.subheader("➕ Emitir Nova Licença de Máquina")
            lista_clientes = [f"{c['cnpj']} - {c.get('razao_social', '')}" for c in dados_clientes]
            lista_ferramentas = [f"{f['id']} - {f['nome']}" for f in dados_ferramentas]
            
            with st.form("form_licenca", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    cliente_sel = st.selectbox("Selecione o Cliente:", lista_clientes)
                    hwid = st.text_input("HWID (Identificador do Computador)")
                    limite_ia = st.number_input("Limite de Análises IA/Dia (Neste PC)", min_value=1, value=10)
                with c2:
                    ferramentas_selecionadas = st.multiselect("Selecione os Módulos/Ferramentas:", lista_ferramentas)
                    
                    datas_ferramentas = {}
                    for fer in ferramentas_selecionadas:
                        datas_ferramentas[fer] = st.date_input(f"Validade para: {fer.split(' - ')[1]}", min_value=datetime.date.today(), key=f"dt_{fer}")
                    
                if st.form_submit_button("💾 Gerar Licença e Módulos", type="primary", use_container_width=True):
                    cnpj_alvo = cliente_sel.split(" - ")[0]
                    if not hwid or not ferramentas_selecionadas: 
                        st.error("Preencha HWID e selecione ao menos uma ferramenta.")
                    else:
                        res_lic = supabase.table("licencas").insert({"cnpj": cnpj_alvo, "hwid": hwid, "limite_ia_diario": limite_ia}).execute()
                        nova_lic_id = res_lic.data[0]['id']
                        
                        payload_ferramentas = []
                        for fer in ferramentas_selecionadas:
                            fer_id = int(fer.split(" - ")[0])
                            payload_ferramentas.append({
                                "licenca_id": nova_lic_id,
                                "ferramenta_id": fer_id,
                                "data_expiracao": str(datas_ferramentas[fer]),
                                "ativa": True
                            })
                        supabase.table("licencas_ferramentas").insert(payload_ferramentas).execute()
                        
                        st.success("✅ Licença e ferramentas vinculadas com sucesso!")
                        st.rerun()

        st.divider()
        
        with st.container(border=True):
            st.subheader("⚙️ Gerenciar Módulos por Máquina")
            lista_licencas_edit = [f"{l['id']} - Máquina: {l['hwid']} (CNPJ: {l['cnpj']})" for l in dados_licencas]
            
            lic_escolha = st.selectbox("Escolha a Instalação (Máquina) para gerenciar as Ferramentas:", [""] + lista_licencas_edit)
            
            if lic_escolha:
                id_lic_editar = int(lic_escolha.split(" - ")[0])
                modulos_ativos = supabase.table("licencas_ferramentas").select("*, ferramentas(nome)").eq("licenca_id", id_lic_editar).execute().data
                
                if modulos_ativos:
                    st.markdown("##### Ferramentas Instaladas nesta Máquina:")
                    for mod in modulos_ativos:
                        with st.container(border=True):
                            c_m1, c_m2, c_m3, c_m4 = st.columns([2, 1, 1, 1]) # Adicionado c_m4 para o botão
                            c_m1.markdown(f"<br>**🛠️ {mod['ferramentas']['nome']}**", unsafe_allow_html=True)
                            
                            nova_dt = c_m2.date_input("Validade", value=datetime.datetime.strptime(mod['data_expiracao'], "%Y-%m-%d").date(), key=f"edt_{mod['id']}")
                            novo_status = c_m3.toggle("Ativo", value=mod['ativa'], key=f"tgl_{mod['id']}")
                            
                            c_m4.markdown("<br>", unsafe_allow_html=True) # Alinhamento visual
                            if c_m4.button("Atualizar", key=f"btn_{mod['id']}", use_container_width=True):
                                supabase.table("licencas_ferramentas").update({"data_expiracao": str(nova_dt), "ativa": novo_status}).eq("id", mod["id"]).execute()
                                st.success(f"{mod['ferramentas']['nome']} atualizado!")
                                st.rerun()
                else:
                    st.info("Nenhuma ferramenta vinculada a esta máquina.")

# ==========================================
# ABA 5: RELATÓRIO DE VENCIMENTOS (CRM)
# ==========================================
with aba_vencimentos:
    st.subheader("⏰ Cobranças e Alertas de Módulos (WhatsApp)")
    
    dados_venc = supabase.table("licencas_ferramentas").select(
        "*, ferramentas(nome), licencas(cnpj, hwid, clientes(razao_social, telefone))"
    ).eq("ativa", True).execute().data
    
    if not dados_venc:
        st.info("Nenhum módulo ativo para relatar.")