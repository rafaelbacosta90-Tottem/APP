import streamlit as st
from supabase import create_client, Client
import datetime

# --- Configuração da Página ---
st.set_page_config(page_title="Gestão de Licenças", layout="wide")

# --- Conexão com Supabase ---
# O Streamlit buscará essas chaves na configuração de Secrets da nuvem
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

# --- Menu Lateral ---
st.sidebar.title("Menu")
opcao = st.sidebar.radio("Selecione a tela:", ["Cadastro", "Administração"])

# --- Tela 1: Cadastro ---
if opcao == "Cadastro":
    st.title("Cadastrar Novo Cliente")
    
    with st.form("form_cadastro"):
        col1, col2 = st.columns(2)
        with col1:
            cnpj = st.text_input("CNPJ (Apenas números)", max_chars=14)
            vencimento = st.date_input("Data de Vencimento da Licença", min_value=datetime.date.today())
        with col2:
            razao_social = st.text_input("Razão Social do Cliente")
            licenca_ativa = st.checkbox("Ativar licença imediatamente?", value=True)
            
        submit = st.form_submit_button("Salvar Cliente")
        
        if submit:
            if not cnpj.isdigit() or len(cnpj) != 14:
                st.error("Por favor, insira um CNPJ válido com 14 números.")
            elif not razao_social:
                st.error("A Razão Social é obrigatória.")
            else:
                try:
                    novo_cliente = {
                        "cnpj": cnpj,
                        "razao_social": razao_social,
                        "vencimento": str(vencimento),
                        "licenca_ativa": licenca_ativa
                    }
                    supabase.table("clientes").insert(novo_cliente).execute()
                    st.success(f"Cliente {razao_social} cadastrado com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao salvar: O CNPJ já existe ou houve falha de conexão. Detalhes: {e}")

# --- Tela 2: Administração ---
elif opcao == "Administração":
    st.title("Administração de Licenças")
    
    # Busca os dados no Supabase
    try:
        resposta = supabase.table("clientes").select("*").execute()
        dados_clientes = resposta.data
        
        if not dados_clientes:
            st.info("Nenhum cliente cadastrado ainda.")
        else:
            # Exibe os dados em uma tabela interativa
            st.subheader("Clientes Cadastrados")
            st.dataframe(
                dados_clientes,
                column_config={
                    "cnpj": "CNPJ",
                    "razao_social": "Razão Social",
                    "vencimento": st.column_config.DateColumn("Vencimento", format="DD/MM/YYYY"),
                    "licenca_ativa": st.column_config.CheckboxColumn("Licença Ativa?")
                },
                hide_index=True,
                use_container_width=True
            )
            
            st.divider()
            
            # Área para alterar o status rapidamente
            st.subheader("Alterar Status da Licença")
            col_a, col_b, col_c = st.columns([2, 2, 1])
            
            # Cria lista de CNPJs para o SelectBox
            lista_cnpjs = [f"{c['cnpj']} - {c['razao_social']}" for c in dados_clientes]
            
            with col_a:
                selecao = st.selectbox("Selecione o Cliente:", lista_cnpjs)
                cnpj_selecionado = selecao.split(" - ")[0] if selecao else None
                
            with col_b:
                novo_status = st.radio("Definir Licença como:", ["Ativa", "Inativa"], horizontal=True)
                
            with col_c:
                st.write("") # Espaçamento
                st.write("")
                if st.button("Atualizar Status", type="primary"):
                    status_bool = True if novo_status == "Ativa" else False
                    supabase.table("clientes").update({"licenca_ativa": status_bool}).eq("cnpj", cnpj_selecionado).execute()
                    st.success("Status atualizado! Recarregue a página para ver na tabela.")
                    
    except Exception as e:
        st.error(f"Erro ao buscar dados do Supabase: {e}")