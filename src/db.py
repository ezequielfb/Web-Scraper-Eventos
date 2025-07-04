# src/db.py
import psycopg2
from psycopg2 import sql
from psycopg2 import extras
import json
import os
from dotenv import load_dotenv
from urllib.parse import urlparse
import re
from datetime import datetime # <-- MUDANÇA: Importar datetime

from .utils import logger

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

class Database:
    def __init__(self):
        self.logger = logger # <-- MUDANÇA: Atribuir o logger primeiro

        self.db_host = None
        self.db_name = None
        self.db_user = None
        self.db_password = None
        self.db_port = None
        
        # Tenta carregar DATABASE_URL primeiro (preferencial para Railway)
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            self.logger.info("DATABASE_URL encontrada. Parseando credenciais...")
            try:
                result = urlparse(database_url)
                self.db_host = result.hostname
                self.db_name = result.path[1:] # Remove a barra inicial
                self.db_user = result.username
                self.db_password = result.password
                self.db_port = result.port if result.port else 5432 # Padrão para 5432 se não especificado
            except Exception as e:
                self.logger.error(f"Erro ao parsear DATABASE_URL: {e}. Tentando variáveis individuais...")
        
        # Fallback para variáveis individuais se DATABASE_URL não existir ou falhar
        if not self.db_host: # Se o parse da DATABASE_URL falhou ou não existia
            self.db_host = os.getenv("DB_HOST")
            self.db_name = os.getenv("DB_NAME")
            self.db_user = os.getenv("DB_USER")
            self.db_password = os.getenv("DB_PASSWORD")
            self.db_port = os.getenv("DB_PORT", "5432")

        self.conn = None
        
        if self.db_host and self.db_name and self.db_user and self.db_password:
            self.logger.info(f"Credenciais carregadas para PostgreSQL: {self.db_user}@{self.db_host}:{self.db_port}/{self.db_name}")
        else:
            self.logger.error("Credenciais do PostgreSQL incompletas ou não encontradas. Verifique .env ou variáveis de ambiente.")

    def connect(self):
        """Estabelece e retorna uma conexão com o banco de dados PostgreSQL."""
        if not self.db_host or not self.db_name or not self.db_user or not self.db_password:
            self.logger.error("Credenciais do PostgreSQL incompletas. Não é possível conectar.")
            return None

        if self.conn is None:
            try:
                self.conn = psycopg2.connect(
                    host=self.db_host,
                    database=self.db_name,
                    user=self.db_user,
                    password=self.db_password,
                    port=self.db_port
                )
                self.logger.info("Conexão com PostgreSQL estabelecida.")
            except psycopg2.OperationalError as e:
                self.logger.error(f"Erro de conexão com o PostgreSQL: {e}")
                self.conn = None
            except Exception as e:
                self.logger.error(f"Erro inesperado ao conectar ao PostgreSQL: {e}")
                self.conn = None
        return self.conn

    def close(self):
        """Fecha a conexão com o banco de dados, se estiver aberta."""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.logger.info("Conexão com PostgreSQL fechada.")

    def create_table(self):
        """Cria a tabela 'eventos' se ela ainda não existir."""
        conn = self.connect()
        if not conn:
            self.logger.error("Não foi possível conectar ao DB para criar a tabela.")
            return

        cursor = conn.cursor()
        try:
            cursor.execute(sql.SQL("""
                CREATE TABLE IF NOT EXISTS eventos (
                    id SERIAL PRIMARY KEY,
                    nome_evento VARCHAR(255) NOT NULL,
                    nome_artista VARCHAR(255),
                    data_evento_inicio TEXT,
                    data_evento_fim TEXT,
                    local VARCHAR(255),
                    cidade VARCHAR(255),
                    estado VARCHAR(10),
                    link_compra VARCHAR(500) UNIQUE,
                    fonte_site VARCHAR(100),
                    data_coleta VARCHAR(255),
                    descricao TEXT,
                    organizador VARCHAR(255),
                    preco VARCHAR(255),
                    tipos_ingresso JSONB,
                    tipo_evento VARCHAR(50),      -- NOVA COLUNA
                    genero_musical VARCHAR(50)    -- NOVA COLUNA
                )
            """))
            conn.commit()
            self.logger.info("Tabela 'eventos' verificada/criada com sucesso no PostgreSQL.")
        except psycopg2.Error as e:
            self.logger.error(f"Erro ao criar tabela no PostgreSQL: {e}")
            conn.rollback()
        finally:
            cursor.close()
            self.close()

    def insert_event(self, event_data):
        """
        Insere um novo evento no banco de dados ou atualiza um existente
        com base no link_compra.
        """
        conn = self.connect()
        if not conn:
            self.logger.error("Não foi possível conectar ao DB para inserir/atualizar evento.")
            return

        cursor = conn.cursor()
        try:
            tipos_ingresso_json = json.dumps(event_data.get('tipos_ingresso', []))

            cursor.execute(sql.SQL("SELECT id FROM eventos WHERE link_compra = %s"), [event_data.get('link_compra')])
            existing_event = cursor.fetchone()

            tipo_evento = event_data.get('tipo_evento', 'Desconhecido')
            genero_musical = event_data.get('genero_musical', 'Desconhecido')

            if existing_event:
                cursor.execute(
                    sql.SQL("""
                        UPDATE eventos SET
                            nome_evento = %s,
                            nome_artista = %s,
                            data_evento_inicio = %s,
                            data_evento_fim = %s,
                            local = %s,
                            cidade = %s,
                            estado = %s,
                            fonte_site = %s,
                            data_coleta = %s,
                            descricao = %s,
                            organizador = %s,
                            preco = %s,
                            tipos_ingresso = %s,
                            tipo_evento = %s,
                            genero_musical = %s
                        WHERE link_compra = %s
                    """),
                    (
                        event_data.get('nome_evento'),
                        event_data.get('nome_artista'),
                        event_data.get('data_evento_inicio'),
                        event_data.get('data_evento_fim'),
                        event_data.get('local'),
                        event_data.get('cidade'),
                        event_data.get('estado'),
                        event_data.get('fonte_site'),
                        event_data.get('data_coleta'),
                        event_data.get('descricao', 'N/A'),
                        event_data.get('organizador', 'N/A'),
                        event_data.get('preco', 'N/A'),
                        tipos_ingresso_json,
                        tipo_evento,
                        genero_musical,
                        event_data.get('link_compra')
                    )
                )
                self.logger.info(f"Evento '{event_data.get('nome_evento')}' já existe. Atualizando dados.")
            else:
                cursor.execute(
                    sql.SQL("""
                        INSERT INTO eventos (
                            nome_evento, nome_artista, data_evento_inicio, data_evento_fim,
                            local, cidade, estado, link_compra, fonte_site, data_coleta,
                            descricao, organizador, preco, tipos_ingresso,
                            tipo_evento,
                            genero_musical
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """),
                    (
                        event_data.get('nome_evento'),
                        event_data.get('nome_artista'),
                        event_data.get('data_evento_inicio'),
                        event_data.get('data_evento_fim'),
                        event_data.get('local'),
                        event_data.get('cidade'),
                        event_data.get('estado'),
                        event_data.get('link_compra'),
                        event_data.get('fonte_site'),
                        event_data.get('data_coleta'),
                        event_data.get('descricao', 'N/A'),
                        event_data.get('organizador', 'N/A'),
                        event_data.get('preco', 'N/A'),
                        tipos_ingresso_json,
                        tipo_evento,
                        genero_musical
                    )
                )
                self.logger.info(f"Evento '{event_data.get('nome_evento')}' inserido com sucesso.")
            
            conn.commit()
        except psycopg2.Error as e:
            self.logger.error(f"Erro ao inserir/atualizar evento '{event_data.get('nome_evento')}' no PostgreSQL: {e}")
            conn.rollback()
        finally:
            cursor.close()
            self.close()

    def get_all_events(self):
        """Retorna todos os eventos armazenados no banco de dados PostgreSQL."""
        conn = self.connect()
        if not conn:
            self.logger.error("Não foi possível conectar ao DB para buscar eventos.")
            return []

        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        try:
            cursor.execute(sql.SQL("SELECT * FROM eventos"))
            rows = cursor.fetchall()
        except psycopg2.Error as e:
            self.logger.error(f"Erro ao buscar eventos do PostgreSQL: {e}")
            rows = []
        finally:
            cursor.close()
            self.close()
        
        events = []
        for row in rows:
            event = dict(row)
            if 'tipos_ingresso' in event and event['tipos_ingresso'] is None:
                event['tipos_ingresso'] = []
            events.append(event)
        return events

    def filter_events(self, city=None, tipo_evento=None, genero_musical=None,
                      min_preco=None, max_preco=None, start_date=None, end_date=None,
                      order_by='data_evento_inicio', order_direction='ASC'):
        """
        Filtra eventos no banco de dados com base nos critérios fornecidos.
        
        Args:
            city (str, optional): Filtra pela cidade.
            tipo_evento (str, optional): Filtra pelo tipo de evento (ex: 'Música', 'Teatro').
            genero_musical (str, optional): Filtra pelo gênero musical (ex: 'Rock', 'Samba/Pagode').
            min_preco (float, optional): Filtra por preço mínimo (valor numérico).
            max_preco (float, optional): Filtra por preço máximo (valor numérico).
            start_date (str, optional): Filtra por eventos a partir de uma data (formato 'YYYY-MM-DD').
            end_date (str, optional): Filtra por eventos até uma data (formato 'YYYY-MM-DD').
            order_by (str, optional): Coluna para ordenar os resultados. Default 'data_evento_inicio'.
            order_direction (str, optional): Direção da ordenação ('ASC' ou 'DESC'). Default 'ASC'.

        Returns:
            list: Uma lista de dicionários, cada um representando um evento filtrado.
        """
        conn = self.connect()
        if not conn:
            self.logger.error("Não foi possível conectar ao DB para filtrar eventos.")
            return []

        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        query_parts = []
        query_params = []

        # Adicionar filtros de texto
        if city:
            query_parts.append(sql.SQL("cidade ILIKE %s")) # ILIKE para case-insensitive
            query_params.append(f"%{city}%") # Usar % para busca parcial ou completa

        if tipo_evento:
            query_parts.append(sql.SQL("tipo_evento ILIKE %s"))
            query_params.append(f"%{tipo_evento}%")

        if genero_musical:
            query_parts.append(sql.SQL("genero_musical ILIKE %s"))
            query_params.append(f"%{genero_musical}%")

        # Construção da query WHERE clause
        where_clause = sql.SQL("")
        if query_parts:
            where_clause = sql.SQL("WHERE ") + sql.SQL(" AND ").join(query_parts)

        # Construir a query principal
        full_query = sql.SQL("SELECT * FROM eventos ") + where_clause

        # Adicionar ordenação
        if order_by and order_direction in ['ASC', 'DESC']:
            full_query += sql.SQL(" ORDER BY {} {}").format(
                sql.Identifier(order_by),
                sql.SQL(order_direction)
            )
        
        filtered_events = []
        try:
            cursor.execute(full_query, query_params)
            rows = cursor.fetchall()
            
            # --- Filtragem em Python para preço e data (Devido a armazenamento VARCHAR) ---
            # Idealmente, 'preco' seria NUMERIC e datas seriam DATE/TIMESTAMP no DB
            # para filtrar diretamente no SQL de forma mais eficiente.
            for row in rows:
                event = dict(row)
                
                # Conversão e filtragem de preço
                event_price_str = event.get('preco', 'N/A')
                current_price = None
                if event_price_str != 'N/A':
                    match = re.search(r'R\$\s*([\d\.,]+)', event_price_str)
                    if match:
                        try:
                            # Limpa o valor para float (remove . de milhar, troca , por .)
                            parsed_price_str = match.group(1).replace('.', '').replace(',', '.')
                            current_price = float(parsed_price_str)
                        except ValueError:
                            pass # current_price permanece None

                if min_preco is not None and current_price is not None and current_price < min_preco:
                    continue # Pula evento se preço abaixo do mínimo
                if max_preco is not None and current_price is not None and current_price > max_preco:
                    continue # Pula evento se preço acima do máximo

                # Conversão e filtragem de data
                # Assumindo data_evento_inicio está em formato 'YYYY-MM-DD HH:MM:SS'
                # ou 'Sábado, 19 de Jul às 14:00' para dados do Sympla.
                # Para uma filtragem robusta por data, o campo `data_evento_inicio`
                # DEVERIA ser um tipo DATE ou TIMESTAMP no banco de dados.
                event_start_date_str = event.get('data_evento_inicio', '')
                event_date_obj = None

                if event_start_date_str != 'N/A':
                    try: # Tenta parsear do formato API (YYYY-MM-DD HH:MM:SS)
                        event_date_obj = datetime.strptime(event_start_date_str, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        try: # Tenta parsear do formato da lista Sympla ('Dia da Semana, DD de Mês às HH:MM')
                            # Ex: 'Sábado, 19 de Jul às 14:00'
                            meses_pt_br = {
                                'Jan': 1, 'Fev': 2, 'Mar': 3, 'Abr': 4, 'Mai': 5, 'Jun': 6,
                                'Jul': 7, 'Ago': 8, 'Set': 9, 'Out': 10, 'Nov': 11, 'Dez': 12
                            }
                            parts = event_start_date_str.split(' ')
                            if len(parts) >= 6: 
                                day = int(parts[2])
                                month = meses_pt_br.get(parts[4])
                                hour_minute = parts[6]

                                if month:
                                    # Heurística para o ano: se o mês já passou, assume próximo ano.
                                    # CUIDADO: Isso pode não ser 100% preciso para eventos muito no futuro.
                                    current_year = datetime.now().year
                                    if month < datetime.now().month:
                                        year_to_use = current_year + 1
                                    else:
                                        year_to_use = current_year
                                    
                                    try:
                                        event_date_obj = datetime.strptime(f"{year_to_use}-{month:02d}-{day:02d} {hour_minute}", '%Y-%m-%d %H:%M')
                                    except ValueError:
                                        pass # Failed to parse
                        except Exception:
                            pass # Catch all for complex date parsing

                if event_date_obj:
                    # Comparação de datas (apenas a parte da data)
                    if start_date:
                        try:
                            filter_start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
                            if event_date_obj.date() < filter_start_date_obj.date():
                                continue
                        except ValueError:
                            self.logger.warning(f"Formato inválido para start_date: {start_date}. Use असाल-MM-DD.")
                    
                    if end_date:
                        try:
                            filter_end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
                            if event_date_obj.date() > filter_end_date_obj.date():
                                continue
                        except ValueError:
                            self.logger.warning(f"Formato inválido para end_date: {end_date}. Use असाल-MM-DD.")


                # Se passou por todos os filtros, adiciona o evento
                if 'tipos_ingresso' in event and event['tipos_ingresso'] is None:
                    event['tipos_ingresso'] = []
                filtered_events.append(event)

        except psycopg2.Error as e:
            self.logger.error(f"Erro ao filtrar eventos do PostgreSQL: {e}")
        finally:
            cursor.close()
            self.close()
        
        return filtered_events