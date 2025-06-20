# src/app_web.py
from flask import Flask, render_template, request, redirect, url_for
from .db import Database
from .utils import setup_logging, logger # Importe o logger para usar aqui também
import os
from datetime import datetime # <-- MUDANÇA: Importar datetime

# Inicializa o logger para a aplicação web
setup_logging()

app = Flask(__name__)

# Instancia o banco de dados
db = Database()

@app.route('/')
def index():
    """Rota principal para exibir o formulário de filtro e os resultados."""
    # Parâmetros de filtro iniciais (vazios)
    city = request.args.get('city', '').strip()
    tipo_evento = request.args.get('tipo_evento', '').strip()
    genero_musical = request.args.get('genero_musical', '').strip()
    min_preco_str = request.args.get('min_preco', '').strip()
    max_preco_str = request.args.get('max_preco', '').strip()
    start_date_str = request.args.get('start_date', '').strip()
    end_date_str = request.args.get('end_date', '').strip()
    
    # Ordem e direção (parâmetros da URL ou padrões)
    order_by = request.args.get('order_by', 'data_evento_inicio').strip()
    order_direction = request.args.get('order_direction', 'ASC').strip().upper()

    # Conversão de tipos para os filtros
    min_preco = None
    if min_preco_str:
        try:
            min_preco = float(min_preco_str)
        except ValueError:
            logger.warning(f"Valor inválido para min_preco: {min_preco_str}")
            min_preco = None

    max_preco = None
    if max_preco_str:
        try:
            max_preco = float(max_preco_str)
        except ValueError:
            logger.warning(f"Valor inválido para max_preco: {max_preco_str}")
            max_preco = None
    
    start_date = None
    if start_date_str:
        try:
            datetime.strptime(start_date_str, '%Y-%m-%d')
            start_date = start_date_str
        except ValueError:
            logger.warning(f"Formato inválido para start_date: {start_date_str}")
            start_date = None
    
    end_date = None
    if end_date_str:
        try:
            datetime.strptime(end_date_str, '%Y-%m-%d')
            end_date = end_date_str
        except ValueError:
            logger.warning(f"Formato inválido para end_date: {end_date_str}")
            end_date = None

    # Chamar o método de filtragem do banco de dados
    events = db.filter_events(
        city=city if city else None,
        tipo_evento=tipo_evento if tipo_evento else None,
        genero_musical=genero_musical if genero_musical else None,
        min_preco=min_preco,
        max_preco=max_preco,
        start_date=start_date,
        end_date=end_date,
        order_by=order_by,
        order_direction=order_direction
    )

    # Passar os resultados e os valores dos filtros para o template HTML
    return render_template(
        'index.html', 
        events=events,
        current_filters={
            'city': city,
            'tipo_evento': tipo_evento,
            'genero_musical': genero_musical,
            'min_preco': min_preco_str,
            'max_preco': max_preco_str,
            'start_date': start_date_str,
            'end_date': end_date_str,
            'order_by': order_by,
            'order_direction': order_direction
        }, 
        now=datetime.now # Passa a função datetime.now para o template
    )

# Este bloco só é executado se você rodar app_web.py diretamente
# Para rodar com Docker, o comando CMD no Dockerfile ou docker-compose.yml será usado
if __name__ == '__main__':
    # Cria a tabela no DB ao iniciar a aplicação pela primeira vez
    db.create_table()
    app.run(debug=True, host='0.0.0.0') # host='0.0.0.0' para ser acessível de fora do container