"""
Exceções customizadas para o cliente da API KOB CAR.
"""


class KobAPIException(Exception):
    """Exceção base para todas as exceções da API KOB."""
    
    def __init__(self, message: str, status_code: int = None, payload: dict = None):
        self.message = message
        self.status_code = status_code
        self.payload = payload or {}
        super().__init__(self.message)
    
    def __str__(self):
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


class KobAuthenticationError(KobAPIException):
    """Erro de autenticação na API KOB."""
    pass


class KobAuthorizationError(KobAPIException):
    """Erro de autorização - usuário não tem permissão para acessar o recurso."""
    pass


class KobValidationError(KobAPIException):
    """Erro de validação de dados enviados para a API."""
    pass


class KobNotFoundError(KobAPIException):
    """Recurso não encontrado na API."""
    pass


class KobAPIError(KobAPIException):
    """Erro genérico da API KOB."""
    pass


class KobConnectionError(KobAPIException):
    """Erro de conexão com a API KOB."""
    pass


class KobTimeoutError(KobAPIException):
    """Timeout na requisição para a API KOB."""
    pass


class KobConfigurationError(KobAPIException):
    """Erro de configuração do cliente."""
    pass

