"""
Módulo para persistência e gestão de dados da API KOB CAR.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

import pandas as pd
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.exc import SQLAlchemyError

from .utils import setup_logging, sanitize_filename, flatten_dict, safe_convert


class DataStorage:
    """Gerenciador de armazenamento de dados."""
    
    def __init__(
        self,
        base_path: str = "./data",
        db_path: Optional[str] = None,
        logger=None
    ):
        """
        Inicializa o gerenciador de armazenamento.
        
        Args:
            base_path: Diretório base para armazenamento de arquivos
            db_path: Caminho para o banco SQLite (padrão: {base_path}/kob_car.db)
            logger: Logger customizado (opcional)
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        self.db_path = db_path or str(self.base_path / "kob_car.db")
        self.engine = None
        self.metadata = MetaData()
        
        self.logger = logger or setup_logging()
    
    def _get_engine(self):
        """Obtém ou cria a engine do SQLAlchemy."""
        if not self.engine:
            self.engine = create_engine(f'sqlite:///{self.db_path}')
            self.logger.info(f"Conexão com banco de dados criada: {self.db_path}")
        return self.engine
    
    def save_json(
        self,
        data: Any,
        filename: str,
        subdir: Optional[str] = None,
        indent: int = 2
    ) -> str:
        """
        Salva dados em formato JSON.
        
        Args:
            data: Dados a serem salvos
            filename: Nome do arquivo
            subdir: Subdiretório (opcional)
            indent: Indentação do JSON
            
        Returns:
            Caminho completo do arquivo salvo
        """

        if subdir:
            save_path = self.base_path / subdir
            save_path.mkdir(parents=True, exist_ok=True)
        else:
            save_path = self.base_path
        

        filename = sanitize_filename(filename)
        if not filename.endswith('.json'):
            filename += '.json'
        
        filepath = save_path / filename
        

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False, default=str)
        
        self.logger.info(f"Dados salvos em JSON: {filepath}")
        return str(filepath)
    
    def load_json(self, filename: str, subdir: Optional[str] = None) -> Any:
        """
        Carrega dados de um arquivo JSON.
        
        Args:
            filename: Nome do arquivo
            subdir: Subdiretório (opcional)
            
        Returns:
            Dados carregados
        """
        if subdir:
            filepath = self.base_path / subdir / filename
        else:
            filepath = self.base_path / filename
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.logger.info(f"Dados carregados de JSON: {filepath}")
        return data
    
    def save_csv(
        self,
        data: List[Dict],
        filename: str,
        subdir: Optional[str] = None,
        flatten: bool = True
    ) -> str:
        """
        Salva dados em formato CSV.
        
        Args:
            data: Lista de dicionários
            filename: Nome do arquivo
            subdir: Subdiretório (opcional)
            flatten: Se True, achata dicionários aninhados
            
        Returns:
            Caminho completo do arquivo salvo
        """
        if not data:
            self.logger.warning("Nenhum dado para salvar em CSV")
            return ""
        

        if subdir:
            save_path = self.base_path / subdir
            save_path.mkdir(parents=True, exist_ok=True)
        else:
            save_path = self.base_path
        

        filename = sanitize_filename(filename)
        if not filename.endswith('.csv'):
            filename += '.csv'
        
        filepath = save_path / filename
        

        if flatten:
            data = [flatten_dict(item) for item in data]
        

        df = pd.DataFrame(data)
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        
        self.logger.info(f"Dados salvos em CSV: {filepath} ({len(data)} registros)")
        return str(filepath)
    
    def load_csv(self, filename: str, subdir: Optional[str] = None) -> pd.DataFrame:
        """
        Carrega dados de um arquivo CSV.
        
        Args:
            filename: Nome do arquivo
            subdir: Subdiretório (opcional)
            
        Returns:
            DataFrame com os dados
        """
        if subdir:
            filepath = self.base_path / subdir / filename
        else:
            filepath = self.base_path / filename
        
        df = pd.read_csv(filepath, encoding='utf-8-sig')
        
        self.logger.info(f"Dados carregados de CSV: {filepath} ({len(df)} registros)")
        return df
    
    def save_excel(
        self,
        data: Dict[str, List[Dict]],
        filename: str,
        subdir: Optional[str] = None
    ) -> str:
        """
        Salva múltiplas tabelas em um arquivo Excel (uma por aba).
        
        Args:
            data: Dicionário onde chave é o nome da aba e valor é lista de dicionários
            filename: Nome do arquivo
            subdir: Subdiretório (opcional)
            
        Returns:
            Caminho completo do arquivo salvo
        """
        if not data:
            self.logger.warning("Nenhum dado para salvar em Excel")
            return ""
        

        if subdir:
            save_path = self.base_path / subdir
            save_path.mkdir(parents=True, exist_ok=True)
        else:
            save_path = self.base_path
        

        filename = sanitize_filename(filename)
        if not filename.endswith('.xlsx'):
            filename += '.xlsx'
        
        filepath = save_path / filename
        

        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            for sheet_name, sheet_data in data.items():
                if sheet_data:
                    df = pd.DataFrame(sheet_data)
                    df.to_excel(writer, sheet_name=sheet_name[:31], index=False)
        
        self.logger.info(f"Dados salvos em Excel: {filepath} ({len(data)} abas)")
        return str(filepath)
    
    def save_to_database(
        self,
        data: List[Dict],
        table_name: str,
        if_exists: str = 'replace',
        flatten: bool = True
    ) -> int:
        """
        Salva dados em banco SQLite.
        
        Args:
            data: Lista de dicionários
            table_name: Nome da tabela
            if_exists: Ação se tabela existir ('fail', 'replace', 'append')
            flatten: Se True, achata dicionários aninhados
            
        Returns:
            Número de registros salvos
        """
        if not data:
            self.logger.warning("Nenhum dado para salvar no banco")
            return 0
        

        if flatten:
            data = [flatten_dict(item) for item in data]
        df = pd.DataFrame(data)
        
        for col in df.columns:
            if df[col].dtype == 'object':

                sample = df[col].dropna().head(1)
                if len(sample) > 0:
                    first_value = sample.iloc[0]
                    if isinstance(first_value, (list, dict)):
                        self.logger.info(f"Convertendo coluna '{col}' com tipo complexo para string")
                        df[col] = df[col].apply(lambda x: str(x) if safe_convert(x) else None)

        engine = self._get_engine()
        
        try:
            df.to_sql(
                name=table_name,
                con=engine,
                if_exists=if_exists,
                index=False,
            )
            
            self.logger.info(
                f"Dados salvos no banco: tabela '{table_name}' ({len(data)} registros)"
            )
            return len(data)
            
        except SQLAlchemyError as e:
            self.logger.error(f"Erro ao salvar no banco: {e}")
            raise
    
    def query_database(self, query: str) -> pd.DataFrame:
        """
        Executa uma query SQL no banco.
        
        Args:
            query: Query SQL
            
        Returns:
            DataFrame com resultados
        """
        engine = self._get_engine()
        
        try:
            df = pd.read_sql(query, con=engine)
            self.logger.info(f"Query executada: {len(df)} registros retornados")
            return df
            
        except SQLAlchemyError as e:
            self.logger.error(f"Erro ao executar query: {e}")
            raise
    
    def execute_query(self, query: str, params: Optional[Dict] = None) -> int:
        """
        Executa uma query SQL de modificação (INSERT, UPDATE, DELETE) no banco.
        
        Args:
            query: Query SQL a ser executada
            params: Parâmetros para a query (opcional)
            
        Returns:
            Número de linhas afetadas
            
        Raises:
            SQLAlchemyError: Se houver erro na execução da query
        """
        engine = self._get_engine()
        
        try:
            with engine.begin() as connection:
                result = connection.execute(query, params or {})
                rows_affected = result.rowcount
                
            self.logger.info(f"Query executada com sucesso: {rows_affected} linhas afetadas")
            return rows_affected
            
        except SQLAlchemyError as e:
            self.logger.error(f"Erro ao executar query: {e}")
            raise
    
    def upsert_to_database(
        self,
        data,
        table_name: str,
        primary_keys: List[str],
        flatten: bool = False
    ) -> int:
        """
        Realiza UPSERT (INSERT OR REPLACE) de dados no banco SQLite.
        Atualiza registros existentes ou insere novos baseado nas chaves primárias.
        
        Args:
            data: DataFrame ou lista de dicionários com os dados
            table_name: Nome da tabela
            primary_keys: Lista de colunas que formam a chave primária
            flatten: Se True, achata dicionários aninhados (apenas para listas de dict)
            
        Returns:
            Número de registros processados
            
        Raises:
            SQLAlchemyError: Se houver erro na execução
        """
        self.logger.info("Função de Upsert Ativada")

        if data is None or (isinstance(data, (list, pd.DataFrame)) and len(data) == 0):
            self.logger.warning("Nenhum dado para fazer upsert no banco")
            return 0
        

        if isinstance(data, pd.DataFrame):
            df = data
        elif isinstance(data, list):

            if data and not isinstance(data[0], dict):
                raise ValueError("data deve ser um DataFrame ou lista de dicionários")
            

            if flatten:
                data = [flatten_dict(item) for item in data]
            

            df = pd.DataFrame(data)
        else:
            raise TypeError("data deve ser um DataFrame ou lista de dicionários")
        

        engine = self._get_engine()

        

        columns = df.columns.tolist()
        placeholders = ', '.join(['?' for _ in columns])
        columns_str = ', '.join([f'"{col}"' for col in columns])

        upsert_query = f"""
            INSERT OR REPLACE INTO {table_name} ({columns_str})
            VALUES ({placeholders})
        """

        try:
            self.logger.info("Iniciando processo de Upsert")
            with engine.begin() as connection:

                values_list = [tuple(row[col] for col in columns) for _, row in df.iterrows()]
                

                connection.connection.executemany(upsert_query, values_list)
            
            self.logger.info(
                f"UPSERT realizado na tabela '{table_name}': {len(df)} registros processados"
            )
            return len(df)
            
        except SQLAlchemyError as e:
            self.logger.error(f"Erro ao fazer upsert no banco: {e}")
            raise

    def bulk_upsert_to_database(
        self,
        data: List[Dict],
        table_name: str,
        primary_keys: List[str],
        flatten: bool = True,
        batch_size: int = 1000
    ) -> int:
        """
        Realiza UPSERT em lote para melhor performance com grandes volumes de dados.
        
        Args:
            data: Lista de dicionários com os dados
            table_name: Nome da tabela
            primary_keys: Lista de colunas que formam a chave primária
            flatten: Se True, achata dicionários aninhados
            batch_size: Tamanho do lote para processamento
            
        Returns:
            Número total de registros processados
        """
        if not data:
            self.logger.warning("Nenhum dado para fazer upsert no banco")
            return 0
        
        total_processed = 0
        

        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            processed = self.upsert_to_database(
                batch,
                table_name,
                primary_keys,
                flatten
            )
            total_processed += processed
            
            self.logger.info(
                f"Lote {i // batch_size + 1}: {processed} registros processados"
            )
        
        return total_processed
    
    def create_snapshot(
        self,
        data: Dict[str, Any],
        prefix: str = "snapshot"
    ) -> str:
        """
        Cria um snapshot timestamped dos dados.
        
        Args:
            data: Dados a serem salvos
            prefix: Prefixo do nome do arquivo
            
        Returns:
            Caminho do arquivo criado
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{timestamp}.json"
        
        return self.save_json(data, filename, subdir="snapshots")
    
    def list_files(self, subdir: Optional[str] = None, pattern: str = "*") -> List[str]:
        """
        Lista arquivos no diretório de dados.
        
        Args:
            subdir: Subdiretório (opcional)
            pattern: Padrão de busca (glob)
            
        Returns:
            Lista de caminhos de arquivos
        """
        if subdir:
            search_path = self.base_path / subdir
        else:
            search_path = self.base_path
        
        if not search_path.exists():
            return []
        
        files = [str(f) for f in search_path.glob(pattern) if f.is_file()]
        return sorted(files)


class DataProcessor:
    """Processador de dados da API KOB CAR."""
    def __init__(self, logger=None):
        """
        Inicializa o processador de dados.
        
        Args:
            logger: Logger customizado (opcional)
        """
        self.logger = logger or setup_logging()
    
    def aggregate_compradores(self, compradores: List[Dict]) -> Dict[str, Any]:
        """
        Agrega estatísticas sobre compradores.
        
        Args:
            compradores: Lista de compradores
            
        Returns:
            Dicionário com estatísticas
        """
        if not compradores:
            return {}
        
        df = pd.DataFrame(compradores)
        
        stats = {
            'total_compradores': len(compradores),
            'limite_total_concedido': 0,
            'limite_total_disponivel': 0,
            'por_status': {},
            'timestamp': datetime.now().isoformat()
        }
        

        if 'limites' in df.columns:
            limites_df = pd.json_normalize(df['limites'])
            if 'limiteConcedido' in limites_df.columns:
                stats['limite_total_concedido'] = float(limites_df['limiteConcedido'].sum())
            if 'limiteDisponivel' in limites_df.columns:
                stats['limite_total_disponivel'] = float(limites_df['limiteDisponivel'].sum())
        

        if 'status' in df.columns:
            stats['por_status'] = df['status'].value_counts().to_dict()
        
        self.logger.info(f"Agregação de compradores concluída: {stats['total_compradores']} compradores")
        return stats
    
    def aggregate_recebiveis(self, recebiveis: List[Dict]) -> Dict[str, Any]:
        """
        Agrega estatísticas sobre recebíveis.
        
        Args:
            recebiveis: Lista de recebíveis
            
        Returns:
            Dicionário com estatísticas
        """
        if not recebiveis:
            return {}
        
        df = pd.DataFrame(recebiveis)
        
        stats = {
            'total_recebiveis': len(recebiveis),
            'valor_total': 0,
            'por_status': {},
            'timestamp': datetime.now().isoformat()
        }
        

        if 'valor' in df.columns:
            stats['valor_total'] = float(df['valor'].sum())
        

        if 'estado' in df.columns:
            stats['por_status'] = df['estado'].value_counts().to_dict()
        elif 'status' in df.columns:
            stats['por_status'] = df['status'].value_counts().to_dict()
        
        self.logger.info(f"Agregação de recebíveis concluída: {stats['total_recebiveis']} recebíveis")
        return stats
    
    def filter_by_date_range(
        self,
        data: List[Dict],
        date_field: str,
        start_date: str,
        end_date: str
    ) -> List[Dict]:
        """
        Filtra dados por intervalo de datas.
        
        Args:
            data: Lista de dicionários
            date_field: Nome do campo de data
            start_date: Data inicial (ISO-8601)
            end_date: Data final (ISO-8601)
            
        Returns:
            Lista filtrada
        """
        if not data:
            return []
        
        df = pd.DataFrame(data)
        
        if date_field not in df.columns:
            self.logger.warning(f"Campo '{date_field}' não encontrado nos dados")
            return data
        

        df[date_field] = pd.to_datetime(df[date_field])
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        

        filtered_df = df[(df[date_field] >= start) & (df[date_field] <= end)]
        
        self.logger.info(
            f"Filtro de data aplicado: {len(filtered_df)} de {len(df)} registros mantidos"
        )
        
        return filtered_df.to_dict('records')
    
    def group_by_field(
        self,
        data: List[Dict],
        field: str,
        flatten: bool = False
    ) -> Dict[str, List[Dict]]:
        """
        Agrupa dados por um campo específico.
        
        Args:
            data: Lista de dicionários
            field: Campo para agrupamento
            flatten: Se True, achata dicionários aninhados antes de agrupar
            
        Returns:
            Dicionário com dados agrupados
        """
        if not data:
            return {}
        
        if flatten:
            data = [flatten_dict(item) for item in data]
        
        df = pd.DataFrame(data)
        
        if field not in df.columns:
            self.logger.warning(f"Campo '{field}' não encontrado nos dados")
            return {}
        
        grouped = df.groupby(field)
        result = {str(key): group.to_dict('records') for key, group in grouped}
        
        self.logger.info(f"Dados agrupados por '{field}': {len(result)} grupos")
        return result

    @staticmethod
    def get_total_count(storage, table_name:str):
        return storage.query_database(f"SELECT COUNT(*) as total FROM {table_name}")