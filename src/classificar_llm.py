"""Classifica uma amostra de resumos com o Gemini: 

O léxico só detecta palavras. Um trabalho pode citar "redes neurais" apenas
como contexto, ou usar IA sem nenhum dos termos da lista. Aqui o LLM lê o resumo inteiro e
decide, para depois compararmos as duas abordagens no notebook 04.

Para economizar chamadas, cada pedido leva 10 resumos. As respostas ficam salvas em
data/processed/classificacao_llm.jsonl: se o script parar no meio, basta rodar de novo que ele
continua de onde parou.

Uso (a partir da raiz do repositório):
    python src/classificar_llm.py
"""

import sys
import time
from pathlib import Path
from typing import Literal

import pandas as pd
from pydantic import BaseModel, Field

from llm import PAUSA_ENTRE_CHAMADAS, criar_cliente, gerar_json, ler_cache, salvar_no_cache

PROCESSADOS = Path("data/processed")
SAIDA = PROCESSADOS / "classificacao_llm.jsonl"

POR_ANO = 20       
POR_CHAMADA = 10
SEMENTE = 42


class Classificacao(BaseModel):
    id: int
    usa_ia: bool = Field(description="O trabalho desenvolve ou aplica técnicas de IA?")
    papel_ia: Literal["metodo_principal", "ferramenta_de_apoio", "apenas_mencao", "nao_usa"] = Field(
        description="Papel da IA no trabalho")
    familia: Literal["aprendizado_maquina", "aprendizado_profundo", "modelos_linguagem",
                     "ia_simbolica", "nenhuma"] = Field(
        description="Principal família de técnica de IA usada")
    justificativa: str = Field(description="Uma frase curta explicando a decisão")


class Lote(BaseModel):
    classificacoes: list[Classificacao]


INSTRUCOES = """Você é especialista em Ciência da Computação e vai classificar resumos de teses e
dissertações brasileiras. Para cada resumo, responda:

- usa_ia: true se o trabalho desenvolve ou aplica técnicas de Inteligência Artificial
  (aprendizado de máquina, redes neurais, aprendizado profundo, modelos de linguagem, sistemas
  multiagentes, raciocínio automático, busca heurística, algoritmos evolutivos etc.).
  false se a IA só aparece como contexto ou não aparece.
- papel_ia:
  - "metodo_principal": a contribuição central do trabalho é uma técnica de IA;
  - "ferramenta_de_apoio": a IA é usada para resolver um problema de outra área;
  - "apenas_mencao": a IA é citada, mas não é usada;
  - "nao_usa": não há IA.
- familia: a principal família de técnica usada ("ia_simbolica" para lógica, ontologias,
  planejamento, agentes e busca; "nenhuma" se não usa IA).
- justificativa: uma frase curta, em português.

Responda com uma classificação para cada resumo, usando o mesmo id recebido.

Resumos:
"""


def montar_amostra() -> pd.DataFrame:
    trabalhos = pd.read_csv(PROCESSADOS / "ia_lexico.csv.gz")
    textos = pd.read_csv(PROCESSADOS / "resumos_preprocessados.csv.gz", usecols=["texto_limpo"])
    amostra = trabalhos.groupby("ano").sample(n=POR_ANO, random_state=SEMENTE)
    amostra["texto"] = textos.loc[amostra["id"], "texto_limpo"].to_numpy()
    return amostra


def main() -> int:
    amostra = montar_amostra()
    feitos = {registro["id"] for registro in ler_cache(SAIDA)}
    pendentes = amostra[~amostra["id"].isin(feitos)]
    print(f"Amostra de {len(amostra)} resumos; {len(feitos)} já classificados, "
          f"{len(pendentes)} pendentes")
    if pendentes.empty:
        return 0

    cliente = criar_cliente()
    for inicio in range(0, len(pendentes), POR_CHAMADA):
        lote = pendentes.iloc[inicio:inicio + POR_CHAMADA]
        prompt = INSTRUCOES + "\n\n".join(f"[id {r.id}] {r.texto}" for r in lote.itertuples())
        resposta = gerar_json(cliente, prompt, Lote)

        esperados = set(lote["id"])
        validos = [c.model_dump() for c in resposta.classificacoes if c.id in esperados]
        salvar_no_cache(SAIDA, validos)
        print(f"Lote {inicio // POR_CHAMADA + 1}: {len(validos)}/{len(lote)} classificados")
        time.sleep(PAUSA_ENTRE_CHAMADAS)

    respondidos = {registro["id"] for registro in ler_cache(SAIDA)}
    faltando = len(set(amostra["id"]) - respondidos)
    if faltando:
        print(f"{faltando} resumos ficaram sem resposta; rode de novo para completar.")
    print(f"Respostas em {SAIDA}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
