import streamlit as st
from supabase import create_client, Client
import datetime
import pandas as pd
import urllib.parse
import re

# --- Configuração da Página ---
st.set_page_config(page_title="Portal de Gestão SaaS", page_icon="🏢", layout="wide")[cite: 1]

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
    st.session_state["autenticado"] = False[cite: 1]

def realizar_login():
    if st.session_state["usuario"] == st.secrets["ADMIN_USER"] and st.session_state["senha"] == st.secrets["ADMIN_PASS"]:[cite: 1]
        st.session_state["autenticado"] = True[cite: 1]
    else:
        st.error("Usuário ou senha incorretos.")[cite: 1]

def realizar_logout():
    st.session_state["autenticado"] = False[cite: 1]

# --- Tela de Login Melhorada ---
if not st.session_state["autenticado"]:[cite: 1]
    st.markdown("<br><br><br>", unsafe_allow_html=True) # Espaçamento superior
    col1, col2, col3 = st.columns([1, 1.2, 1])[cite: 1]
    with col2:
        with st.container(border=True): # Design em Card para o Login
            st.title("🔒 Acesso Restrito")[cite: 1]
            st.markdown("Insira suas credenciais para gerenciar o sistema SaaS.")[cite: 1]
            st.divider()
            with st.form("form_login"):[cite: 1]
                st.text_input("Usuário", key="usuario")[cite: 1]
                st.text_input("Senha", type="password", key="senha")[cite: 1]
                st.form_submit_button("Entrar", on_click=realizar_login, use_container_width=True)[cite: 1]
    st.stop()  [cite: 1]

# --- Conexão com Supabase ---
@st.cache_resource
def init_connection():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])[cite: 1]

supabase = init_connection()[cite: 1]

# --- Menu Lateral ---
with st.sidebar:
    st.title("Bem-vindo(a)")[cite: 1]
    st.markdown("Painel de Controle Administrativo")
    st.divider()
    st.button("Sair / Logout", on_click=realizar_logout, type="primary", use_container_width=True)[cite: 1]

# --- Cabeçalho Principal ---
st.title("🏢 Gestão de Clientes, Licenças e Ferramentas")[cite: 1]
st.markdown("---")[cite: 1]

aba_dashboard, aba_clientes, aba_ferramentas, aba_licencas, aba_vencimentos, aba_acessos, aba_versoes = st.tabs([
    "📊 Dashboard", "👥 Clientes", "🛠️ Ferramentas", "🔑 Licenças (Máquinas)", "⏰ Vencimentos", "📡 Auditoria", "🚀 Sistema"
])[cite: 1]

# Buscas globais
try:
    dados_clientes = supabase.table("clientes").select("*").execute().data[cite: 1]
    dados_licencas = supabase.table("licencas").select("*").order("id").execute().data[cite: 1]
    dados_ferramentas = supabase.table("ferramentas").select("*").order("id").execute().data[cite: 1]
except Exception as e:
    st.error(f"Erro ao conectar com o banco de dados: {e}")[cite: 1]
    dados_clientes, dados_licencas, dados_ferramentas = [], [], [][cite: 1]

