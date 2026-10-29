import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

ENTRADA = Path("data/processed/resumos_preprocessados.csv.gz")
SAIDA = Path("data/processed/embeddings.npz")

MODELO = "paraphrase-multilingual-MiniLM-L12-v2"


def main() -> int:
    if not ENTRADA.exists():
        print(f"Arquivo não encontrado: {ENTRADA}. Rode antes: python src/preprocess.py")
        return 1

    df = pd.read_csv(ENTRADA, usecols=["texto_limpo", "apto_texto"])
    aptos = df[df["apto_texto"]]
    print(f"Gerando embeddings de {len(aptos)} resumos com {MODELO}...")

    modelo = SentenceTransformer(MODELO)
    vetores = modelo.encode(
        aptos["texto_limpo"].tolist(),
        batch_size=16,
        show_progress_bar=True,
        normalize_embeddings=True,
    )

    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    # ids = posição de cada resumo na base, para ligar o vetor de volta ao trabalho
    np.savez_compressed(SAIDA, ids=aptos.index.to_numpy(), vetores=vetores.astype(np.float32))
    print(f"Salvo em {SAIDA} ({vetores.shape[0]} vetores de {vetores.shape[1]} dimensões)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
