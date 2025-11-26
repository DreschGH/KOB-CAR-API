"""
Funções utilitárias para o cliente da API KOB CAR.
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
import pandas as pd
import pandas as np
import calendar


def setup_logging(
    log_level: str = "INFO",
    log_dir: str = "./logs",
    log_file: str = "kob_car_api.log"
) -> logging.Logger:
    """
    Configura o sistema de logging.
    
    Args:
        log_level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Diretório para salvar os logs
        log_file: Nome do arquivo de log
        
    Returns:
        Logger configurado
    """

    Path(log_dir).mkdir(parents=True, exist_ok=True)
    

    logger = logging.getLogger("kob_car_api")
    logger.setLevel(getattr(logging, log_level.upper()))
    

    if logger.handlers:
        return logger
    

    file_handler = logging.FileHandler(
        os.path.join(log_dir, log_file),
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    

    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper()))
    

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def safe_convert(x):
    if x is None:
        return None
    if isinstance(x, np.ndarray):
        return str(x) if x.size > 0 else None
    if isinstance(x, list) > 0:
        return str(x) if len(x) > 0 else None
    if pd.isna(x):
        return None
    return str(x)
    
def format_cnpj(cnpj: str) -> str:
    """
    Formata um CNPJ para exibição.
    
    Args:
        cnpj: CNPJ sem formatação (14 dígitos)
        
    Returns:
        CNPJ formatado (XX.XXX.XXX/XXXX-XX)
    """
    if len(cnpj) != 14:
        return cnpj
    
    return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"

def format_cpf(cpf: str) -> str:
    """
    Formata um CPF para exibição.
    
    Args:
        cpf: CPF sem formatação (11 dígitos)
        
    Returns:
        CPF formatado (XXX.XXX.XXX-XX)
    """
    if len(cpf) != 11:
        return cpf
    
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"

def format_currency(value: float) -> str:
    """
    Formata um valor monetário para exibição.
    
    Args:
        value: Valor numérico
        
    Returns:
        Valor formatado como moeda brasileira
    """
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def parse_iso_date(date_str: str) -> datetime:
    """
    Converte uma string ISO-8601 para datetime.
    
    Args:
        date_str: String de data no formato ISO-8601
        
    Returns:
        Objeto datetime
    """
    return datetime.fromisoformat(date_str.replace('Z', '+00:00'))

def format_date(date_obj: datetime, format_str: str = "%d/%m/%Y %H:%M:%S") -> str:
    """
    Formata um objeto datetime para string.
    
    Args:
        date_obj: Objeto datetime
        format_str: Formato de saída
        
    Returns:
        Data formatada como string
    """
    return date_obj.strftime(format_str)

def to_iso_datetime(date_obj: datetime) -> str:
    """
    Converte um objeto datetime para uma string no formato ISO 8601.
    
    Args:
        date_obj: Objeto datetime
    
    Returns:
        String no formato ISO 8601 (ex: '2025-10-28T14:35:22')
    """
    return date_obj.isoformat()

def sanitize_filename(filename: str) -> str:
    """
    Remove caracteres inválidos de um nome de arquivo.
    
    Args:
        filename: Nome do arquivo
        
    Returns:
        Nome do arquivo sanitizado
    """
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename

def deep_get(dictionary: Dict, keys: str, default: Any = None) -> Any:
    """
    Obtém um valor aninhado em um dicionário usando notação de ponto.
    
    Args:
        dictionary: Dicionário a ser consultado
        keys: Chaves separadas por ponto (ex: "pessoa.nome")
        default: Valor padrão se a chave não existir
        
    Returns:
        Valor encontrado ou default
    """
    keys_list = keys.split('.')
    value = dictionary
    
    for key in keys_list:
        if isinstance(value, dict):
            value = value.get(key)
            if value is None:
                return default
        else:
            return default
    
    return value

def flatten_dict(d: Dict, parent_key: str = '', sep: str = '_') -> Dict:
    """
    Achata um dicionário aninhado.
    
    Args:
        d: Dicionário a ser achatado
        parent_key: Chave pai (usado na recursão)
        sep: Separador entre chaves
        
    Returns:
        Dicionário achatado
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def chunk_list(lst: list, chunk_size: int) -> list:
    """
    Divide uma lista em chunks menores.
    
    Args:
        lst: Lista a ser dividida
        chunk_size: Tamanho de cada chunk
        
    Returns:
        Lista de chunks
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

def safe_cast(value: Any, to_type: type, default: Any = None) -> Any:
    """
    Tenta converter um valor para um tipo específico de forma segura.
    
    Args:
        value: Valor a ser convertido
        to_type: Tipo de destino
        default: Valor padrão em caso de erro
        
    Returns:
        Valor convertido ou default
    """
    try:
        return to_type(value)
    except (ValueError, TypeError):
        return default

def normalize_vendas_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza os nomes das colunas do DataFrame de vendas.
    
    Args:
        df: DataFrame com dados de vendas
        
    Returns:
        DataFrame com colunas normalizadas
    """
    df = df.rename(columns={
        "comprador.cnpj": "comprador_cnpj",
        "comprador.nomeFantasia": "comprador_nomeFantasia",
        "comprador.razaoSocial": "comprador_razaoSocial",
        "vendedor.cnpj": "vendedor_cnpj",
        "vendedor.nomeFantasia": "vendedor_nomeFantasia",
        "vendedor.razaoSocial": "vendedor_razaoSocial"
    })
 
    for col in df.columns:
        if df[col].dtype == 'object':
            is_list_or_dict = df[col].dropna().apply(lambda x: isinstance(x, (list, dict))).any()
            if is_list_or_dict:
                print(f"  > Convertendo coluna de vendas aninhada: {col}")
                df[col] = df[col].astype(str)


    if 'numeroNotasFiscais' in df.columns:
         df['numeroNotasFiscais'] = df['numeroNotasFiscais'].astype(str)
            
    return df

