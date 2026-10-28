# Evolução temática das teses e dissertações de Computação no Brasil (2010–2024)

Como mudaram os temas da pós-graduação brasileira em Computação nos últimos 15 anos? Este projeto
analisa os resumos de teses e dissertações do **Catálogo de Teses e Dissertações da CAPES**, que são dados
abertos, para responder:

- Quais temas ganharam e quais perderam espaço entre 2010 e 2024?
- Quando a Inteligência Artificial e o Machine Learning viraram tendência dominante?
- Há diferença entre mestrado e doutorado?
- E entre as regiões do país?

## Backlog/Roadmap

- [ ] Coleta dos dados abertos da CAPES
- [ ] Limpeza e consolidação da base de Computação (2010–2024)
- [ ] Pré-processamento dos resumos (NLP)
- [ ] Modelagem de tópicos (BERTopic, com LDA como baseline)
- [ ] Análise temporal e estatística
- [ ] Classificação supervisionada de trabalhos de IA
- [ ] Classificação de temas com LLM
- [ ] App de perguntas sobre os dados

## Estrutura

```
data/
  raw/          arquivos originais da CAPES (não versionados)
  processed/    bases tratadas
notebooks/      análises, em ordem de execução
src/            scripts de coleta e tratamento
reports/
  figures/      gráficos gerados
```

## Como rodar

Requer Python 3.10 ou superior.

```bash
python -m venv .venv
source .venv/bin/activate        # Para Windows é: .venv\Scripts\activate
pip install -r requirements.txt
```

## Contexto

Projeto ligado ao artigo escrito em coautoria com Júlia Paulo Amorim na disciplina de Técnicas de Apresentação
Científica (UnB). Esta é a minha implementação do pipeline e das extensões com LLM.

## Dados

[Catálogo de Teses e Dissertações – Dados Abertos CAPES](https://dadosabertos.capes.gov.br/group/catalogo-de-teses-e-dissertacoes-brasil).

## Autoras

Letícia Gonçalves Bomfim — Ciência da Computação, Universidade de Brasília
Júlia Paulo Amorim - Ciência da Computação, Universidade de Brasília