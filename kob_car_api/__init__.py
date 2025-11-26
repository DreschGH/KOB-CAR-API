"""
KOB CAR API Client - Cliente Python para a API de Contas a Receber da plataforma KOB.
"""

from .client import KobCARClient
from .auth import AuthManager
from .storage import DataStorage, DataProcessor
from .exceptions import (
    KobAPIException,
    KobAuthenticationError,
    KobAuthorizationError,
    KobValidationError,
    KobNotFoundError,
    KobAPIError,
    KobConnectionError,
    KobTimeoutError,
    KobConfigurationError
)
from .validators import Validators
from .utils import (
    setup_logging,
    format_cnpj,
    format_cpf,
    format_currency,
    parse_iso_date,
    format_date
)

__version__ = "1.0.0"
__author__ = "Gabriel Henrique Dresch"
__email__ = "gabriel.dresch@intelbras.com"

__all__ = [
    # Cliente principal
    "KobCARClient",
    
    # Autenticação
    "AuthManager",
    
    # Armazenamento
    "DataStorage",
    "DataProcessor",
    
    # Exceções
    "KobAPIException",
    "KobAuthenticationError",
    "KobAuthorizationError",
    "KobValidationError",
    "KobNotFoundError",
    "KobAPIError",
    "KobConnectionError",
    "KobTimeoutError",
    "KobConfigurationError",
    
    # Validadores
    "Validators",
    
    # Utilitários
    "setup_logging",
    "format_cnpj",
    "format_cpf",
    "format_currency",
    "parse_iso_date",
    "format_date",
]