# ==========================================
# ABA 1: DASHBOARD
# ==========================================
with aba_dashboard:
    st.subheader("📊 Visão Geral do SaaS")[cite: 1]
    
    # Puxa os dados atualizados da telemetria
    try:
        resp_acessos = supabase.table("acessos_clientes").select("usos_ia_hoje, editais_baixados").execute()[cite: 1]
        dados_acessos = resp_acessos.data[cite: 1]
    except:
        dados_acessos = [][cite: 1]
        
    total_ia_hoje = 0[cite: 1]
    total_editais_rede = 0[cite: 1]
    
    if dados_acessos:
        df_acc = pd.DataFrame(dados_acessos)[cite: 1]
        if "usos_ia_hoje" in df_acc.columns: [cite: 1]
            total_ia_hoje = int(df_acc["usos_ia_hoje"].fillna(0).sum())[cite: 1]
        if "editais_baixados" in df_acc.columns: [cite: 1]
            total_editais_rede = int(df_acc["editais_baixados"].fillna(0).sum())[cite: 1]

    df_cli = pd.DataFrame(dados_clientes) if dados_clientes else pd.DataFrame()[cite: 1]
    df_lic = pd.DataFrame(dados_licencas) if dados_licencas else pd.DataFrame()[cite: 1]
    
    try:
        modulos_ativos = len(supabase.table("licencas_ferramentas").select("id").eq("ativa", True).execute().data)[cite: 1]
    except:
        modulos_ativos = 0[cite: 1]
        
    st.markdown("#### 👥 Carteira de Clientes e Instalações")[cite: 1]
    c1, c2, c3 = st.columns(3)[cite: 1]
    with c1:
        with st.container(border=True):
            st.metric("Empresas Clientes", len(df_cli))[cite: 1]
    with c2:
        with st.container(border=True):
            st.metric("Total de Máquinas (PCs)", len(df_lic))[cite: 1]
    with c3:
        with st.container(border=True):
            st.metric("Módulos Ativos (Geral)", modulos_ativos)[cite: 1]
    
    st.divider()[cite: 1]
    
    st.markdown("#### 🚀 Engajamento e Volume da Rede")[cite: 1]
    c4, c5 = st.columns(2)[cite: 1]
    with c4:
        with st.container(border=True):
            st.metric("🤖 Análises com IA (Hoje)", total_ia_hoje, help="Soma de todas as análises feitas pelas máquinas hoje.")[cite: 1]
    with c5:
        with st.container(border=True):
            st.metric("📥 Total de Editais Baixados", f"{total_editais_rede:,}".replace(",", "."), help="Soma histórica de todos os editais encontrados e baixados por todos os seus clientes em conjunto.")[cite: 1]

# ==========================================
# ABA 2: GESTÃO DE CLIENTES (CRM)
# ==========================================
with aba_clientes:
    st.subheader("🏢 Carteira de Clientes e Consumo")[cite: 1]
    
    try:
        acc_data = supabase.table("acessos_clientes").select("cnpj, editais_baixados").execute().data[cite: 1]
        if acc_data and not df_cli.empty:
            df_soma = pd.DataFrame(acc_data).groupby("cnpj")["editais_baixados"].sum().reset_index()[cite: 1]
            df_cli_display = pd.merge(df_cli, df_soma, on="cnpj", how="left")[cite: 1]
            df_cli_display["editais_baixados"] = df_cli_display["editais_baixados"].fillna(0).astype(int)[cite: 1]
        else:
            df_cli_display = df_cli.copy()[cite: 1]
            if not df_cli_display.empty: df_cli_display["editais_baixados"] = 0[cite: 1]
    except:
        df_cli_display = df_cli.copy()[cite: 1]
        if not df_cli_display.empty: df_cli_display["editais_baixados"] = 0[cite: 1]

    if not df_cli_display.empty:
        st.dataframe(
            df_cli_display,
            column_config={
                "cnpj": "CNPJ", "razao_social": "Razão Social", 
                "contato_nome": "Contato", "telefone": "WhatsApp", "email": "E-mail",[cite: 1]
                "editais_baixados": st.column_config.NumberColumn("Editais Baixados", help="Total de editais encontrados e processados por este cliente"),[cite: 1]
                "data_cadastro": st.column_config.DatetimeColumn("Cadastrado", format="DD/MM/YYYY")[cite: 1]
            }, hide_index=True, use_container_width=True,
            column_order=["cnpj", "razao_social", "contato_nome", "telefone", "editais_baixados", "data_cadastro"][cite: 1]
        )
    else:
        st.info("Nenhum cliente cadastrado ainda.")[cite: 1]

    st.divider()[cite: 1]

    col_cad, col_edit = st.columns(2)[cite: 1]
    
    with col_cad:
        with st.container(border=True): # Agrupamento visual
            st.subheader("➕ Novo Cliente")[cite: 1]
            with st.form("form_cliente", clear_on_submit=True):[cite: 1]
                cnpj = st.text_input("CNPJ (Apenas números)", max_chars=14)[cite: 1]
                razao_social = st.text_input("Razão Social / Nome Fantasia")[cite: 1]
                contato_nome = st.text_input("Pessoa de Contato")[cite: 1]
                telefone = st.text_input("WhatsApp (Ex: 5511999999999)")[cite: 1]
                email = st.text_input("E-mail Financeiro/Suporte")[cite: 1]
                
                if st.form_submit_button("💾 Salvar Novo Cliente", type="primary", use_container_width=True):
                    if len(cnpj) != 14: st.error("CNPJ inválido.")[cite: 1]
                    elif not razao_social: st.error("Razão Social é obrigatória.")[cite: 1]
                    else:
                        try:
                            supabase.table("clientes").insert({
                                "cnpj": cnpj, "razao_social": razao_social, 
                                "contato_nome": contato_nome, "telefone": telefone, "email": email
                            }).execute()[cite: 1]
                            st.success("✅ Cliente salvo com sucesso!")[cite: 1]
                            st.rerun()[cite: 1]
                        except Exception as e:
                            st.error(f"Erro: Este CNPJ já pode estar cadastrado. ({e})")[cite: 1]
                        
    with col_edit:
        with st.container(border=True): # Agrupamento visual
            st.subheader("✏️ Editar Cliente")[cite: 1]
            if dados_clientes:[cite: 1]
                lista_clientes_edit = [f"{c['cnpj']} - {c.get('razao_social', 'Sem Nome')}" for c in dados_clientes][cite: 1]
                cliente_escolha = st.selectbox("Selecione o Cliente:", [""] + lista_clientes_edit)[cite: 1]
                
                if cliente_escolha:
                    cnpj_editar = cliente_escolha.split(" - ")[0][cite: 1]
                    cliente_atual = next((item for item in dados_clientes if item["cnpj"] == cnpj_editar), None)[cite: 1]
                    
                    with st.form("form_editar_cliente"):[cite: 1]
                        novo_nome = st.text_input("Razão Social", value=cliente_atual.get("razao_social", ""))[cite: 1]
                        novo_contato = st.text_input("Pessoa de Contato", value=cliente_atual.get("contato_nome", ""))[cite: 1]
                        novo_tel = st.text_input("WhatsApp", value=cliente_atual.get("telefone", ""))[cite: 1]
                        novo_email = st.text_input("E-mail", value=cliente_atual.get("email", ""))[cite: 1]
                        
                        if st.form_submit_button("💾 Atualizar Dados", type="primary", use_container_width=True):
                            supabase.table("clientes").update({
                                "razao_social": novo_nome,
                                "contato_nome": novo_contato,
                                "telefone": novo_tel,
                                "email": novo_email
                            }).eq("cnpj", cnpj_editar).execute()[cite: 1]
                            st.success("✅ Cliente atualizado com sucesso!")[cite: 1]
                            st.rerun()[cite: 1]
            else:
                st.info("Cadastre um cliente primeiro para poder editá-lo.")[cite: 1]

