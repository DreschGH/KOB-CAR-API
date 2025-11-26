"""
Gerenciamento de autenticação para a API KOB CAR.
"""

import logging
from typing import Optional
import requests

from .exceptions import KobAuthenticationError, KobConnectionError
from .utils import setup_logging


class AuthManager:
    """Gerenciador de autenticação e tokens."""
    
    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        timeout: int = 30,
        logger: Optional[logging.Logger] = None
    ):
        """
        Inicializa o gerenciador de autenticação.
        
        Args:
            base_url: URL base da API
            username: Nome de usuário
            password: Senha
            timeout: Timeout para requisições em segundos
            logger: Logger customizado (opcional)
        """
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.timeout = timeout
        self.token: Optional[str] = None
        self.logger = logger or setup_logging()
    
    def authenticate(self) -> str:
        """
        Realiza autenticação e obtém token Bearer.
        
        Returns:
            Token de autenticação
            
        Raises:
            KobAuthenticationError: Se a autenticação falhar
            KobConnectionError: Se houver erro de conexão
        """
        endpoint = f"{self.base_url}/auth/login"
        payload = {
            "Usuario": self.username,
            "Senha": self.password
        }
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": "Bearer null"
        }
        
        self.logger.info(f"Autenticando usuário: {self.username}")
        
        try:
            response = requests.post(
                endpoint,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            
            # Verifica status code
            if response.status_code == 401:
                self.logger.error("Falha na autenticação: credenciais inválidas")
                raise KobAuthenticationError(
                    "Credenciais inválidas. Verifique usuário e senha.",
                    status_code=401
                )
            
            response.raise_for_status()
            
            # Extrai token da resposta
            response_data = response.json()
            
            if 'payload' not in response_data or 'token' not in response_data['payload']:
                self.logger.error("Resposta de autenticação não contém token")
                raise KobAuthenticationError(
                    "Resposta de autenticação inválida: token não encontrado"
                )
            
            self.token = response_data['payload']['token']
            self.logger.info("Autenticação realizada com sucesso")
            
            return self.token
            
        except requests.exceptions.Timeout as e:
            self.logger.error(f"Timeout na autenticação: {e}")
            raise KobConnectionError(
                f"Timeout ao conectar com a API (>{self.timeout}s)"
            ) from e
            
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Erro de conexão na autenticação: {e}")
            raise KobConnectionError(
                f"Não foi possível conectar à API: {self.base_url}"
            ) from e
            
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"Erro HTTP na autenticação: {e.response.status_code}")
            raise KobAuthenticationError(
                f"Erro HTTP {e.response.status_code}: {e.response.text}",
                status_code=e.response.status_code
            ) from e
            
        except (KeyError, TypeError, ValueError) as e:
            self.logger.error(f"Erro ao processar resposta de autenticação: {e}")
            raise KobAuthenticationError(
                "Erro ao processar resposta de autenticação"
            ) from e
    
    def get_token(self) -> str:
        """
        Obtém o token atual ou autentica se necessário.
        
        Returns:
            Token de autenticação
            
        Raises:
            KobAuthenticationError: Se não houver token e a autenticação falhar
        """
        if not self.token:
            self.logger.warning("Token não disponível, realizando autenticação")
            self.authenticate()
        
        return self.token
    
    def is_authenticated(self) -> bool:
        """
        Verifica se há um token de autenticação válido.
        
        Returns:
            True se autenticado, False caso contrário
        """
        return self.token is not None
    
    def clear_token(self):
        """Limpa o token de autenticação atual."""
        self.logger.info("Token de autenticação removido")
        self.token = None
    
    def get_auth_header(self) -> dict:
        """
        Obtém o header de autorização com o token.
        
        Returns:
            Dicionário com o header Authorization
            
        Raises:
            KobAuthenticationError: Se não houver token
        """
        token = self.get_token()
        return {"Authorization": f"Bearer {token}"}

