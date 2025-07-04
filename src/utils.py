# src/utils.py
import logging
import os
from datetime import datetime

# Configura o logger global
logger = logging.getLogger('event_scraper')
logger.setLevel(logging.INFO)

def setup_logging():
    """Configura o sistema de logging para salvar logs em um arquivo e exibir no console."""
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    log_filename = os.path.join(log_dir, 'scraper.log')

    # Remove handlers antigos para evitar duplicação de logs
    if logger.handlers:
        for handler in list(logger.handlers):
            logger.removeHandler(handler)

    # Handler para console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # Handler para arquivo
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    logger.info("Sistema de Busca de Shows inicializado.")