# ==========================================
# ABA 3: GESTÃO DE FERRAMENTAS
# ==========================================
with aba_ferramentas:
    c_cad_fer, c_lista_fer = st.columns([1, 2])[cite: 1]
    with c_cad_fer:
        with st.container(border=True):
            st.subheader("➕ Nova Ferramenta")[cite: 1]
            with st.form("form_ferramenta", clear_on_submit=True):[cite: 1]
                nome_fer = st.text_input("Nome do Módulo/Ferramenta")[cite: 1]
                if st.form_submit_button("💾 Cadastrar", type="primary", use_container_width=True):
                    if nome_fer:[cite: 1]
                        supabase.table("ferramentas").insert({"nome": nome_fer}).execute()[cite: 1]
                        st.success("✅ Ferramenta adicionada!")[cite: 1]
                        st.rerun()[cite: 1]
    with c_lista_fer:
        with st.container(border=True):
            st.subheader("🛠️ Ferramentas Disponíveis")[cite: 1]
            if dados_ferramentas:[cite: 1]
                st.dataframe(pd.DataFrame(dados_ferramentas), hide_index=True, use_container_width=True)[cite: 1]

# ==========================================
# ABA 4: GESTÃO DE LICENÇAS (MÁQUINAS E MÓDULOS)
# ==========================================
with aba_licencas:
    if not dados_clientes or not dados_ferramentas:[cite: 1]
        st.warning("⚠️ Cadastre pelo menos um Cliente e uma Ferramenta para gerar licenças.")[cite: 1]
    else:
        with st.container(border=True):
            st.subheader("➕ Emitir Nova Licença de Máquina")[cite: 1]
            lista_clientes = [f"{c['cnpj']} - {c.get('razao_social', '')}" for c in dados_clientes][cite: 1]
            lista_ferramentas = [f"{f['id']} - {f['nome']}" for f in dados_ferramentas][cite: 1]
            
            with st.form("form_licenca", clear_on_submit=True):[cite: 1]
                c1, c2 = st.columns(2)[cite: 1]
                with c1:
                    cliente_sel = st.selectbox("Selecione o Cliente:", lista_clientes)[cite: 1]
                    hwid = st.text_input("HWID (Identificador do Computador)")[cite: 1]
                    limite_ia = st.number_input("Limite de Análises IA/Dia (Neste PC)", min_value=1, value=10)[cite: 1]
                with c2:
                    ferramentas_selecionadas = st.multiselect("Selecione os Módulos/Ferramentas:", lista_ferramentas)[cite: 1]
                    
                    datas_ferramentas = {}[cite: 1]
                    for fer in ferramentas_selecionadas:[cite: 1]
                        datas_ferramentas[fer] = st.date_input(f"Validade para: {fer.split(' - ')[1]}", min_value=datetime.date.today(), key=f"dt_{fer}")[cite: 1]
                    
                if st.form_submit_button("💾 Gerar Licença e Módulos", type="primary", use_container_width=True):
                    cnpj_alvo = cliente_sel.split(" - ")[0][cite: 1]
                    if not hwid or not ferramentas_selecionadas: [cite: 1]
                        st.error("Preencha HWID e selecione ao menos uma ferramenta.")[cite: 1]
                    else:
                        res_lic = supabase.table("licencas").insert({"cnpj": cnpj_alvo, "hwid": hwid, "limite_ia_diario": limite_ia}).execute()[cite: 1]
                        nova_lic_id = res_lic.data[0]['id'][cite: 1]
                        
                        payload_ferramentas = [][cite: 1]
                        for fer in ferramentas_selecionadas:[cite: 1]
                            fer_id = int(fer.split(" - ")[0])[cite: 1]
                            payload_ferramentas.append({
                                "licenca_id": nova_lic_id,
                                "ferramenta_id": fer_id,
                                "data_expiracao": str(datas_ferramentas[fer]),
                                "ativa": True
                            })[cite: 1]
                        supabase.table("licencas_ferramentas").insert(payload_ferramentas).execute()[cite: 1]
                        
                        st.success("✅ Licença e ferramentas vinculadas com sucesso!")[cite: 1]
                        st.rerun()[cite: 1]

        st.divider()[cite: 1]
        
        with st.container(border=True):
            st.subheader("⚙️ Gerenciar Módulos por Máquina")[cite: 1]
            lista_licencas_edit = [f"{l['id']} - Máquina: {l['hwid']} (CNPJ: {l['cnpj']})" for l in dados_licencas][cite: 1]
            
            lic_escolha = st.selectbox("Escolha a Instalação (Máquina) para gerenciar as Ferramentas:", [""] + lista_licencas_edit)[cite: 1]
            
            if lic_escolha:
                id_lic_editar = int(lic_escolha.split(" - ")[0])[cite: 1]
                modulos_ativos = supabase.table("licencas_ferramentas").select("*, ferramentas(nome)").eq("licenca_id", id_lic_editar).execute().data[cite: 1]
                
                if modulos_ativos:
                    st.markdown("##### Ferramentas Instaladas nesta Máquina:")[cite: 1]
                    for mod in modulos_ativos:[cite: 1]
                        with st.container(border=True):[cite: 1]
                            c_m1, c_m2, c_m3, c_m4 = st.columns([2, 1, 1, 1]) # Adicionado c_m4 para o botão
                            c_m1.markdown(f"<br>**🛠️ {mod['ferramentas']['nome']}**", unsafe_allow_html=True)[cite: 1]
                            
                            nova_dt = c_m2.date_input("Validade", value=datetime.datetime.strptime(mod['data_expiracao'], "%Y-%m-%d").date(), key=f"edt_{mod['id']}")[cite: 1]
                            novo_status = c_m3.toggle("Ativo", value=mod['ativa'], key=f"tgl_{mod['id']}")[cite: 1]
                            
                            c_m4.markdown("<br>", unsafe_allow_html=True) # Alinhamento visual
                            if c_m4.button("Atualizar", key=f"btn_{mod['id']}", use_container_width=True):[cite: 1]
                                supabase.table("licencas_ferramentas").update({"data_expiracao": str(nova_dt), "ativa": novo_status}).eq("id", mod["id"]).execute()[cite: 1]
                                st.success(f"{mod['ferramentas']['nome']} atualizado!")[cite: 1]
                                st.rerun()[cite: 1]
                else:
                    st.info("Nenhuma ferramenta vinculada a esta máquina.")[cite: 1]

