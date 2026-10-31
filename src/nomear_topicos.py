"""Dá nomes legíveis aos tópicos do BERTopic usando o Gemini.

O BERTopic descreve cada tópico por palavras soltas. Enquanto, aqui o LLM recebe essas palavras e 
alguns títulos de trabalhos do tópico e propõe um nome curto usado nos gráficos e no app.

Uso (a partir da raiz do repositório, depois do notebook 02):
    python src/nomear_topicos.py
"""

import sys
import time
from pathlib import Path

import pandas as pd
from pydantic import BaseModel, Field

from llm import PAUSA_ENTRE_CHAMADAS, criar_cliente, gerar_json, ler_cache, salvar_no_cache

PROCESSADOS = Path("data/processed")
RELATORIOS = Path("reports")
CACHE = PROCESSADOS / "nomes_topicos.jsonl"
SAIDA = RELATORIOS / "topicos_nomeados.csv"

TITULOS_POR_TOPICO = 6
TOPICOS_POR_CHAMADA = 10
SEMENTE = 42


class Nome(BaseModel):
    topico: int
    nome: str = Field(description="Nome curto do tema, de 2 a 5 palavras, em português")
    descricao: str = Field(description="Uma frase descrevendo o que os trabalhos estudam")


class Lote(BaseModel):
    nomes: list[Nome]


INSTRUCOES = """Você vai nomear temas de pesquisa encontrados em teses e dissertações brasileiras
de Ciência da Computação. Cada tema vem com suas palavras mais características (já reduzidas à
forma base, então podem soar estranhas, como "dado rotular") e alguns títulos de trabalhos.

Para cada tema, dê:
- nome: de 2 a 5 palavras, como o nome de uma linha de pesquisa (ex.: "Visão computacional",
  "Engenharia de requisitos"). Não use as palavras "estudo" ou "pesquisa".
- descricao: uma frase dizendo o que os trabalhos desse tema estudam.

Use o mesmo número de tema recebido.

Temas:
"""


def main() -> int:
    info = pd.read_csv(RELATORIOS / "topicos_bertopic.csv")
    trabalhos = pd.read_csv(PROCESSADOS / "topicos_bertopic.csv.gz", usecols=["id", "topico"])
    titulos = pd.read_csv(PROCESSADOS / "resumos_preprocessados.csv.gz", usecols=["titulo"])["titulo"]

    feitos = {registro["topico"] for registro in ler_cache(CACHE)}
    pendentes = info[~info["tópico"].isin(feitos)]
    print(f"{len(info)} tópicos; {len(pendentes)} sem nome")

    if not pendentes.empty:
        cliente = criar_cliente()
        for inicio in range(0, len(pendentes), TOPICOS_POR_CHAMADA):
            lote = pendentes.iloc[inicio:inicio + TOPICOS_POR_CHAMADA]
            blocos = []
            for linha in lote.itertuples():
                ids = trabalhos.loc[trabalhos["topico"] == linha.tópico, "id"]
                exemplos = titulos.loc[ids.sample(min(TITULOS_POR_TOPICO, len(ids)),
                                                  random_state=SEMENTE)]
                lista = "\n".join(f"  - {t}" for t in exemplos)
                blocos.append(f"[tema {linha.tópico}] palavras: {linha.palavras}\n{lista}")
            resposta = gerar_json(cliente, INSTRUCOES + "\n\n".join(blocos), Lote)

            esperados = set(lote["tópico"])
            validos = [n.model_dump() for n in resposta.nomes if n.topico in esperados]
            salvar_no_cache(CACHE, validos)
            print(f"Lote {inicio // TOPICOS_POR_CHAMADA + 1}: {len(validos)}/{len(lote)} nomeados")
            time.sleep(PAUSA_ENTRE_CHAMADAS)

    nomes = pd.DataFrame(ler_cache(CACHE)).drop_duplicates("topico", keep="last")
    tabela = info.merge(nomes, left_on="tópico", right_on="topico", how="left").drop(columns="topico")
    tabela.to_csv(SAIDA, index=False)
    print(f"Salvo em {SAIDA}")
    print(tabela[["tópico", "trabalhos", "nome"]].head(15).to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
