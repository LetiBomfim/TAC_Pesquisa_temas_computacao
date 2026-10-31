"""App para explorar a evolução temática das teses e dissertações de Computação (2010–2024).

Para rodar no seu computador (a partir da raiz do repositório):
    pip install -r app/requirements.txt
    streamlit run app/app.py

O app só lê arquivos já processados pelos scripts e notebooks do projeto. Nada é recalculado
aqui, o que o deixa leve o bastante para rodar de graça no Streamlit Community Cloud.
"""

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

RAIZ = Path(__file__).resolve().parent.parent
PROCESSADOS = RAIZ / "data" / "processed"
RELATORIOS = RAIZ / "reports"

AZUL, LARANJA, VERDE, VERMELHO = "#2a78d6", "#eb6834", "#1baf7a", "#e34948"
CORES_GRAU = {"Mestrado": AZUL, "Doutorado": LARANJA, "Mestrado Profissional": VERDE}
NOMES_FAMILIAS = {
    "aprendizado_maquina": "Aprendizado de máquina",
    "aprendizado_profundo": "Aprendizado profundo",
    "modelos_linguagem": "Modelos de linguagem",
}

st.set_page_config(page_title="Teses de Computação no Brasil", page_icon="🎓", layout="wide")


# --------------------------------------------------------------------------------------------
# Dados
# --------------------------------------------------------------------------------------------

@st.cache_data
def carregar_dados() -> tuple[pd.DataFrame, pd.DataFrame]:
    trabalhos = pd.read_csv(PROCESSADOS / "ia_lexico.csv.gz")
    base = pd.read_csv(PROCESSADOS / "teses_computacao_2010_2024.csv.gz",
                       usecols=["titulo", "resumo", "ies_sigla", "programa"])
    trabalhos = trabalhos.join(base, on="id")

    temas = pd.read_csv(RELATORIOS / "topicos_bertopic.csv")
    nomes = RELATORIOS / "topicos_nomeados.csv"
    if nomes.exists():  # nomes gerados pelo LLM (src/nomear_topicos.py), se já existirem
        temas = temas.merge(pd.read_csv(nomes)[["tópico", "nome"]], on="tópico", how="left")
    else:
        temas["nome"] = None
    palavras = temas["palavras"].str.split(", ").str[:3].str.join(", ")
    temas["rotulo"] = temas["nome"].fillna(palavras)
    repetidos = temas["rotulo"].duplicated(keep=False)
    temas.loc[repetidos, "rotulo"] += " (" + temas.loc[repetidos, "tópico"].astype(str) + ")"

    trabalhos = trabalhos.merge(temas[["tópico", "rotulo"]], left_on="topico",
                                right_on="tópico", how="left").drop(columns="tópico")
    return trabalhos, temas


def grafico_linhas(dados: pd.DataFrame, titulo: str, cor=None, cores=None):
    figura = px.line(dados, x="ano", y="valor", color=cor, color_discrete_map=cores,
                     markers=True, template="simple_white")
    figura.update_traces(line_width=2.5)
    figura.update_layout(title=titulo, xaxis_title=None, yaxis_title=None, legend_title=None,
                         hovermode="x unified", margin=dict(t=50, l=10, r=10, b=10),
                         yaxis=dict(ticksuffix="%", rangemode="tozero", gridcolor="rgba(128, 128, 128, 0.25)",
                                    showgrid=True))
    if cor is None:
        figura.update_traces(line_color=AZUL)
    return figura


trabalhos, temas = carregar_dados()

# --------------------------------------------------------------------------------------------
# Cabeçalho
# --------------------------------------------------------------------------------------------

st.title("Evolução temática da pós-graduação em Computação no Brasil")
st.caption("Teses e dissertações do Catálogo da CAPES, 2010–2024. "
           "[Código e metodologia no GitHub](https://github.com/LetiBomfim/TAC_Pesquisa_temas_computacao)")

ia_por_ano = trabalhos.groupby("ano")["ia"].mean() * 100
col1, col2, col3, col4 = st.columns(4)
col1.metric("Trabalhos analisados", f"{len(trabalhos):,}".replace(",", "."))
col2.metric("Temas encontrados", len(temas))
col3.metric("Citam IA em 2010", f"{ia_por_ano.iloc[0]:.0f}%")
col4.metric("Citam IA em 2024", f"{ia_por_ano.iloc[-1]:.0f}%",
            delta=f"{ia_por_ano.iloc[-1] - ia_por_ano.iloc[0]:+.0f} p.p.")

aba_ia, aba_temas, aba_busca = st.tabs(["Ascensão da IA", "Temas", "Explorar trabalhos"])

# --------------------------------------------------------------------------------------------
# Aba 1: IA ao longo do tempo
# --------------------------------------------------------------------------------------------

