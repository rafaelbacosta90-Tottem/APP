import streamlit as st
from supabase import create_client, Client
import datetime

# --- Configuração da Página ---
st.set_page_config(page_title="Gestão de Licenças", layout="wide")

# --- Conexão com Supabase ---
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

# --- Menu Lateral ---
st.sidebar.title("Menu")
opcao = st.sidebar.radio("Selecione a tela:", ["Cadastro de Licença", "Administração"])

# --- Tela 1: Cadastro ---
if opcao == "Cadastro de Licença":
    st.title("Cadastrar Nova Licença")
    
    with st.form("form_cadastro"):
        col1, col2 = st.columns(2)
        with col1:
            cnpj = st.text_input("CNPJ (Apenas números)", max_chars=14)
            hwid = st.text_input("HWID (Identificador da Máquina)")
        with col2:
            data_expiracao = st.date_input("Data de Expiração", min_value=datetime.date.today())
            ativa = st.checkbox("Ativar licença imediatamente?", value=True)
            
        submit = st.form_submit_button("Salvar Licença")
        
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
                    st.success(f"Licença para o CNPJ {cnpj} cadastrada com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao salvar no banco de dados. Detalhes: {e}")

# --- Tela 2: Administração ---
elif opcao == "Administração":
    st.title("Administração de Licenças")
    
    # Busca os dados na tabela 'licencas'
    try:
        # Usamos order('id') para manter a tabela organizada
        resposta = supabase.table("licencas").select("*").order("id").execute()
        dados_licencas = resposta.data
        
        if not dados_licencas:
            st.info("Nenhuma licença cadastrada ainda.")
        else:
            # Exibe os dados em uma tabela interativa
            st.subheader("Licenças Atuais")
            st.dataframe(
                dados_licencas,
                column_config={
                    "id": "ID",
                    "cnpj": "CNPJ",
                    "hwid": "HWID",
                    "data_expiracao": st.column_config.DateColumn("Expiração", format="DD/MM/YYYY"),
                    "ativa": st.column_config.CheckboxColumn("Ativa?"),
                    "created_at": st.column_config.DatetimeColumn("Criada em", format="DD/MM/YYYY HH:mm")
                },
                hide_index=True,
                use_container_width=True
            )
            
            st.divider()
            
            # Área para alterar o status rapidamente
            st.subheader("Alterar Status da Licença")
            col_a, col_b, col_c = st.columns([2, 2, 1])
            
            # Cria lista usando o ID da licença (para o caso de um cliente ter mais de uma)
            lista_licencas = [f"{c['id']} - CNPJ: {c['cnpj']}" for c in dados_licencas]
            
            with col_a:
                selecao = st.selectbox("Selecione a Licença (pelo ID):", lista_licencas)
                id_selecionado = selecao.split(" - ")[0] if selecao else None
                
            with col_b:
                novo_status = st.radio("Definir Licença como:", ["Ativa", "Inativa"], horizontal=True)
                
            with col_c:
                st.write("") # Espaçamento
                st.write("")
                if st.button("Atualizar Status", type="primary"):
                    status_bool = True if novo_status == "Ativa" else False
                    supabase.table("licencas").update({"ativa": status_bool}).eq("id", id_selecionado).execute()
                    st.success("Status atualizado! Recarregue a página para ver a mudança na tabela.")
                    
    except Exception as e:
        st.error(f"Erro ao buscar dados do Supabase: {e}")