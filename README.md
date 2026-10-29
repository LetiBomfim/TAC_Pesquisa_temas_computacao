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
- [X] Modelagem de tópicos (BERTopic, com LDA como baseline)
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
source .venv/bin/activate         # Para Windows é: .venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download pt_core_news_sm
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


### 4. Gerar os embeddings

```bash
python src/embeddings.py
```

Transforma cada resumo num vetor de 384 números que representa seu sentido, com o modelo
multilíngue `paraphrase-multilingual-MiniLM-L12-v2`. É a etapa mais lenta e grava `data/processed/embeddings.npz`, que não é versionado. 
Em computadores com pouca memória, feche outros programas antes de rodar.


## Exploração

O notebook [`notebooks/01_exploracao.ipynb`](notebooks/01_exploracao.ipynb) traz o primeiro
olhar sobre a base: **23.749 trabalhos** entre 2010 e 2024.

![Teses e dissertações por ano](reports/figures/trabalhos_por_ano_grau.png)

- O mestrado acadêmico atingiu o pico em 2016 e caiu até 2023, voltando a subir em 2024.
- O doutorado cresce quase todo ano: sua participação no total dobrou, de 13% para 26%.
- O Sudeste concentra 43% dos trabalhos, enquanto Norte e Centro-Oeste, juntos, menos de 10%.


## Modelagem de tópicos

O notebook [`notebooks/02_modelagem_topicos.ipynb`](notebooks/02_modelagem_topicos.ipynb) descobre
os temas dos trabalhos sem rótulos prévios. O **BERTopic** agrupa os resumos pelo sentido e
encontrou **65 tópicos**, o **LDA**, método clássico baseado só na contagem de palavras, serve de
comparação com o mesmo número de tópicos.

![Os 8 maiores tópicos](reports/figures/topicos_principais.png)

| Modelo | Coerência (NPMI) | Diversidade |
|---|---|---|
| BERTopic | 0,171 | 0,825 |
| LDA | 0,059 | 0,817 |

A coerência mede se as palavras principais de um tópico aparecem juntas nos mesmos resumos. O
BERTopic gera temas muito mais nítidos e também um pouco mais
distintos entre si. O LDA tende a misturar assuntos dentro de um mesmo tópico.

Um achado: **não existe um tópico único de Inteligência Artificial**. Aprendizado de máquina
aparece como ferramenta espalhada por vários temas de aplicação. Medir a evolução da IA exige outra abordagem, 
que é o foco das próximas etapas.

**Limitações conhecidas:** o modelo pequeno do spaCy erra alguns lemas (por exemplo, "nuvem" vira
"nuver" em parte dos casos), e o nome da cidade de Pelotas aparece como "pelota" em alguns
tópicos. Os temas continuam reconhecíveis, mas um modelo de lematização maior melhoraria as
palavras-chave.


## Análise temporal

O notebook [`notebooks/03_analise_temporal.ipynb`](notebooks/03_analise_temporal.ipynb) responde
às perguntas centrais do projeto. Como a IA não forma um tópico próprio, cada trabalho é marcado
por um léxico de termos técnicos ([`src/lexico_ia.py`](src/lexico_ia.py)), dividido em três
famílias: aprendizado de máquina, aprendizado profundo e modelos de linguagem.

### Quando a IA virou tendência

![Trabalhos que citam IA por ano](reports/figures/ia_por_ano.png)

A fração de trabalhos que citam IA passou de **8% em 2010 para 42% em 2024**. O ponto de virada
é **2018**: antes, a fatia crescia 0,8 ponto percentual por ano; depois, **3,8 pontos por ano**,
quase cinco vezes mais rápido. O ano foi encontrado testando cada ano como início de uma nova
fase e escolhendo o que melhor separa a série em duas retas.

![Famílias de termos de IA](reports/figures/ia_familias.png)

O crescimento veio em três ondas: o aprendizado de máquina cresce o período todo; o aprendizado
profundo aparece por volta de 2017 e se estabiliza em cerca de 12% desde 2022; e os modelos de
linguagem surgem em 2020 e são os que mais crescem no fim da série (de 0,7% para 6,7% dos
trabalhos).

### Temas que ganharam e perderam espaço

![Variação dos tópicos](reports/figures/variacao_topicos.png)

Comparando 2010–2014 com 2020–2024, ganharam espaço aplicações em **saúde**, os **métodos de
aprendizado de máquina**, **agricultura**, **neurociência computacional**, **blockchain e
criptografia**, **educação** e **IoT**. Perderam espaço **engenharia e qualidade de software**,
**otimização combinatória e lógica**, **programação paralela e hardware**, **redes de sensores**,
**serviços web** e **TV digital**.

### Mestrado × doutorado e regiões

![IA por grau](reports/figures/ia_por_grau.png)

No período todo, o doutorado tem mais trabalhos de IA que o mestrado (23% contra 20%). Mas,
ano a ano, as curvas andam juntas: em 2020–2024, o mestrado tem até um pouco mais (37% contra
35%). A diferença no total vem da composição: o doutorado cresceu justamente nos anos em que a
IA se espalhou.

![IA por região](reports/figures/ia_por_regiao.png)

Entre 2010 e 2014, todas as regiões tinham de 8% a 12% de trabalhos de IA. Em 2020–2024, a
diferença aparece e é estatisticamente significativa (qui-quadrado, p < 0,001): **Centro-Oeste
(39%) e Sudeste (38%)** lideram, e o **Norte (31%)** fica atrás.

**Limitação:** o léxico identifica trabalhos que *citam* termos de IA no resumo. Um trabalho
pode usar IA sem citar nenhum desses termos, ou citá-los só como contexto. As próximas etapas
testam abordagens que olham o sentido do resumo, e não só as palavras.


## Contexto

Projeto ligado ao artigo escrito em coautoria com Júlia Paulo Amorim na disciplina de Técnicas de Apresentação
Científica (UnB). Esta é a minha implementação do pipeline e das extensões com LLM.

## Dados

[Catálogo de Teses e Dissertações – Dados Abertos CAPES](https://dadosabertos.capes.gov.br/group/catalogo-de-teses-e-dissertacoes-brasil).

## Autoria

- **Implementação:** Letícia Gonçalves Bomfim, Ciência da Computação, Universidade de Brasília
- **Artigo:** Letícia Gonçalves Bomfim e Júlia Paulo Amorim, Universidade de Brasília