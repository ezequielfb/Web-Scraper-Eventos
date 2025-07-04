# src/main.py
from .db import Database
from .sympla_scraper import SymplaScraper
from .utils import setup_logging
import os
import json

def main():
    setup_logging()
    
    # Inicializa o banco de dados
    db = Database()
    db.create_table() # Garante que a tabela 'eventos' exista no PostgreSQL

    # Inicializa o scraper do Sympla
    sympla_scraper = SymplaScraper()
    
    # Executa a raspagem dos eventos do Sympla
    # max_pages=1 para teste rápido
    # Você pode aumentar este valor para raspar mais páginas
    sympla_events = sympla_scraper.scrape_events(city="São Paulo", max_pages=1) 
    
    if sympla_events:
        for event in sympla_events:
            # Para cada evento da lista, busca detalhes adicionais usando as APIs
            event_details = sympla_scraper.fetch_event_details(event['link_compra'])
            if event_details:
                event.update(event_details) # Atualiza o dicionário do evento com os detalhes
            
            # Insere/Atualiza evento no banco de dados PostgreSQL
            db.insert_event(event) 
            
        # Opcional: Exportar todos os eventos do banco de dados para um arquivo JSON local
        # Esta parte é mais para visualização e depuração local, e não para execução normal.
        # all_db_events = db.get_all_events()
        # output_file_path = os.path.join(sympla_scraper.output_dir, sympla_scraper.output_filename)
        # with open(output_file_path, 'w', encoding='utf-8') as f:
        #     json.dump(all_db_events, f, ensure_ascii=False, indent=4)
        # print(f"Dados do Sympla exportados para {output_file_path}")
    else:
        print("Nenhum evento encontrado no Sympla para exportar.")

    print("\n--- Processo de Raspagem e Armazenamento Concluído ---")


if __name__ == "__main__":
    main()