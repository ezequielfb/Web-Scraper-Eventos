# Use uma imagem base Python oficial (escolha a versão mais próxima da sua local)
FROM python:3.10-slim-buster

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia o arquivo de dependências (requirements.txt) primeiro
COPY requirements.txt .

# Instala as dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código da aplicação para o diretório de trabalho
COPY . .

# Comando Padrão para executar a aplicação Flask
# Isso pode ser sobrescrito pelo 'command' no docker-compose.yml
CMD ["flask", "run", "--host", "0.0.0.0"]