with aba_ia:
    st.markdown("Um trabalho conta como **de IA** quando o resumo cita termos técnicos da área "
                "(veja `src/lexico_ia.py`). O crescimento acelerou a partir de **2018**.")
    st.caption("Esses valores são um piso: na auditoria com LLM, o léxico deixou de fora parte dos "
               "trabalhos de IA, principalmente nos primeiros anos. Detalhes no README do projeto.")

    serie = ia_por_ano.rename("valor").reset_index()
    st.plotly_chart(grafico_linhas(serie, "Trabalhos que citam IA (% do total do ano)"),
                    width="stretch")

    esquerda, direita = st.columns(2)
    with esquerda:
        familias = (trabalhos.groupby("ano")[list(NOMES_FAMILIAS)].mean() * 100).reset_index()
        familias = familias.melt(id_vars="ano", var_name="familia", value_name="valor")
        familias["familia"] = familias["familia"].map(NOMES_FAMILIAS)
        cores = dict(zip(NOMES_FAMILIAS.values(), (AZUL, LARANJA, VERDE)))
        st.plotly_chart(grafico_linhas(familias, "Por família de termos (%)", "familia", cores),
                        width="stretch")
    with direita:
        graus = trabalhos[trabalhos["grau"].isin(CORES_GRAU)]
        por_grau = (graus.groupby(["ano", "grau"])["ia"].mean() * 100).rename("valor").reset_index()
        st.plotly_chart(grafico_linhas(por_grau, "Por grau (%)", "grau", CORES_GRAU),
                        width="stretch")

# --------------------------------------------------------------------------------------------
# Aba 2: temas
# --------------------------------------------------------------------------------------------

with aba_temas:
    variacao_arquivo = RELATORIOS / "variacao_topicos.csv"
    if variacao_arquivo.exists():
        variacao = pd.read_csv(variacao_arquivo).merge(temas[["tópico", "rotulo"]], on="tópico")
        destaque = pd.concat([variacao.head(8), variacao.tail(8)])
        destaque["direção"] = destaque["variação (p.p.)"].map(lambda v: "ganhou" if v > 0 else "perdeu")
        figura = px.bar(destaque, x="variação (p.p.)", y="rotulo", color="direção", orientation="h",
                        color_discrete_map={"ganhou": AZUL, "perdeu": VERMELHO},
                        template="simple_white")
        figura.update_layout(title="Temas que mais ganharam e perderam espaço (2010–2014 → 2020–2024)",
                             yaxis_title=None, xaxis_title="pontos percentuais", showlegend=False,
                             height=520, margin=dict(t=50, l=10, r=10, b=10))
        st.plotly_chart(figura, width="stretch")

    st.subheader("Evolução de um tema")
    opcoes = temas.sort_values("trabalhos", ascending=False)
    escolhido = st.selectbox("Escolha um tema", opcoes["tópico"],
                             format_func=lambda t: opcoes.set_index("tópico").loc[t, "rotulo"])
    linha = temas.set_index("tópico").loc[escolhido]

    fatia = (trabalhos.assign(no_tema=trabalhos["topico"] == escolhido)
             .groupby("ano")["no_tema"].mean() * 100).rename("valor").reset_index()
    esquerda, direita = st.columns([2, 1])
    with esquerda:
        st.plotly_chart(grafico_linhas(fatia, "Fatia dos trabalhos no tema (%)"),
                        width="stretch")
    with direita:
        st.metric("Trabalhos no tema", f"{int(linha['trabalhos']):,}".replace(",", "."))
        st.markdown(f"**Palavras mais características:** {linha['palavras']}")
        exemplos = trabalhos.loc[trabalhos["topico"] == escolhido].sort_values("ano", ascending=False)
        st.markdown("**Trabalhos recentes:**")
        for item in exemplos.head(5).itertuples():
            st.markdown(f"- {item.titulo.strip().capitalize()} ({item.ies_sigla}, {item.ano})")

# --------------------------------------------------------------------------------------------
# Aba 3: busca
# --------------------------------------------------------------------------------------------

with aba_busca:
    filtro1, filtro2, filtro3 = st.columns(3)
    anos = filtro1.slider("Anos", 2010, 2024, (2010, 2024))
    graus_escolhidos = filtro2.multiselect("Grau", sorted(trabalhos["grau"].unique()))
    regioes = filtro3.multiselect("Região", sorted(trabalhos["regiao"].unique()))
    termo = st.text_input("Buscar no título", placeholder="ex.: redes neurais, blockchain, ensino")
    so_ia = st.checkbox("Só trabalhos que citam IA")

    filtrados = trabalhos[trabalhos["ano"].between(*anos)]
    if graus_escolhidos:
        filtrados = filtrados[filtrados["grau"].isin(graus_escolhidos)]
    if regioes:
        filtrados = filtrados[filtrados["regiao"].isin(regioes)]
    if termo:
        filtrados = filtrados[filtrados["titulo"].str.contains(termo, case=False, na=False, regex=False)]
    if so_ia:
        filtrados = filtrados[filtrados["ia"]]

    st.caption(f"{len(filtrados):,} trabalhos encontrados".replace(",", "."))
    tabela = filtrados[["ano", "titulo", "grau", "ies_sigla", "regiao", "rotulo"]].rename(columns={
        "titulo": "Título", "ano": "Ano", "grau": "Grau", "ies_sigla": "Instituição",
        "regiao": "Região", "rotulo": "Tema"})
    st.dataframe(tabela.sort_values("Ano", ascending=False), hide_index=True,
                 width="stretch", height=420)
