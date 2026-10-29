import math
from itertools import combinations


def coerencia_npmi(topicos: list[list[str]], documentos: list[set[str]]) -> float:
    """NPMI médio dos pares de palavras de cada tópico, contando coocorrência por documento."""
    n_docs = len(documentos)
    vocabulario = {palavra for topico in topicos for palavra in topico}
    docs_com = {palavra: set() for palavra in vocabulario}
    for i, doc in enumerate(documentos):
        for palavra in vocabulario & doc:
            docs_com[palavra].add(i)

    notas_topicos = []
    for topico in topicos:
        notas = []
        for a, b in combinations(topico, 2):
            p_a = len(docs_com[a]) / n_docs
            p_b = len(docs_com[b]) / n_docs
            p_ab = len(docs_com[a] & docs_com[b]) / n_docs
            if p_ab == 0:
                notas.append(-1.0)
            elif p_ab == 1:
                notas.append(1.0)
            else:
                pmi = math.log(p_ab / (p_a * p_b))
                notas.append(pmi / -math.log(p_ab))
        notas_topicos.append(sum(notas) / len(notas))
    return sum(notas_topicos) / len(notas_topicos)


def diversidade(topicos: list[list[str]]) -> float:
    todas = [palavra for topico in topicos for palavra in topico]
    return len(set(todas)) / len(todas)