# ==========================================
# ABA 5: RELATÓRIO DE VENCIMENTOS (CRM)
# ==========================================
with aba_vencimentos:
    st.subheader("⏰ Cobranças e Alertas de Módulos (WhatsApp)")[cite: 1]
    
    dados_venc = supabase.table("licencas_ferramentas").select(
        "*, ferramentas(nome), licencas(cnpj, hwid, clientes(razao_social, telefone))"
    ).eq("ativa", True).execute().data[cite: 1]
    
    if not dados_venc:[cite: 1]
        st.info("Nenhum módulo ativo para relatar.")[cite: 1]
    else:
        lista_plana = [][cite: 1]
        for d in dados_venc:[cite: 1]
            try:
                nome_fer = d.get('ferramentas', {}).get('nome') if d.get('ferramentas') else f"Ferramenta ID {d.get('ferramenta_id')}"[cite: 1]
                
                dados_cli = d.get('licencas', {}).get('clientes') or {}[cite: 1]
                cliente_nome = dados_cli.get('razao_social')[cite: 1]
                telefone_cli = dados_cli.get('telefone')[cite: 1]
                
                if not cliente_nome or str(cliente_nome).lower() == 'nan':[cite: 1]
                    cliente_nome = f"Cliente (CNPJ: {d['licencas']['cnpj']})"[cite: 1]
                
                if not telefone_cli or str(telefone_cli).lower() == 'nan':[cite: 1]
                    telefone_cli = ""[cite: 1]

                lista_plana.append({
                    "id_relacao": d['id'],
                    "ferramenta": nome_fer,
                    "data_exp": d['data_expiracao'],
                    "cnpj": d['licencas']['cnpj'],
                    "hwid": d['licencas']['hwid'],
                    "cliente": cliente_nome,
                    "telefone": telefone_cli
                })[cite: 1]
            except Exception as e: 
                pass[cite: 1]
            
        if lista_plana:
            df_venc = pd.DataFrame(lista_plana)[cite: 1]
            hoje = datetime.date.today()[cite: 1]
            df_venc['data_exp_dt'] = pd.to_datetime(df_venc['data_exp']).dt.date[cite: 1]
            df_venc['dias_restantes'] = (df_venc['data_exp_dt'] - hoje).apply(lambda x: x.days)[cite: 1]
            
            df_filtrado = df_venc.sort_values(by="dias_restantes")[cite: 1]
            
            for index, row in df_filtrado.iterrows():[cite: 1]
                dias = row['dias_restantes'][cite: 1]
                
                if dias <= 20:[cite: 1]
                    cor = "red" if dias < 0 else ("orange" if dias == 0 else "green")[cite: 1]
                    status = f"Vencida há {abs(dias)} dias" if dias < 0 else ("Vence HOJE!" if dias == 0 else f"Vence em {dias} dias")[cite: 1]

                    with st.container(border=True):[cite: 1]
                        col_i, col_m, col_w = st.columns([3, 4, 3]) # Ajuste de largura
                        with col_i:
                            st.markdown(f"🏢 **{row['cliente']}**")[cite: 1]
                            st.markdown(f"🛠️ Módulo: {row['ferramenta']}")[cite: 1]
                        with col_m:
                            st.markdown(f"<br>⏳ **Status:** :{cor}[{status}] (Validade: {row['data_exp_dt'].strftime('%d/%m/%Y')})", unsafe_allow_html=True)[cite: 1]
                        with col_w:
                            st.markdown("<br>", unsafe_allow_html=True)
                            if row['telefone']:[cite: 1]
                                numero_limpo = re.sub(r'\D', '', str(row['telefone']))[cite: 1]
                                msg = f"Olá {row['cliente']}! A licença do módulo *{row['ferramenta']}* expira em {dias} dias. Deseja agilizar a renovação?" if dias > 0 else f"Olá {row['cliente']}! A licença do módulo *{row['ferramenta']}* expirou. Vamos renovar?"[cite: 1]
                                st.link_button("💬 Cobrar no WhatsApp", f"https://wa.me/{numero_limpo}?text={urllib.parse.quote(msg)}", use_container_width=True)[cite: 1]
                            else:
                                st.warning("⚠️ Cliente sem WhatsApp")[cite: 1]

