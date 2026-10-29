# Evolução temática das teses e dissertações de Computação no Brasil (2010–2024)

Como mudaram os temas da pós-graduação brasileira em Computação nos últimos 15 anos? Este projeto
analisa os resumos de teses e dissertações do **Catálogo de Teses e Dissertações da CAPES**, que são dados
abertos, para responder:

- Quais temas ganharam e quais perderam espaço entre 2010 e 2024?
- Quando a Inteligência Artificial e o Machine Learning viraram tendência dominante?
- Há diferença entre mestrado e doutorado?
- E entre as regiões do país?

## Backlog/Roadmap

- [X] Coleta dos dados abertos da CAPES
- [X] Limpeza e consolidação da base de Computação (2010–2024)
- [X] Pré-processamento dos resumos (NLP)
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

### 1. Baixar os dados

```bash
python src/download_capes.py
```

O script baixa os arquivos do Catálogo de Teses e Dissertações direto do portal de dados
abertos da CAPES, um CSV por ano, de 2010 a 2024, e salva em `data/raw/` com o nome padrão `capes_<ano>.csv`.
O download completo pode demorar. Para testar com menos dados, escolha os anos:

```bash
python src/download_capes.py --anos 2023          # só 2023
python src/download_capes.py --anos 2022 2023     # 2022 e 2023
```

Arquivos que já foram baixados são pulados, então dá para interromper e rodar de novo depois.
Para baixar de novo mesmo assim, é necessário usar `--forcar`.

### 2. Montar a base de Computação

```bash
python src/build_dataset.py
```

O script lê os CSVs de cada ano em `data/raw/`, padroniza os nomes das colunas, mantém só os trabalhos da área de avaliação
**Ciência da Computação**, remove trabalhos sem resumo e duplicados, e grava o resultado em
`data/processed/teses_computacao_2010_2024.csv.gz`.

No final, mostra quantos trabalhos ficaram por ano e por grau.

>**Observação:** a partir de 2024, a CAPES passou a chamar a área de avaliação de
>"Computação" (antes era "Ciência da Computação"). O script considera os dois nomes.

### 3. Pré-processar os resumos

```bash
python src/preprocess.py
```

Marca os resumos que ficam fora da análise de texto e gera duas versões de cada resumo: `texto_limpo`, em minúsculas, para o
BERTopic e o LLM, e `texto_lematizado`, só com substantivos, adjetivos e verbos na forma base e
sem palavras genéricas de texto acadêmico, para o LDA.

## Exploração

O notebook [`notebooks/01_exploracao.ipynb`](notebooks/01_exploracao.ipynb) traz o primeiro
olhar sobre a base: **23.749 trabalhos** entre 2010 e 2024.

![Teses e dissertações por ano](reports/figures/trabalhos_por_ano_grau.png)

- O mestrado acadêmico atingiu o pico em 2016 e caiu até 2023, voltando a subir em 2024.
- O doutorado cresce quase todo ano: sua participação no total dobrou, de 13% para 26%.
- O Sudeste concentra 43% dos trabalhos, enquanto Norte e Centro-Oeste, juntos, menos de 10%.


## Contexto

Projeto ligado ao artigo escrito em coautoria com Júlia Paulo Amorim na disciplina de Técnicas de Apresentação
Científica (UnB). Esta é a minha implementação do pipeline e das extensões com LLM.

## Dados

[Catálogo de Teses e Dissertações – Dados Abertos CAPES](https://dadosabertos.capes.gov.br/group/catalogo-de-teses-e-dissertacoes-brasil).

## Autoria

- **Implementação:** Letícia Gonçalves Bomfim, Ciência da Computação, Universidade de Brasília
- **Artigo:** Letícia Gonçalves Bomfim e Júlia Paulo Amorim, Universidade de Brasília