import streamlit as st
from supabase import create_client, Client
import datetime
import pandas as pd
import urllib.parse
import re

# --- Configuração da Página ---
st.set_page_config(page_title="Portal de Gestão SaaS", page_icon="🏢", layout="wide")

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
        st.markdown("Insira suas credenciais para gerenciar o sistema SaaS.")
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

st.title("Gestão de Clientes, Licenças e Ferramentas")
st.markdown("---")

aba_dashboard, aba_clientes, aba_ferramentas, aba_licencas, aba_vencimentos, aba_acessos, aba_versoes = st.tabs([
    "📊 Dashboard", "🏢 Clientes", "🛠️ Ferramentas", "🔑 Licenças (Máquinas)", "⏰ Vencimentos", "📡 Auditoria", "🚀 Sistema"
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
    st.subheader("Visão Geral do SaaS")
    df_cli = pd.DataFrame(dados_clientes) if dados_clientes else pd.DataFrame()
    df_lic = pd.DataFrame(dados_licencas) if dados_licencas else pd.DataFrame()
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Empresas Clientes", len(df_cli))
    c2.metric("Total de Máquinas (PCs)", len(df_lic))
    c3.metric("Módulos Ativos (Geral)", len(supabase.table("licencas_ferramentas").select("id").eq("ativa", True).execute().data))

# ==========================================
# ABA 2: GESTÃO DE CLIENTES
# ==========================================
with aba_clientes:
    st.subheader("🏢 Carteira de Clientes")
    if not df_cli.empty:
        st.dataframe(
            df_cli,
            column_config={
                "cnpj": "CNPJ", "razao_social": "Razão Social", 
                "contato_nome": "Contato", "telefone": "WhatsApp", "email": "E-mail",
                "data_cadastro": st.column_config.DatetimeColumn("Cadastrado", format="DD/MM/YYYY")
            }, hide_index=True, use_container_width=True
        )
    else:
        st.info("Nenhum cliente cadastrado ainda.")

    st.divider()

    col_cad, col_edit = st.columns(2)
    
    with col_cad:
        st.subheader("➕ Novo Cliente")
        with st.form("form_cliente", clear_on_submit=True):
            cnpj = st.text_input("CNPJ (Apenas números)", max_chars=14)
            razao_social = st.text_input("Razão Social / Nome Fantasia")
            contato_nome = st.text_input("Pessoa de Contato")
            telefone = st.text_input("WhatsApp (Ex: 5511999999999)")
            email = st.text_input("E-mail Financeiro/Suporte")
            
            if st.form_submit_button("💾 Salvar Novo Cliente", type="primary"):
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
                    
                    if st.form_submit_button("💾 Atualizar Dados", type="primary"):
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
        st.subheader("➕ Nova Ferramenta")
        with st.form("form_ferramenta", clear_on_submit=True):
            nome_fer = st.text_input("Nome do Módulo/Ferramenta")
            if st.form_submit_button("💾 Cadastrar", type="primary"):
                if nome_fer:
                    supabase.table("ferramentas").insert({"nome": nome_fer}).execute()
                    st.success("✅ Ferramenta adicionada!")
                    st.rerun()
    with c_lista_fer:
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
                
                # Gera dinamicamente um seletor de data para cada ferramenta selecionada
                datas_ferramentas = {}
                for fer in ferramentas_selecionadas:
                    datas_ferramentas[fer] = st.date_input(f"Validade para: {fer.split(' - ')[1]}", min_value=datetime.date.today(), key=f"dt_{fer}")
                
            if st.form_submit_button("💾 Gerar Licença e Módulos", type="primary"):
                cnpj_alvo = cliente_sel.split(" - ")[0]
                if not hwid or not ferramentas_selecionadas: 
                    st.error("Preencha HWID e selecione ao menos uma ferramenta.")
                else:
                    # 1. Cria a licença base (Máquina)
                    res_lic = supabase.table("licencas").insert({"cnpj": cnpj_alvo, "hwid": hwid, "limite_ia_diario": limite_ia}).execute()
                    nova_lic_id = res_lic.data[0]['id']
                    
                    # 2. Associa as ferramentas com suas respectivas datas
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
        st.subheader("⚙️ Gerenciar Módulos por Máquina")
        lista_licencas_edit = [f"{l['id']} - Máquina: {l['hwid']} (CNPJ: {l['cnpj']})" for l in dados_licencas]
        
        lic_escolha = st.selectbox("Escolha a Instalação (Máquina) para gerenciar as Ferramentas:", [""] + lista_licencas_edit)
        
        if lic_escolha:
            id_lic_editar = int(lic_escolha.split(" - ")[0])
            
            # Busca as ferramentas ligadas a esta máquina
            modulos_ativos = supabase.table("licencas_ferramentas").select("*, ferramentas(nome)").eq("licenca_id", id_lic_editar).execute().data
            
            if modulos_ativos:
                st.markdown("##### Ferramentas Instaladas nesta Máquina:")
                for mod in modulos_ativos:
                    with st.container(border=True):
                        c_m1, c_m2, c_m3 = st.columns([2, 1, 1])
                        c_m1.markdown(f"**🛠️ {mod['ferramentas']['nome']}**")
                        
                        nova_dt = c_m2.date_input("Validade", value=datetime.datetime.strptime(mod['data_expiracao'], "%Y-%m-%d").date(), key=f"edt_{mod['id']}")
                        novo_status = c_m3.toggle("Status", value=mod['ativa'], key=f"tgl_{mod['id']}")
                        
                        if st.button("Atualizar Módulo", key=f"btn_{mod['id']}", use_container_width=True):
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
    # Puxa os dados cruzados (Módulos -> Licenças -> Clientes)
    dados_venc = supabase.table("licencas_ferramentas").select("*, licencas(cnpj, hwid, clientes(razao_social, telefone))").eq("ativa", True).execute().data
    
    if not dados_venc:
        st.info("Nenhum módulo ativo para relatar.")
    else:
        # Achata os dados para o Pandas
        lista_plana = []
        for d in dados_venc:
            try:
                lista_plana.append({
                    "id_relacao": d['id'],
                    "ferramenta": d.get('ferramentas', {}).get('nome', 'Ferramenta ID '+str(d['ferramenta_id'])),
                    "data_exp": d['data_expiracao'],
                    "cnpj": d['licencas']['cnpj'],
                    "hwid": d['licencas']['hwid'],
                    "cliente": d['licencas']['clientes']['razao_social'],
                    "telefone": d['licencas']['clientes']['telefone']
                })
            except: pass
            
        if lista_plana:
            df_venc = pd.DataFrame(lista_plana)
            hoje = datetime.date.today()
            df_venc['data_exp_dt'] = pd.to_datetime(df_venc['data_exp']).dt.date
            df_venc['dias_restantes'] = (df_venc['data_exp_dt'] - hoje).apply(lambda x: x.days)
            
            df_filtrado = df_venc.sort_values(by="dias_restantes")
            
            for index, row in df_filtrado.iterrows():
                dias = row['dias_restantes']
                if dias <= 20: # Mostra apenas quem vence em 20 dias ou menos (ou já venceu)
                    cor = "red" if dias < 0 else ("orange" if dias == 0 else "green")
                    status = f"Vencida há {abs(dias)} dias" if dias < 0 else ("Vence HOJE!" if dias == 0 else f"Vence em {dias} dias")

                    with st.container(border=True):
                        col_i, col_m, col_w = st.columns([2, 4, 2])
                        with col_i:
                            st.markdown(f"🏢 **{row['cliente']}**")
                            st.markdown(f"🛠️ Módulo: {row['ferramenta']}")
                        with col_m:
                            st.markdown(f"⏳ **Status:** :{cor}[{status}] (Validade: {row['data_exp_dt'].strftime('%d/%m/%Y')})")
                        with col_w:
                            if row['telefone']:
                                numero_limpo = re.sub(r'\D', '', str(row['telefone']))
                                msg = f"Olá {row['cliente']}! A licença do módulo *{row['ferramenta']}* expira em {dias} dias. Deseja agilizar a renovação?" if dias > 0 else f"Olá {row['cliente']}! A licença do módulo *{row['ferramenta']}* expirou. Vamos renovar?"
                                st.link_button("💬 Cobrar no WhatsApp", f"https://wa.me/{numero_limpo}?text={urllib.parse.quote(msg)}", use_container_width=True)

# (Aba 6 Auditoria e Aba 7 Versões continuam iguais à lógica anterior, basta colar aqui o final padrão delas se desejar)

# ==========================================
# ABA 6: SISTEMA & IA
# ==========================================
with aba_versoes:
    st.subheader("🚀 Atualizações (OTA) e Chaves de IA")
    try:
        dados_v = supabase.table("controle_versoes").select("*").eq("id", 1).single().execute().data
        if dados_v:
            with st.form("form_versoes"):
                st.markdown("**1. Atualizações Obrigatórias do Executável**")
                v_atual = st.text_input("Versão Atual (Mais Recente)", value=dados_v.get("versao_atual", ""))
                v_minima = st.text_input("Versão Mínima Obrigatória", value=dados_v.get("versao_minima_obrigatoria", ""))
                url_down = st.text_input("Link de Download Direto do .exe", value=dados_v.get("url_download", ""))
                
                st.markdown("---")
                st.markdown("**2. Inteligência Artificial (Global)**")
                c_dots = st.text_input("Chave API: DOTS (OpenRouter)", value=dados_v.get("chave_dots", ""), type="password")
                c_gemini = st.text_input("Chave API: Google Gemini (Fallback)", value=dados_v.get("chave_gemini", ""), type="password")
                
                if st.form_submit_button("💾 Salvar Configurações na Nuvem", type="primary"):
                    supabase.table("controle_versoes").update({
                        "versao_atual": v_atual, "versao_minima_obrigatoria": v_minima, "url_download": url_down,
                        "chave_dots": c_dots, "chave_gemini": c_gemini
                    }).eq("id", 1).execute()
                    st.success("✅ Configurações e Chaves guardadas com segurança!")
                    st.rerun()
    except Exception as e:
        st.error(f"Erro ao carregar configurações globais: {e}")
        # ==========================================
# ABA 7: AUDITORIA (LOGS E CONSUMO)
# ==========================================
with aba_acessos:
    st.subheader("📡 Logs de Acesso, Máquinas e Consumo")
    
    if st.button("🔄 Atualizar Tabela de Logs"): 
        st.rerun()
        
    try:
        resp_acessos = supabase.table("acessos_clientes").select("*").order("data_ultimo_acesso", desc=True).execute()
        
        if resp_acessos.data:
            df_acessos = pd.DataFrame(resp_acessos.data)
            
            # Cruza os logs com a tabela de Clientes para mostrar o nome da Empresa
            if not df_cli.empty:
                df_acessos = pd.merge(df_acessos, df_cli[['cnpj', 'razao_social']], on='cnpj', how='left')
            else:
                df_acessos['razao_social'] = "Desconhecido"
            
            # Organiza as colunas de forma lógica
            colunas_ordem = ["cnpj", "razao_social", "maquina", "versao_atual", "usos_ia_hoje", "editais_baixados", "data_ultimo_acesso"]
            df_acessos = df_acessos[[c for c in colunas_ordem if c in df_acessos.columns]]
            
            # Ajuste de Fuso Horário (UTC para horário local)
            df_acessos["data_ultimo_acesso"] = pd.to_datetime(df_acessos["data_ultimo_acesso"]).dt.tz_localize(None) - pd.Timedelta(hours=3)
            
            st.dataframe(
                df_acessos, 
                column_config={
                    "cnpj": "CNPJ", 
                    "razao_social": "Cliente", 
                    "maquina": "Computador (Identificador)", 
                    "versao_atual": "Versão do App", 
                    "usos_ia_hoje": "Análises IA (Hoje)", 
                    "editais_baixados": "Editais Sincronizados",
                    "data_ultimo_acesso": st.column_config.DatetimeColumn("Último Acesso / Ping", format="DD/MM/YYYY HH:mm:ss")
                }, 
                use_container_width=True, 
                hide_index=True
            )
        else:
            st.info("Nenhum log de acesso registado pelas máquinas ainda.")
            
    except Exception as e:
        st.error(f"Erro ao processar os logs de auditoria: {e}")