# ==========================================
# ABA 6: AUDITORIA (LOGS E CONSUMO)
# ==========================================
with aba_acessos:
    col_aud1, col_aud2 = st.columns([4, 1])
    col_aud1.subheader("📡 Logs de Acesso, Máquinas e Consumo")[cite: 1]
    if col_aud2.button("🔄 Atualizar Tabela", use_container_width=True):[cite: 1]
        st.rerun()[cite: 1]
        
    try:
        resp_acessos = supabase.table("acessos_clientes").select("*").order("data_ultimo_acesso", desc=True).execute()[cite: 1]
        
        if resp_acessos.data:[cite: 1]
            df_acessos = pd.DataFrame(resp_acessos.data)[cite: 1]
            
            if not df_cli.empty:[cite: 1]
                df_acessos = pd.merge(df_acessos, df_cli[['cnpj', 'razao_social']], on='cnpj', how='left')[cite: 1]
            else:
                df_acessos['razao_social'] = "Desconhecido"[cite: 1]
            
            colunas_ordem = ["cnpj", "razao_social", "maquina", "versao_atual", "usos_ia_hoje", "editais_baixados", "data_ultimo_acesso"][cite: 1]
            df_acessos = df_acessos[[c for c in colunas_ordem if c in df_acessos.columns]][cite: 1]
            
            df_acessos["data_ultimo_acesso"] = pd.to_datetime(df_acessos["data_ultimo_acesso"]).dt.tz_localize(None) - pd.Timedelta(hours=3)[cite: 1]
            
            with st.container(border=True):
                st.dataframe(
                    df_acessos, 
                    column_config={
                        "cnpj": "CNPJ", 
                        "razao_social": "Cliente", 
                        "maquina": "Computador (ID)", 
                        "versao_atual": "Versão do App", 
                        "usos_ia_hoje": "Análises IA (Hoje)", 
                        "editais_baixados": "Editais Sincronizados",[cite: 1]
                        "data_ultimo_acesso": st.column_config.DatetimeColumn("Último Ping", format="DD/MM/YYYY HH:mm:ss")[cite: 1]
                    }, 
                    use_container_width=True, 
                    hide_index=True[cite: 1]
                )
        else:
            st.info("Nenhum log de acesso registrado pelas máquinas ainda.")[cite: 1]
            
    except Exception as e:
        st.error(f"Erro ao processar os logs de auditoria: {e}")[cite: 1]

