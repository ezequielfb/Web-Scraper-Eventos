# src/sympla_scraper.py
import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import time
from urllib.parse import urlparse, urljoin
import re
import string # Importar para pré-processamento de texto

from .scraper_base import BaseScraper

class SymplaScraper(BaseScraper):
    def __init__(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        output_data_dir = os.path.join(current_dir, '..', 'data')
        output_file_name = "sympla_events.json"

        super().__init__(
            base_url="https://www.sympla.com.br/eventos",
            source_name="Sympla",
            output_dir=output_data_dir,
            output_filename=output_file_name
        )
        os.makedirs(self.output_dir, exist_ok=True)
        self.logger.info("SymplaScraper inicializado.")

        # Dicionários para classificação de eventos (IA leve baseada em palavras-chave)
        # Ordem importa: coloque categorias/gêneros mais específicos antes dos mais gerais,
        # ou aqueles com palavras-chave que podem ser subconjunto de outros.
        self.event_types = {
            'Música': ['show', 'festival', 'banda', 'cantor', 'grito', 'carnaval', 'axe', 'concerto', 'orquestra', 'tributo', 'turnê', 'rock', 'pop', 'sertanejo', 'samba', 'pagode', 'eletrônica', 'dj', 'mpb', 'funk', 'gospel', 'clássica', 'hip hop', 'rap', 'trap', 'reggae', 'forró', 'jazz', 'blues', 'acústico', 'balada', 'micareta'],
            'Teatro': ['teatro', 'peça', 'stand-up', 'comédia', 'drama', 'monólogo', 'musical', 'palco', 'humor', 'performance'],
            'Esporte': ['esporte', 'corrida', 'maratona', 'futebol', 'jogo', 'campeonato', 'treino', 'crossfit', 'ciclismo', 'fitness', 'natação', 'vôlei', 'basquete', 'luta', 'jiu-jitsu', 'mma', 'patinação', 'skate', 'surf', 'triathlon'],
            'Feira/Exposição': ['feira', 'exposição', 'expo', 'mostra', 'artesanato', 'negócios', 'mercado', 'design', 'arte', 'fotografia', 'quadrinhos', 'games', 'geek', 'literária', 'livros', 'automóveis', 'imóveis'],
            'Palestras/Cursos': ['palestra', 'curso', 'workshop', 'webinar', 'conferência', 'treinamento', 'seminário', 'aulão', 'congresso', 'fórum', 'encontro', 'apresentação', 'imersão', 'mentoria'],
            'Infantil': ['infantil', 'criança', 'kids', 'infância', 'contar histórias', 'brincadeiras', 'personagens', 'bonecos', 'mágica', 'família'],
            'Gastronomia': ['gastronomia', 'comida', 'chef', 'degustação', 'festival de comida', 'restaurante', 'vinho', 'cerveja', 'churrasco', 'harmonização', 'bar', 'cozinha'],
            'Dança': ['dança', 'ballet', 'zumba', 'street dance', 'coreografia', 'break', 'dançar', 'espetáculo de dança'],
            'Cinema': ['cinema', 'filme', 'mostra de cinema', 'curta', 'documentário', 'sessão'],
            'Religioso/Espiritual': ['igreja', 'culto', 'louvor', 'palavra', 'retiro', 'evangélico', 'católico', 'espiritual', 'meditação', 'yoga'],
            'Festas/Baladas': ['festa', 'balada', 'danceteria', 'noite', 'reveillon', 'carnaval'], # Pode sobrepor com Música, mas é mais um "tipo"
            'Outros': [] # Catch-all, mantenha no final
        }

        self.music_genres = {
            'Rock': ['rock', 'metal', 'hardcore', 'punk', 'alternativo', 'indie rock', 'heavy metal', 'thrash metal', 'grunge', 'pop rock', 'progressivo'],
            'Pop': ['pop', 'r&b', 'k-pop', 'idols', 'divas', 'indie pop', 'hiphop', 'soul', 'funk internacional', 'electropop'],
            'Sertanejo': ['sertanejo', 'modão', 'country', 'rodeio', 'universitário', 'agro', 'dupla sertaneja', 'piseiro'],
            'Samba/Pagode': ['samba', 'pagode', 'partido alto', 'roda de samba', 'chorinho', 'bossa nova', 'samba-rock'],
            'Eletrônica': ['eletrônica', 'techno', 'house', 'rave', 'dj', 'edm', 'trance', 'trap', 'dubstep', 'psytrance'],
            'MPB': ['mpb', 'bossa nova', 'jazz', 'blues', 'acústico', 'instrumental'],
            'Funk': ['funk', 'funk carioca', 'passinho', 'brega funk', 'favela'],
            'Gospel': ['gospel', 'cristã', 'adoração', 'louvor', 'religioso'],
            'Clássica': ['clássica', 'orquestra', 'ópera', 'erudita', 'coral', 'concerto'],
            'Reggae': ['reggae', 'roots', 'dub', 'rastafari', 'bob marley'],
            'Forró': ['forró', 'pé de serra', 'universitário', 'xote', 'baião', 'arrastapé', 'são joão'],
            'Hip Hop/Rap': ['hip hop', 'rap', 'trap', 'rima', 'mcs', 'batalha de rima'],
            'Outro Musical': [] # Para outros tipos de música não específicos
        }
            
    def _classify_event(self, event_name, artist_name, organizer_name):
        """
        Classifica o evento com base em palavras-chave no nome, artista e organizador.
        Inclui pré-processamento de texto simples.
        """
        # Pré-processamento do texto
        def preprocess_text(text):
            if not text:
                return ""
            text = text.lower() # Converter para minúsculas
            text = text.translate(str.maketrans('', '', string.punctuation)) # Remover pontuação
            text = re.sub(r'\s+', ' ', text).strip() # Remover múltiplos espaços e espaços nas bordas
            return text

        processed_event_name = preprocess_text(event_name)
        processed_artist_name = preprocess_text(artist_name)
        processed_organizer_name = preprocess_text(organizer_name)

        text_to_classify = processed_event_name + " " + processed_artist_name + " " + processed_organizer_name
        
        tipo_evento = 'Outros'
        genero_musical = 'N/A' # N/A se não for música ou não houver gênero

        # Classificar Tipo de Evento (ordem importa: categorias mais específicas primeiro)
        for category, keywords in self.event_types.items():
            for keyword in keywords:
                if keyword in text_to_classify:
                    tipo_evento = category
                    break
            if tipo_evento != 'Outros':
                break

        # Se o tipo de evento for Música, tentar classificar o Gênero Musical
        if tipo_evento == 'Música':
            genero_musical = 'Outro Musical' # Padrão para música não específica
            for genre, keywords in self.music_genres.items():
                for keyword in keywords:
                    if keyword in text_to_classify:
                        genero_musical = genre
                        break
                if genero_musical != 'Outro Musical':
                    break
        
        return tipo_evento, genero_musical

    def parse_sympla_events_page(self, html_content):
        if not html_content:
            self.logger.warning("Conteúdo HTML vazio para parse_sympla_events_page, retornando lista vazia.")
            return []

        soup = BeautifulSoup(html_content, 'html.parser')
        events = []

        self.logger.info("Extraindo eventos da página de lista.")

        event_cards = soup.find_all('a', class_=['sympla-card', '_5ar7pz0', '_5ar7pz4'])

        if not event_cards:
            self.logger.warning("Nenhum card de evento encontrado na página de lista. Verifique os seletores da lista.")
            return []

        self.logger.info(f"Encontrados {len(event_cards)} cards de evento.")

        for card in event_cards:
            try:
                link = card.get('href', 'N/A')
                if link != 'N/A' and not link.startswith('http'):
                    link = urljoin(self.base_url, link)

                info_block = card.find('div', class_='_5ar7pz1')
                if not info_block:
                    self.logger.warning(f"Não foi possível encontrar o bloco de informações para o card: {link}. Pulando.")
                    continue

                title_tag = info_block.find('h3', class_='_5ar7pz6')
                title = title_tag.text.strip() if title_tag else 'N/A'

                location_tag = info_block.find('p', class_='_5ar7pz8')
                location_full_str = location_tag.text.strip() if location_tag else 'N/A'

                date_time_tag = info_block.find('div', class_=['qtfy415', 'qtfy413', 'qtfy416'])
                date_time_str = date_time_tag.text.strip() if date_time_tag else 'N/A'

                city = 'N/A'
                state = 'N/A'
                venue = location_full_str

                if location_full_str != 'N/A' and ' - ' in location_full_str:
                    parts = location_full_str.split(' - ')
                    if len(parts) >= 2:
                        venue = parts[0].strip()
                        city_state_part = parts[1].strip()
                        if ',' in city_state_part:
                            city_state_split = city_state_part.split(',')
                            if len(city_state_split) == 2:
                                city = city_state_split[0].strip()
                                state = city_state_split[1].strip()
                            elif len(city_state_split) == 1:
                                city = city_state_split[0].strip()
                        else:
                            city = city_state_part
                
                # Classificar o evento aqui.
                # A classificação inicial é baseada apenas no nome e artista,
                # pois o organizador só é conhecido após fetch_event_details.
                tipo_evento, genero_musical = self._classify_event(title, title, None) 
                
                event_info = {
                    'nome_evento': title,
                    'nome_artista': title,
                    'data_evento_inicio': date_time_str,
                    'data_evento_fim': 'N/A',
                    'local': venue,
                    'cidade': city,
                    'estado': state,
                    'link_compra': link,
                    'fonte_site': self.source_name,
                    'data_coleta': datetime.now().isoformat(),
                    'organizador': 'N/A', # Será preenchido pelo fetch_event_details
                    'preco': 'N/A',       # Será preenchido pelo fetch_event_details
                    'tipo_evento': tipo_evento,       # NOVA CHAVE (classificação inicial)
                    'genero_musical': genero_musical  # NOVA CHAVE (classificação inicial)
                }
                events.append(event_info)
            except Exception as e:
                self.logger.error(f"Erro ao analisar card de evento na lista: {e}. HTML do card: {card}. Pulando.")
                continue
        return events


    def fetch_event_details(self, event_url):
        details = {
            'descricao': 'N/A', # Mantido N/A
            'organizador': 'N/A',
            'preco': 'N/A',
            'tipos_ingresso': []
        }
        self.logger.info(f"Buscando detalhes do evento em: {event_url}")

        parsed_url = urlparse(event_url)
        event_id = parsed_url.path.split('/')[-1] # Extrai o ID do evento da URL
        if not event_id.isdigit(): # Garante que é um ID válido
            self.logger.warning(f"Não foi possível extrair ID do evento da URL: {event_url}")
            return details

        # URLs do bileto.sympla.com.br não têm essas APIs (geralmente)
        if 'bileto.sympla.com.br' in parsed_url.netloc:
            self.logger.warning("URL é do domínio bileto.sympla.com.br. Raspagem de detalhes limitada.")
            return details
        
        # --- ETAPA 1: API do Organizador ---
        organizer_api_url = f"https://event-page.svc.sympla.com.br/api/event-bff/purchase/event/{event_id}/organizer"
        
        # Headers mais importantes para a API do Organizador
        organizer_api_headers = {
            'accept': '*/*',
            'accept-encoding': 'gzip, deflate, br, zstd',
            'accept-language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'origin': 'https://www.sympla.com.br',
            'referer': 'https://www.sympla.com.br/',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0', # User-Agent do Edge
        }

        try:
            organizer_api_response = requests.get(organizer_api_url, headers=organizer_api_headers, timeout=10)
            organizer_api_response.raise_for_status() # Levanta exceção para erros HTTP
            organizer_data = organizer_api_response.json()
            
            if organizer_data:
                # Prioriza fantasyName, senão usa name
                details['organizador'] = organizer_data.get('fantasyName') or organizer_data.get('name', 'N/A')
                self.logger.info(f"Organizador obtido via API: {details['organizador']}")
            else:
                self.logger.warning(f"Nenhum dado de organizador retornado pela API para evento ID: {event_id}")

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erro ao buscar dados do organizador da API para {event_id}: {e}")
        except json.JSONDecodeError as e:
            self.logger.error(f"Erro ao decodificar JSON da API do organizador para {event_id}: {e}")
        except Exception as e:
            self.logger.error(f"Erro inesperado na análise da API do organizador para {event_id}: {e}")
        
        # --- ETAPA 2: API de Ingressos ---
        tickets_api_url = f"https://event-page.svc.sympla.com.br/api/event-bff/purchase/event/{event_id}/tickets"
        
        # Headers mais importantes para a API de Ingressos (similares aos de organizador)
        tickets_api_headers = {
            'accept': '*/*',
            'accept-encoding': 'gzip, deflate, br, zstd',
            'accept-language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'origin': 'https://www.sympla.com.br',
            'referer': 'https://www.sympla.com.br/',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0', # User-Agent do Edge
        }

        try:
            tickets_api_response = requests.get(tickets_api_url, headers=tickets_api_headers, timeout=10)
            tickets_api_response.raise_for_status() 
            tickets_data = tickets_api_response.json()
            self.logger.info(f"Dados de ingressos obtidos via API para evento ID: {event_id}")

            if tickets_data:
                extracted_prices_info = []
                numeric_prices = []

                for ticket_item in tickets_data:
                    ticket_info = {}
                    
                    ticket_info['tipo'] = ticket_item.get('name', 'N/A')
                    
                    sale_price_monetary = ticket_item.get('salePriceMonetary', {})
                    main_price_decimal = sale_price_monetary.get('decimal')
                    ticket_info['valor_principal'] = f"R$ {main_price_decimal:.2f}".replace('.', ',') if isinstance(main_price_decimal, (int, float)) else 'N/A'

                    fee_monetary = ticket_item.get('feeMonetary', {})
                    fee_decimal = fee_monetary.get('decimal')
                    ticket_info['taxa'] = f" (+ R$ {fee_decimal:.2f} taxa)".replace('.', ',') if isinstance(fee_decimal, (int, float)) else 'N/A'
                    
                    installments = ticket_item.get('installments', [])
                    if installments:
                        # Tenta pegar a opção com mais parcelas para o valor parcelado
                        max_installments_option = max(installments, key=lambda x: x.get('installments', 0), default={})
                        parcel_price_decimal = max_installments_option.get('price', {}).get('decimal')
                        if parcel_price_decimal:
                            ticket_info['valor_parcelado'] = f"em até {max_installments_option.get('installments')}x R$ {parcel_price_decimal:.2f}".replace('.', ',')
                        else:
                            ticket_info['valor_parcelado'] = 'N/A'
                    else:
                        ticket_info['valor_parcelado'] = 'N/A'

                    end_date_str = ticket_item.get('endDate')
                    if end_date_str:
                        try:
                            dt_obj = datetime.strptime(end_date_str, '%Y-%m-%d %H:%M:%S')
                            ticket_info['data_limite_venda'] = dt_obj.strftime('%d/%m/%Y')
                        except ValueError:
                            ticket_info['data_limite_venda'] = 'N/A'
                    else:
                        ticket_info['data_limite_venda'] = 'N/A'

                    extracted_prices_info.append(ticket_info)

                    if isinstance(main_price_decimal, (int, float)):
                        numeric_prices.append(main_price_decimal)
                
                details['tipos_ingresso'] = extracted_prices_info

                if numeric_prices:
                    details['preco'] = f"A partir de R$ {min(numeric_prices):.2f}".replace('.', ',')
                    self.logger.info(f"Preço geral do evento (mínimo) via API: {details['preco']}")
                elif extracted_prices_info:
                    details['preco'] = extracted_prices_info[0].get('valor_principal', 'N/A')
                    self.logger.info(f"Preço geral do evento (primeiro texto) via API: {details['preco']}")
                else:
                    self.logger.warning("Nenhum preço de ingresso encontrado via API.")
            else:
                self.logger.warning("Nenhum dado de ingresso retornado pela API.")

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erro ao buscar dados de ingressos da API para {event_id}: {e}")
        except json.JSONDecodeError as e:
            self.logger.error(f"Erro ao decodificar JSON da API de ingressos para {event_id}: {e}")
        except Exception as e:
            self.logger.error(f"Erro inesperado na análise da API de ingressos para {event_id}: {e}")
        
        return details

    def scrape_events(self, city=None, filters=None, max_pages=3):
        all_events_data = []
        current_page = 1
        has_more_pages = True

        self.logger.info(f"Iniciando scraping do Sympla para {city if city else 'todos os eventos'}...")

        while has_more_pages and current_page <= max_pages:
            self.logger.info(f"\n--- Coletando eventos da página {current_page} ---")
            target_url = self.base_url
            if city:
                target_url = f"{self.base_url}?s=&cidade={city.replace(' ', '%20')}"
            if current_page > 1:
                target_url += f"&page={current_page}"

            html = self._fetch_page(target_url) 
            if html:
                events_on_page = self.parse_sympla_events_page(html)
                if events_on_page:
                    all_events_data.extend(events_on_page)
                    if len(events_on_page) < 24:
                        has_more_pages = False
                    current_page += 1
                    time.sleep(2)
                else:
                    has_more_pages = False
            else:
                has_more_pages = False 
        self.logger.info(f"\nTotal de eventos coletados de todas as páginas: {len(all_events_data)}.")
        return all_events_data