def normalize_reservas_columns(df: pd.DataFrame) -> pd.DataFrame:

    df = df.rename(columns={
        "comprador.cnpj": "comprador_cnpj",
        "comprador.nomeFantasia": "comprador_nomeFantasia",
        "comprador.razaoSocial": "comprador_razaoSocial",
        "vendedor.cnpj": "vendedor_cnpj",
        "vendedor.nomeFantasia": "vendedor_nomeFantasia",
        "vendedor.razaoSocial": "vendedor_razaoSocial"
    })
    
    for col in df.columns:
        if df[col].dtype == 'object':
            is_list_or_dict = df[col].dropna().apply(lambda x: isinstance(x, (list, dict))).any()
            if is_list_or_dict:
                print(f"  > Convertendo coluna de reservas aninhada: {col}")
                df[col] = df[col].astype(str)
                
    return df

def normalize_compradores_columns(df:pd.DataFrame) -> pd.DataFrame:

    df=df.rename(
        columns={
            "pessoaJuridica.cnpj":"pessoaJuridica_cnpj",
            "pessoaJuridica.nomeFantasia":"pessoaJuridica_nomeFantasia",
            "pessoaJuridica.razaoSocial":"pessoaJuridica_razaoSocial"
        }
    )
    for col in df.columns:
        if df[col].dtype == 'object':
            is_list_or_dict = df[col].dropna().apply(lambda x: isinstance(x, (list, dict))).any()
            if is_list_or_dict:
                print(f"  > Convertendo coluna de compradores aninhada: {col}")
                df[col] = df[col].astype(str)

    return df

def get_last_n_months(n):
    """
    Retorna os últimos n meses com primeiro e último dia de cada mês.
    
    Args:
        n: Número de meses a retornar
    
    Yields:
        tuple: (primeiro_dia, ultimo_dia, ano, mes)
    """
    today = datetime.now()
    current_year = today.year
    current_month = today.month
    
    for i in range(n): 
        month = current_month - i
        year = current_year
        while month <= 0:
            month += 12
            year -= 1
        first_day = datetime(year, month, 1)
        last_day_num = calendar.monthrange(year, month)[1]
        last_day = datetime(year, month, last_day_num)
        yield (first_day, last_day, year, month)