# ==========================================
# ABA 7: SISTEMA & IA
# ==========================================
with aba_versoes:
    st.subheader("🚀 Atualizações (OTA) e Chaves de IA")[cite: 1]
    try:
        dados_v = supabase.table("controle_versoes").select("*").eq("id", 1).single().execute().data[cite: 1]
        if dados_v:
            with st.container(border=True):
                with st.form("form_versoes"):[cite: 1]
                    st.markdown("**1. Atualizações Obrigatórias do Executável**")[cite: 1]
                    c_v1, c_v2 = st.columns(2)
                    v_atual = c_v1.text_input("Versão Atual (Mais Recente)", value=dados_v.get("versao_atual", ""))[cite: 1]
                    v_minima = c_v2.text_input("Versão Mínima Obrigatória", value=dados_v.get("versao_minima_obrigatoria", ""))[cite: 1]
                    url_down = st.text_input("Link de Download Direto do .exe", value=dados_v.get("url_download", ""))[cite: 1]
                    
                    st.divider()
                    st.markdown("**2. Inteligência Artificial (Global)**")[cite: 1]
                    c_dots = st.text_input("Chave API: DOTS (OpenRouter)", value=dados_v.get("chave_dots", ""), type="password")[cite: 1]
                    c_gemini = st.text_input("Chave API: Google Gemini (Fallback)", value=dados_v.get("chave_gemini", ""), type="password")[cite: 1]
                    
                    if st.form_submit_button("💾 Salvar Configurações na Nuvem", type="primary"):[cite: 1]
                        supabase.table("controle_versoes").update({
                            "versao_atual": v_atual, "versao_minima_obrigatoria": v_minima, "url_download": url_down,[cite: 1]
                            "chave_dots": c_dots, "chave_gemini": c_gemini[cite: 1]
                        }).eq("id", 1).execute()[cite: 1]
                        st.success("✅ Configurações e Chaves guardadas com segurança!")[cite: 1]
                        st.rerun()[cite: 1]
    except Exception as e:
        st.error(f"Erro ao carregar configurações globais: {e}")[cite: 1]