"""Monta a base de teses e dissertações de Computação (2010–2024) a partir dos CSVs da CAPES.

Os arquivos de 1987–2012 e os de 2013 em diante têm nomes de colunas diferentes.
Este script lê só as colunas necessárias de cada ano, padroniza os nomes, filtra a
área de avaliação Ciência da Computação e grava uma base única.

Como usar: (a partir da raiz do repositório, depois de rodar download_capes.py):
    python src/build_dataset.py
"""

import sys
import unicodedata
from pathlib import Path

import pandas as pd

PASTA_RAW = Path("data/raw")
SAIDA = Path("data/processed/teses_computacao_2010_2024.csv.gz")

AREAS_ALVO = {"CIENCIA DA COMPUTACAO", "COMPUTACAO"}
TAMANHO_MINIMO_RESUMO = 100  # caracteres; abaixo disso costuma ser resumo vazio ou "-"

COLUNAS = {
    "ano": ["AN_BASE", "AnoBase"],
    "ies_sigla": ["SG_ENTIDADE_ENSINO", "SiglaIes"],
    "ies_nome": ["NM_ENTIDADE_ENSINO", "NomeIes"],
    "uf": ["SG_UF_IES", "Uf"],
    "regiao": ["NM_REGIAO", "Regiao"],
    "programa": ["NM_PROGRAMA", "NomePrograma"],
    "grau": ["NM_GRAU_ACADEMICO", "Nivel"],
    "titulo": ["NM_PRODUCAO", "TituloTese"],
    "resumo": ["DS_RESUMO", "ResumoTese"],
    "palavras_chave": ["DS_PALAVRA_CHAVE", "PalavrasChave"],
    "area_avaliacao": ["NM_AREA_AVALIACAO", "AreaAvaliacao"],
    "area_conhecimento": ["NM_AREA_CONHECIMENTO", "AreaConhecimento"],
}
OBRIGATORIAS = {"ano", "grau", "titulo", "resumo", "area_avaliacao"}

GRAUS = {
    "MESTRADO": "Mestrado",
    "DOUTORADO": "Doutorado",
    "MESTRADO PROFISSIONAL": "Mestrado Profissional",
    "PROFISSIONALIZANTE": "Mestrado Profissional",
    "DOUTORADO PROFISSIONAL": "Doutorado Profissional",
}

REGIOES = {
    "NORTE": "Norte",
    "NORDESTE": "Nordeste",
    "CENTRO-OESTE": "Centro-Oeste",
    "CENTRO OESTE": "Centro-Oeste",
    "SUDESTE": "Sudeste",
    "SUL": "Sul",
}


def normalizar(texto: str) -> str:
    """Maiúsculas, sem acentos e sem espaços nas pontas, para comparar categorias."""
    sem_acento = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    return " ".join(sem_acento.upper().split())


def detectar_encoding(caminho: Path) -> str:
    """Os arquivos da CAPES variam entre UTF-8 e Latin-1 conforme o ano."""
    with open(caminho, "rb") as arquivo:
        amostra = arquivo.read(1024 * 1024)
    try:
        amostra.decode("utf-8")
        return "utf-8"
    except UnicodeDecodeError:
        return "latin-1"


def mapear_colunas(cabecalho: list[str], caminho: Path) -> dict[str, str]:
    """Descobre, para cada coluna padronizada, qual é o nome dela neste arquivo."""
    cabecalho = [coluna.strip().lstrip("﻿") for coluna in cabecalho]
    mapa = {}
    for padrao, candidatas in COLUNAS.items():
        encontrada = next((c for c in candidatas if c in cabecalho), None)
        if encontrada:
            mapa[encontrada] = padrao

    faltando = OBRIGATORIAS - set(mapa.values())
    if faltando:
        raise ValueError(
            f"{caminho.name}: não encontrei as colunas {sorted(faltando)}.\n"
            f"Colunas do arquivo: {cabecalho}\n"
            "Adicione o nome certo na lista COLUNAS de build_dataset.py."
        )
    return mapa


def ler_ano(caminho: Path) -> pd.DataFrame:
    encoding = detectar_encoding(caminho)
    cabecalho = pd.read_csv(caminho, sep=";", encoding=encoding, nrows=0).columns.tolist()
    mapa = mapear_colunas(cabecalho, caminho)

    partes = []
    leitor = pd.read_csv(
        caminho,
        sep=";",
        encoding=encoding,
        usecols=lambda c: c.strip().lstrip("﻿") in mapa,
        dtype=str,
        chunksize=50_000,
        on_bad_lines="warn",
    )
    for bloco in leitor:
        bloco.columns = [mapa[c.strip().lstrip("﻿")] for c in bloco.columns]
        da_area = bloco["area_avaliacao"].fillna("").map(normalizar).isin(AREAS_ALVO)
        partes.append(bloco[da_area])

    return pd.concat(partes, ignore_index=True) if partes else pd.DataFrame()


def limpar(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for coluna in df.columns:
        df[coluna] = df[coluna].str.strip()

    df["ano"] = pd.to_numeric(df["ano"], errors="coerce").astype("Int64")
    df["grau"] = df["grau"].map(lambda g: GRAUS.get(normalizar(g), g))
    if "regiao" in df:
        df["regiao"] = df["regiao"].map(lambda r: REGIOES.get(normalizar(r), r))

    antes = len(df)
    df = df[df["resumo"].fillna("").str.len() >= TAMANHO_MINIMO_RESUMO]
    sem_resumo = antes - len(df)

    antes = len(df)
    chave = df["titulo"].map(normalizar) + "|" + df["resumo"].str[:200].map(normalizar)
    df = df[~chave.duplicated()]
    duplicados = antes - len(df)

    print(f"Removidos: {sem_resumo} sem resumo válido, {duplicados} duplicados")
    return df.drop(columns="area_avaliacao").sort_values("ano").reset_index(drop=True)


def main() -> int:
    arquivos = sorted(PASTA_RAW.glob("capes_*.csv"))
    if not arquivos:
        print(f"Nenhum CSV em {PASTA_RAW}. Rode antes: python src/download_capes.py")
        return 1

    anos = []
    for caminho in arquivos:
        df_ano = ler_ano(caminho)
        print(f"{caminho.name}: {len(df_ano)} trabalhos de Computação")
        if df_ano.empty:
            print(f"  ATENÇÃO: nenhum trabalho encontrado em {caminho.name}. "
                  "Confira se o nome da área de avaliação mudou (AREAS_ALVO).")
        anos.append(df_ano)

    base = limpar(pd.concat(anos, ignore_index=True))

    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    base.to_csv(SAIDA, index=False, compression="gzip")

    print(f"\nBase final: {len(base)} trabalhos -> {SAIDA}")
    print(base.groupby(["ano", "grau"]).size().unstack(fill_value=0).to_string())
    return 0


if __name__ == "__main__":
    sys.exit(main())