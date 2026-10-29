"""Identifica trabalhos de Inteligência Artificial pelos termos que aparecem no resumo.

Aprendizado de máquina apareceespalhado por vários temas de aplicação, por isso a IA é marcada à parte, 
agrupados em três famílias que correspondem a fases da área:

- aprendizado de máquina: os termos gerais e os métodos clássicos;
- aprendizado profundo: redes convolucionais, recorrentes etc.;
- modelos de linguagem: transformers e LLMs, a fase mais recente.

Um trabalho é marcado como de IA quando o resumo cita pelo menos um termo de qualquer família.
A comparação é feita sem acentos e em minúsculas, então "Aprendizado de Máquina" e
"aprendizado de maquina" contam igual.
"""

import re
import unicodedata

FAMILIAS = {
    "aprendizado_maquina": [
        r"inteligencia artificial",
        r"aprendizado de maquina",
        r"aprendizagem de maquina",
        r"machine learning",
        r"redes? neura(?:l|is)",
        r"neural networks?",
        r"aprendizado (?:nao )?supervisionado",
        r"aprendizado por reforco",
        r"reinforcement learning",
        r"random forest",
        r"florestas? aleatorias?",
        r"\bsvms?\b",
        r"maquinas? de vetores? de suporte",
        r"gradient boosting",
        r"\bxgboost\b",
        r"classificadores?\b",
    ],
    "aprendizado_profundo": [
        r"deep learning",
        r"aprendizado profundo",
        r"aprendizagem profunda",
        r"redes? (?:neurais )?convolucion",
        r"\bcnns?\b",
        r"\blstms?\b",
        r"redes? (?:neurais )?recorrentes?",
    ],
    "modelos_linguagem": [
        r"transformers?\b",
        r"\bbert\b",
        r"\bllms?\b",
        r"grandes? modelos? de linguagem",
        r"large language models?",
        r"\bgpt",
        r"ia generativa",
        r"inteligencia artificial generativa",
    ],
}

PADROES = {familia: re.compile("|".join(termos)) for familia, termos in FAMILIAS.items()}


def normalizar(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return sem_acento.lower()


def familias_citadas(texto: str) -> dict[str, bool]:
    """Para cada família, diz se o texto cita algum termo dela."""
    texto = normalizar(texto)
    return {familia: bool(padrao.search(texto)) for familia, padrao in PADROES.items()}


def eh_ia(texto: str) -> bool:
    return any(familias_citadas(texto).values())
