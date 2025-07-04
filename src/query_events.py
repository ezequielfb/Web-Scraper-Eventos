# src/query_events.py
from .db import Database
from .utils import setup_logging
import os
from datetime import datetime

def run_interactive_query():
    setup_logging() # Configura o logger para este script também

    db = Database() # Instancia a conexão com o banco de dados

    print("\n--- Ferramenta de Consulta Interativa de Eventos ---")
    print("Deixe um campo em branco e pressione Enter para ignorar o filtro.")

    # Coletar parâmetros de filtro do usuário
    city = input("Cidade (ex: São Paulo): ").strip()
    tipo_evento = input("Tipo de Evento (ex: Música, Teatro): ").strip()
    genero_musical = input("Gênero Musical (ex: Rock, Samba/Pagode): ").strip()

    min_preco_str = input("Preço Mínimo (ex: 50.00): ").strip()
    max_preco_str = input("Preço Máximo (ex: 150.00): ").strip()
    
    # Adicionando filtro por data
    start_date_str = input("Data Inicial (YYYY-MM-DD, ex: 2025-07-01): ").strip()
    end_date_str = input("Data Final (YYYY-MM-DD, ex: 2025-07-31): ").strip()

    order_by = input("Ordenar por (nome_evento, data_evento_inicio, preco, etc. - padrão: data_evento_inicio): ").strip()
    order_direction = input("Direção da ordenação (ASC ou DESC - padrão: ASC): ").strip().upper()

    # Converter entradas para o formato correto
    min_preco = None
    if min_preco_str:
        try:
            min_preco = float(min_preco_str)
        except ValueError:
            print("Aviso: Preço Mínimo inválido. Ignorando este filtro.")

    max_preco = None
    if max_preco_str:
        try:
            max_preco = float(max_preco_str)
        except ValueError:
            print("Aviso: Preço Máximo inválido. Ignorando este filtro.")

    # Validar e formatar datas
    start_date = None
    if start_date_str:
        try:
            datetime.strptime(start_date_str, '%Y-%m-%d') # Apenas para validar o formato
            start_date = start_date_str
        except ValueError:
            print("Aviso: Data Inicial inválida. Use YYYY-MM-DD. Ignorando este filtro.")

    end_date = None
    if end_date_str:
        try:
            datetime.strptime(end_date_str, '%Y-%m-%d') # Apenas para validar o formato
            end_date = end_date_str
        except ValueError:
            print("Aviso: Data Final inválida. Use YYYY-MM-DD. Ignorando este filtro.")

    # Chamar a função de filtragem com os parâmetros coletados
    print("\nBuscando eventos com os filtros especificados...")
    filtered_events = db.filter_events(
        city=city if city else None,
        tipo_evento=tipo_evento if tipo_evento else None,
        genero_musical=genero_musical if genero_musical else None,
        min_preco=min_preco,
        max_preco=max_preco,
        start_date=start_date,
        end_date=end_date,
        order_by=order_by if order_by else 'data_evento_inicio',
        order_direction=order_direction if order_direction in ['ASC', 'DESC'] else 'ASC'
    )

    print("\n--- Resultados da Consulta ---")
    if filtered_events:
        print(f"Encontrados {len(filtered_events)} evento(s) correspondente(s):")
        for i, event in enumerate(filtered_events):
            print(f"\n{i+1}. Nome: {event['nome_evento']}")
            print(f"   Artista: {event['nome_artista']}")
            print(f"   Data: {event['data_evento_inicio']}")
            print(f"   Local: {event['local']}, {event['cidade']} - {event['estado']}")
            print(f"   Preço: {event['preco']}")
            print(f"   Organizador: {event['organizador']}")
            print(f"   Tipo: {event['tipo_evento']} ({event['genero_musical']})")
            print(f"   Link: {event['link_compra']}")
            # Opcional: imprimir detalhes dos tipos_ingresso se quiser
            # if event['tipos_ingresso']:
            #     print("   Tipos de Ingresso:")
            #     for tipo_ing in event['tipos_ingresso']:
            #         print(f"     - {tipo_ing.get('tipo', 'N/A')}: {tipo_ing.get('valor_principal', 'N/A')}{tipo_ing.get('taxa', '')} {tipo_ing.get('valor_parcelado', '')} (Vendas até: {tipo_ing.get('data_limite_venda', 'N/A')})")
    else:
        print("Nenhum evento encontrado com os filtros especificados.")

    print("\n--- Consulta Interativa Concluída ---")

if __name__ == "__main__":
    run_interactive_query()