"""
Baixa os arquivos anuais do Catálogo de Teses e Dissertações da CAPES.
Fonte: https://dadosabertos.capes.gov.br/group/catalogo-de-teses-e-dissertacoes-brasil
"""

import argparse
import sys
from pathlib import Path

import requests
from tqdm import tqdm

PASTA_RAW = Path("data/raw")

BASE = "https://dadosabertos.capes.gov.br/dataset"

# Um CSV por ano-base. Os links mudam quando a CAPES republica um ano,
# então vale conferir no portal se algum download falhar com 404.
URLS = {
    2010: f"{BASE}/b59bd607-7422-4b37-bedc-0e6c1b96bee2/resource/859ea6a8-2967-4856-bd18-fdeaa7220ccb/download/dados_2010.csv",
    2011: f"{BASE}/b59bd607-7422-4b37-bedc-0e6c1b96bee2/resource/e37189cd-204c-43ad-8d8d-9ba3821336b0/download/dados_2011.csv",
    2012: f"{BASE}/b59bd607-7422-4b37-bedc-0e6c1b96bee2/resource/14fe8b64-b861-42dc-92a2-be603e925e21/download/dados_2012.csv",
    2013: f"{BASE}/4b0780eb-5ba4-48d4-8d6a-0b77c56f2fd7/resource/49155638-ffc6-4782-a3ca-489bb4345324/download/br-capes-btd-2013a2016-2017-12-01_2013.csv",
    2014: f"{BASE}/4b0780eb-5ba4-48d4-8d6a-0b77c56f2fd7/resource/bf1a79a5-ac49-44e8-b4a5-eca30fb48174/download/br-capes-btd-2013a2016-2017-12-01_2014.csv",
    2015: f"{BASE}/4b0780eb-5ba4-48d4-8d6a-0b77c56f2fd7/resource/e4e2325f-6638-42b3-b801-03c418970a9e/download/br-capes-btd-2013a2016-2017-12-01_2015.csv",
    2016: f"{BASE}/4b0780eb-5ba4-48d4-8d6a-0b77c56f2fd7/resource/7403d9ac-0e71-4539-bc44-8d7aa7b8f452/download/br-capes-btd-2013a2016-2017-12-01_2016.csv",
    2017: f"{BASE}/36d1c92c-f9e0-4da1-a4f0-633e6ebefe03/resource/902bd63b-137f-4090-89e9-cab94f12c41d/download/br-capes-btd-2017-2024-08-19.csv",
    2018: f"{BASE}/36d1c92c-f9e0-4da1-a4f0-633e6ebefe03/resource/638668a6-07da-4c7e-8aab-9044ae3cc753/download/br-capes-btd-2018-2024-08-19.csv",
    2019: f"{BASE}/36d1c92c-f9e0-4da1-a4f0-633e6ebefe03/resource/8f4f2bce-2744-460a-8f14-f1648c7a16df/download/br-capes-btd-2019-2025-04-29.csv",
    2020: f"{BASE}/36d1c92c-f9e0-4da1-a4f0-633e6ebefe03/resource/e37df31a-f250-4405-8b21-ca7e5c7c1696/download/br-capes-btd-2020-2024-08-19.csv",
    2021: f"{BASE}/dbb9b83e-7779-4b99-89d2-1ff8099f36f6/resource/068003e4-196c-41f4-8c35-1f7c94b4e55c/download/br-capes-btd-2021-2025-03-31.csv",
    2022: f"{BASE}/dbb9b83e-7779-4b99-89d2-1ff8099f36f6/resource/78f73608-6f5e-463c-ba79-0bff4f8a578d/download/br-capes-btd-2022-2025-03-31.csv",
    2023: f"{BASE}/dbb9b83e-7779-4b99-89d2-1ff8099f36f6/resource/b69baf26-8d02-4c10-ba39-7e9ab799e6ed/download/br-capes-btd-2023-2025-03-31.csv",
    2024: f"{BASE}/dbb9b83e-7779-4b99-89d2-1ff8099f36f6/resource/87133ba7-ac99-4d87-966e-8f580bc96231/download/br-capes-btd-2024-2025-12-01.csv",
}


def baixar(url: str, destino: Path) -> None:
    """ Baixa em blocos para não carregar o arquivo inteiro na memória. """
    temporario = destino.with_suffix(".part")
    with requests.get(url, stream=True, timeout=60) as resposta:
        resposta.raise_for_status()
        tamanho = int(resposta.headers.get("content-length", 0))
        with open(temporario, "wb") as arquivo, tqdm(
            total=tamanho, unit="B", unit_scale=True, desc=destino.name
        ) as barra:
            for bloco in resposta.iter_content(chunk_size=1024 * 1024):
                arquivo.write(bloco)
                barra.update(len(bloco))
    temporario.replace(destino)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--anos", nargs="+", type=int, default=sorted(URLS))
    parser.add_argument("--forcar", action="store_true", help="baixa de novo arquivos já existentes")
    args = parser.parse_args()

    desconhecidos = [ano for ano in args.anos if ano not in URLS]
    if desconhecidos:
        print(f"Sem URL cadastrada para: {desconhecidos}")
        return 1

    PASTA_RAW.mkdir(parents=True, exist_ok=True)
    falhas = []

    for ano in args.anos:
        destino = PASTA_RAW / f"capes_{ano}.csv"
        if destino.exists() and not args.forcar:
            print(f"{destino.name} já existe, pulando")
            continue
        try:
            baixar(URLS[ano], destino)
        except requests.RequestException as erro:
            print(f"Falha em {ano}: {erro}")
            falhas.append(ano)

    if falhas:
        print(f"Anos com falha: {falhas}. Rode de novo só com eles: --anos {' '.join(map(str, falhas))}")
        return 1
    print("Download concluído.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
