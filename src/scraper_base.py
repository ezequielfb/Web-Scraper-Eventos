# src/scraper_base.py
import requests
import time
from .utils import logger # Importa o logger

class BaseScraper:
    def __init__(self, base_url, source_name, output_dir, output_filename):
        self.base_url = base_url
        self.source_name = source_name
        self.output_dir = output_dir
        self.output_filename = output_filename
        self.logger = logger
        # self.driver = None # Não é necessário para a estratégia atual do Sympla (API-based)

    def _fetch_page(self, url):
        """
        Faz a requisição HTTP para a URL usando requests.
        :param url: URL a ser buscada.
        :return: Conteúdo HTML da página como string (bytes), ou None em caso de erro.
        """
        self.logger.info(f"Buscando URL: {url} (Usando Requests)")
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0' # User-Agent atualizado
            }
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status() # Lança exceção para códigos de status HTTP 4xx/5xx
            self.logger.info(f"Status da requisição: {response.status_code}")
            self.logger.info(f"Tamanho do conteúdo HTML recebido: {len(response.content)} caracteres")
            return response.content
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erro na requisição (requests): {e}")
            return None
        except Exception as e:
            self.logger.error(f"Erro inesperado ao buscar página (requests): {e}")
            return None

    def scrape_events(self, city=None, filters=None, max_pages=3):
        raise NotImplementedError("O método 'scrape_events' deve ser implementado pela subclasse.")