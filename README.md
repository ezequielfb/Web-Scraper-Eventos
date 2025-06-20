# Web Scraper de Eventos Sympla  
Coleta, Armazenamento e Visualização de Eventos

## Visão Geral

Este projeto é um sistema completo para coleta, armazenamento, análise e visualização de dados de eventos da plataforma Sympla.

Foi desenvolvido em fases, cada uma abordando um segmento específico, culminando em uma aplicação robusta com interface web interativa.

Objetivo:  
Coletar shows e eventos do Sympla (ou qualquer site de estrutura similar), classificá-los, armazená-los em um banco de dados PostgreSQL em nuvem e exibi-los em uma interface web amigável.

## Funcionalidades

- Raspagem de Dados (Web Scraping):  
  Coleta de informações detalhadas de eventos do Sympla (nome, data, local, link de compra, organizador, preços e tipos de ingresso), utilizando engenharia reversa das APIs internas do Sympla.

- Armazenamento Persistente:  
  Dados armazenados em um banco PostgreSQL hospedado na nuvem (Railway).

- Classificação de Eventos:  
  Lógica de "IA leve" baseada em palavras-chave para categorizar eventos por tipo_evento e genero_musical.

- Containerização com Docker:  
  Aplicação empacotada em containers Docker para portabilidade e consistência.

- Interface Web Interativa:  
  Aplicação Flask com HTML e CSS, exibindo e filtrando eventos.  
  Interface acessível em http://localhost:5000.

## Tecnologias Utilizadas

- Python 3.10
- Flask + Jinja2
- HTML + CSS
- PostgreSQL
- Docker e Docker Compose

### Principais Bibliotecas

- requests
- beautifulsoup4
- psycopg2-binary
- python-dotenv

## Estrutura do Projeto

```
.
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env
└── src/
    ├── main.py
    ├── scraper_base.py
    ├── sympla_scraper.py
    ├── db.py
    ├── utils.py
    ├── app_web.py
    ├── static/
    │   └── style.css
    └── templates/
        ├── base.html
        └── index.html
```

## Como Configurar e Executar

### Pré-requisitos

- Docker instalado (incluindo Docker Compose, dispensavel se não quiser usa BD)
- Git para clonar o repositório

### Passos

1. Clone o repositório:

```
git clone https://github.com/ezequielfb/Web-Scraper-Eventos.git
cd Web-Scraper-Eventos
```

2. Crie um arquivo `.env` na raiz do projeto, contendo a URL do banco de dados:

```
DATABASE_URL=postgresql://usuario:senha@host:porta/dbname
```

(Exemplo obtido da Railway ou outro provedor de PostgreSQL)

3. Construa e inicie os containers:

```
docker-compose up --build -d
```

4. Acesse a interface web:  
   Abra seu navegador em [http://localhost:5000](http://localhost:5000)

5. (Opcional) Verificar logs:

```
docker-compose logs -f
```

Os logs também são salvos em `./logs`.

## Desafios e Lições Aprendidas

### Defesas Anti-Bot Avançadas

- O Sympla possui defesas que bloquearam scraping com BeautifulSoup e Selenium.
- Solução: engenharia reversa das APIs internas, com requests diretos.

### Escolha do Framework

- Decisão entre Streamlit e Flask.
- Escolhi o Flask pois quero melhorar meu aprendizado de HTML/CSS/JS tradicional (frontend em geral).

### Integração PostgreSQL + Docker

- Tive problemas de inicialização da classe Database e variáveis de ambiente, era um pequeno bug na hora do carregamento das variáveis via docker-compose

### Estilização dos Cards

- Uso de `overflow: visible` e `transform: scale()` para garantir estabilidade visual.

## Considerações Finais

Este projeto serviu como um laboratório prático para aplicar conceitos de scraping, backend, banco de dados e desenvolvimento web em um caso real com desafios técnicos consideráveis.

