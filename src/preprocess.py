"""Prepara os resumos para a modelagem de tópicos.

Etapas:
1. Marca resumos que não devem entrar na análise de texto:
   - escritos em inglês (a análise é feita em português);
   - corrompidos (o mesmo trecho repetido várias vezes, erro comum na base da CAPES);
   - duplicados (o mesmo resumo cadastrado em mais de um trabalho).
2. Gera duas versões do texto:
   - texto_limpo: minúsculas, sem URLs e espaços extras. Entrada do BERTopic e do LLM,
     que funcionam melhor com o texto quase original.
   - texto_lematizado: só substantivos, adjetivos e verbos, na forma base (lema) e sem
     stopwords. Entrada do LDA, que trabalha com contagem de palavras.

"""

import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

import pandas as pd
import spacy
from tqdm import tqdm

ENTRADA = Path("data/processed/teses_computacao_2010_2024.csv.gz")
SAIDA = Path("data/processed/resumos_preprocessados.csv.gz")

LIMITE_REPETICAO = 0.2 
CLASSES_MANTIDAS = {"NOUN", "PROPN", "ADJ", "VERB"}

PALAVRAS_PT = {"de", "que", "uma", "para", "com", "os", "das", "dos", "não", "em"}
PALAVRAS_EN = {"the", "and", "of", "this", "which", "with", "is", "are", "to", "in"}

# Palavras que aparecem em quase todo resumo acadêmico e não dizem nada sobre o tema.
STOPWORDS_DOMINIO = {
    "trabalho", "pesquisa", "dissertação", "tese", "estudo", "resultado", "objetivo",
    "proposta", "propor", "apresentar", "abordagem", "método", "metodologia", "análise",
    "analisar", "utilizar", "usar", "uso", "utilização", "realizar", "permitir", "obter",
    "mostrar", "demonstrar", "avaliar", "avaliação", "desenvolver", "desenvolvimento",
    "base", "partir", "forma", "meio", "processo", "problema", "solução", "parte",
    "caso", "tipo", "área", "contexto", "aspecto", "exemplo", "capítulo", "seção",
    "presente", "principal", "diferente", "possível", "novo", "grande", "melhor",
    "existir", "existente", "ser", "ter", "haver", "poder", "dever", "fazer",
    "considerar", "possuir", "tornar", "buscar", "visar", "levar", "ficar", "indicar",
    "seguinte", "relação", "ponto", "vista", "maneira", "termo", "nível", "ano",
    "basear", "aplicar", "gerar", "literatura", "identificar", "alto", "real",
    "encontrar", "capaz", "comparar", "importante", "entanto", "necessário",
    "necessidade", "desafio", "melhorar", "relacionar", "definir", "criar", "fornecer",
    "auxiliar", "representar", "conceito", "reduzir", "aumentar", "pequeno", "envolver",
    "quantidade", "específico", "eficiente", "complexo", "proposto", "diverso",
    "experimento", "experimental", "atual", "comum", "importância", "objetivar",
}
MIN_OCORRENCIAS_SINGULAR = 20


def detectar_idioma(texto: str) -> str:
    """Conta palavras muito comuns de cada idioma."""
    palavras = re.findall(r"\w+", texto.lower())
    pt = sum(p in PALAVRAS_PT for p in palavras)
    en = sum(p in PALAVRAS_EN for p in palavras)
    return "en" if en > pt else "pt"


def taxa_repeticao(texto: str) -> float:
    """Fração de trechos de 3 palavras que já apareceram antes no mesmo texto."""
    palavras = texto.lower().split()
    trigramas = list(zip(palavras, palavras[1:], palavras[2:]))
    if not trigramas:
        return 0.0
    return 1 - len(set(trigramas)) / len(trigramas)


def chave_texto(texto: str) -> str:
    """Versão sem acentos, pontuação e caixa, para achar resumos iguais."""
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"\W+", " ", sem_acento.lower()).strip()


def limpar_texto(texto: str) -> str:
    texto = texto.lower()
    texto = re.sub(r"https?://\S+|www\.\S+|\S+@\S+", " ", texto)
    return " ".join(texto.split())


def marcar_qualidade(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["idioma"] = df["resumo"].map(detectar_idioma)
    df["corrompido"] = df["resumo"].map(taxa_repeticao) > LIMITE_REPETICAO
    df["duplicado"] = df["resumo"].map(chave_texto).duplicated(keep=False)
    df["apto_texto"] = (df["idioma"] == "pt") & ~df["corrompido"] & ~df["duplicado"]
    return df


def lematizar(textos: list[str], nlp) -> list[str]:
    stopwords = nlp.Defaults.stop_words | STOPWORDS_DOMINIO
    resultado = []
    documentos = nlp.pipe(textos, batch_size=200)
    for doc in tqdm(documentos, total=len(textos), desc="Lematizando"):
        lemas = [
            t.lemma_.lower()
            for t in doc
            if t.pos_ in CLASSES_MANTIDAS
            and t.is_alpha
            and len(t.lemma_) > 2
            and t.lemma_.lower() not in stopwords
        ]
        resultado.append(" ".join(lemas))
    return unificar_plurais(resultado, stopwords)


def unificar_plurais(textos: list[str], stopwords: set[str]) -> list[str]:
    contagem = Counter(palavra for texto in textos for palavra in texto.split())
    troca = {
        palavra: palavra[:-1]
        for palavra in contagem
        if palavra.endswith("s")
        and len(palavra) > 4
        and contagem.get(palavra[:-1], 0) >= MIN_OCORRENCIAS_SINGULAR
    }
    return [
        " ".join(p for p in (troca.get(palavra, palavra) for palavra in texto.split())
                 if p not in stopwords)
        for texto in textos
    ]


def main() -> int:
    if not ENTRADA.exists():
        print(f"Base não encontrada em {ENTRADA}. Rode antes: python src/build_dataset.py")
        return 1

    df = marcar_qualidade(pd.read_csv(ENTRADA))
    print(f"{len(df)} trabalhos na base")
    print(f"  em inglês:   {(df['idioma'] == 'en').sum()}")
    print(f"  corrompidos: {df['corrompido'].sum()}")
    print(f"  duplicados:  {df['duplicado'].sum()}")
    print(f"  aptos para análise de texto: {df['apto_texto'].sum()}")

    df["texto_limpo"] = df["resumo"].map(limpar_texto)
    
    nlp = spacy.load("pt_core_news_sm", disable=["parser", "ner"])
    aptos = df["apto_texto"]
    df["texto_lematizado"] = ""
    df.loc[aptos, "texto_lematizado"] = lematizar(df.loc[aptos, "texto_limpo"].tolist(), nlp)

    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(SAIDA, index=False, compression="gzip")
    print(f"\nSalvo em {SAIDA}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
