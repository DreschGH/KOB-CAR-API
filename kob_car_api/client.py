"""
Cliente principal para a API KOB CAR (Contas a Receber).
"""

import os
import logging
from typing import Any, Dict, List, Optional
from decimal import Decimal
from datetime import date, timedelta

import requests
from dotenv import load_dotenv

from .auth import AuthManager
from .exceptions import (
    KobAPIError,
    KobAuthorizationError,
    KobConnectionError,
    KobNotFoundError,
    KobTimeoutError,
    KobValidationError,
    KobConfigurationError
)
from .validators import Validators
from .utils import setup_logging


class KobCARClient:
    """Cliente para interação com a API KOB CAR."""
    
    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        base_url: Optional[str] = None,
        cnpj_vendedor: Optional[str] = None,
        timeout: int = 30,
        log_level: str = "INFO",
        auto_authenticate: bool = False
    ):
        """
        Inicializa o cliente da API KOB CAR.
        
        Args:
            username: Usuário da API (ou carrega de KOB_API_USER)
            password: Senha da API (ou carrega de KOB_API_PASSWORD)
            base_url: URL base da API (ou carrega de KOB_API_BASE_URL)
            cnpj_vendedor: CNPJ do vendedor (ou carrega de KOB_CNPJ_VENDEDOR)
            timeout: Timeout para requisições em segundos
            log_level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            auto_authenticate: Se True, autentica automaticamente na inicialização
        
        Raises:
            KobConfigurationError: Se as credenciais não forem fornecidas
        """
        
        load_dotenv()
        
        
        self.username = username or os.getenv('KOB_API_USER')
        self.password = password or os.getenv('KOB_API_PASSWORD')
        self.base_url = (base_url or os.getenv('KOB_API_BASE_URL', 'https://api.kob.tech')).rstrip('/')
        self.cnpj_vendedor = cnpj_vendedor or os.getenv('KOB_CNPJ_VENDEDOR')
        self.timeout = timeout
        
        
        if not self.username or not self.password:
            raise KobConfigurationError(
                "Credenciais não fornecidas. Configure KOB_API_USER e KOB_API_PASSWORD "
                "no arquivo .env ou passe como parâmetros."
            )
        
        
        self.logger = setup_logging(log_level=log_level)
        

        self.auth_manager = AuthManager(
            base_url=self.base_url,
            username=self.username,
            password=self.password,
            timeout=self.timeout,
            logger=self.logger
        )
        

        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "KOB-CAR-Python-Client/1.0.0"
        })
        

        if auto_authenticate:
            self.authenticate()
        
        self.logger.info("Cliente KOB CAR inicializado")
    
    def authenticate(self):
        """Realiza autenticação na API."""
        self.auth_manager.authenticate()
        self.session.headers.update(self.auth_manager.get_auth_header())
    
    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        **kwargs
    ) -> Optional[Dict]:
        """
        Realiza uma requisição HTTP para a API.
        
        Args:
            method: Método HTTP (GET, POST, DELETE, etc.)
            endpoint: Endpoint da API (sem a URL base)
            params: Parâmetros de query string
            json_data: Dados JSON para enviar no body
            **kwargs: Argumentos adicionais para requests
            
        Returns:
            Resposta JSON da API ou None se não houver conteúdo
            
        Raises:
            KobAuthenticationError: Se não estiver autenticado
            KobAuthorizationError: Se não tiver permissão
            KobNotFoundError: Se o recurso não for encontrado
            KobValidationError: Se houver erro de validação (422)
            KobAPIError: Para outros erros da API
            KobConnectionError: Se houver erro de conexão
            KobTimeoutError: Se houver timeout
        """

        if not self.auth_manager.is_authenticated():
            self.logger.info("Não autenticado, realizando autenticação automática")
            self.authenticate()
        
        url = f"https://bff.kob.tech{endpoint}"
        
        self.logger.debug(f"{method.upper()} {endpoint}")
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                timeout=self.timeout,
                **kwargs
            )
            

            if response.status_code == 401:
                self.logger.warning("Token expirado ou inválido, re-autenticando")
                self.auth_manager.clear_token()
                self.authenticate()

                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_data,
                    timeout=self.timeout,
                    **kwargs
                )
            
            if response.status_code == 403:
                raise KobAuthorizationError(
                    "Acesso negado. Usuário não tem permissão para acessar este recurso.",
                    status_code=403
                )
            
            if response.status_code == 404:
                raise KobNotFoundError(
                    "Recurso não encontrado.",
                    status_code=404
                )
            
            if response.status_code == 422:
                error_data = response.json() if response.text else {}
                raise KobValidationError(
                    error_data.get('mensagem', 'Erro de validação'),
                    status_code=422,
                    payload=error_data.get('payload', {})
                )
            
            response.raise_for_status()
            

            if response.text:
                return response.json()
            
            return None
            
        except requests.exceptions.Timeout as e:
            self.logger.error(f"Timeout na requisição: {e}")
            raise KobTimeoutError(
                f"Timeout ao fazer requisição (>{self.timeout}s)"
            ) from e
            
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Erro de conexão: {e}")
            raise KobConnectionError(
                f"Erro ao conectar com a API: {self.base_url}"
            ) from e
            
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"Erro HTTP {e.response.status_code}: {e.response.text}")
            

            try:
                error_data = e.response.json()
                message = error_data.get('mensagem', str(e))
                payload = error_data.get('payload', {})
            except:
                message = str(e)
                payload = {}
            
            raise KobAPIError(
                message,
                status_code=e.response.status_code,
                payload=payload
            ) from e
    
    def get_compradores(
        self,
        cnpj_vendedor: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict]:
        """
        Lista compradores associados a um vendedor.
        
        Args:
            cnpj_vendedor: CNPJ do vendedor (usa o padrão se não fornecido)
            status: Filtro de status (opcional)
            
        Returns:
            Lista de compradores
        """
        cnpj = cnpj_vendedor or self.cnpj_vendedor
        if not cnpj:
            raise KobConfigurationError("CNPJ do vendedor não configurado")
        
        cnpj = Validators.validate_cnpj(cnpj)
        
        endpoint = f"/contasareceber/{cnpj}/compradores"
        params = {}
        
        if status:
            params['status'] = status
        
        self.logger.info(f"Listando compradores para vendedor {cnpj}")
        return self._request('GET', endpoint, params=params) or []
    
    def get_detalhes_comprador(
        self,
        cnpj_comprador: str,
        cnpj_vendedor: Optional[str] = None
    ) -> Dict:
        """
        Consulta detalhes de um comprador específico.
        
        Args:
            cnpj_comprador: CNPJ do comprador
            cnpj_vendedor: CNPJ do vendedor (usa o padrão se não fornecido)
            
        Returns:
            Detalhes do comprador
        """
        cnpj_vend = cnpj_vendedor or self.cnpj_vendedor
        if not cnpj_vend:
            raise KobConfigurationError("CNPJ do vendedor não configurado")
        
        cnpj_vend = Validators.validate_cnpj(cnpj_vend)
        cnpj_comp = Validators.validate_cnpj(cnpj_comprador)
        
        endpoint = f"/contasareceber/{cnpj_vend}/compradores/{cnpj_comp}"
        
        self.logger.info(f"Consultando detalhes do comprador {cnpj_comp}")
        return self._request('GET', endpoint)
    
    def criar_reserva(
        self,
        data: Dict,
        cnpj_vendedor: Optional[str] = None
    ) -> Dict:
        """
        Cria uma nova reserva de limite.
        
        Args:
            data: Dados da reserva (referenciaConciliacao, descricao, valorBase, 
                  percentualMajoracaoValorBase, cnpjComprador, codigoCondicaoPagamento)
            cnpj_vendedor: CNPJ do vendedor (usa o padrão se não fornecido)
            
        Returns:
            Dados da reserva criada
        """
        cnpj = cnpj_vendedor or self.cnpj_vendedor
        if not cnpj:
            raise KobConfigurationError("CNPJ do vendedor não configurado")
        
        cnpj = Validators.validate_cnpj(cnpj)
        

        validated_data = Validators.validate_reserva_data(data)
        
        endpoint = f"/contasareceber/{cnpj}/reservas"
        
        self.logger.info(f"Criando reserva para comprador {validated_data['cnpjComprador']}")
        return self._request('POST', endpoint, json_data=validated_data)
    
    def consultar_reserva(
        self,
        id_reserva: int,
        cnpj_vendedor: Optional[str] = None
    ) -> Dict:
        """
        Consulta detalhes de uma reserva de limite.
        
        Args:
            id_reserva: ID da reserva
            cnpj_vendedor: CNPJ do vendedor (usa o padrão se não fornecido)
            
        Returns:
            Detalhes da reserva
        """
        cnpj = cnpj_vendedor or self.cnpj_vendedor
        if not cnpj:
            raise KobConfigurationError("CNPJ do vendedor não configurado")
        
        cnpj = Validators.validate_cnpj(cnpj)
        
        endpoint = f"/contasareceber/{cnpj}/reservas/{id_reserva}"
        
        self.logger.info(f"Consultando reserva {id_reserva}")
        return self._request('GET', endpoint)
    
    def consultar_reservas(
        self,
        data_inicial: Optional[str] = None,
        data_final: Optional[str] = None,
        cnpj_vendedor: Optional[str] = None
    ) -> Dict:
        """
        Consulta detalhes de uma venda.
        
        Args:
            id_kob: ID da venda no sistema KOB
            cnpj_vendedor: CNPJ do vendedor (usa o padrão se não fornecido)
            
        Returns:
            Detalhes da venda
        """
        cnpj = cnpj_vendedor or self.cnpj_vendedor
        if not cnpj:
            raise KobConfigurationError("CNPJ do vendedor não configurado")
        
        cnpj = Validators.validate_cnpj(cnpj)

        dataFim=data_final or date.today().strftime('%Y-%m-%d')
        dataInicio = data_inicial or (date.today() -timedelta(60)).strftime('%Y-%m-%d')
        params = {}
        if dataInicio and dataFim:
            Validators.validate_date_range(dataInicio, dataFim)
            params['dataInicio'] = dataInicio
            params['dataFim'] = dataFim
        
        endpoint = f"/contasareceber/public/{cnpj}/reservas"
        
        self.logger.info(f"Consultando Reservas")
        return self._request('GET', endpoint, params=params)

    def cancelar_reserva(
        self,
        id_reserva: int,
        cnpj_vendedor: Optional[str] = None
    ) -> None:
        """
        Cancela uma reserva de limite.
        
        Args:
            id_reserva: ID da reserva
            cnpj_vendedor: CNPJ do vendedor (usa o padrão se não fornecido)
        """
        cnpj = cnpj_vendedor or self.cnpj_vendedor
        if not cnpj:
            raise KobConfigurationError("CNPJ do vendedor não configurado")
        
        cnpj = Validators.validate_cnpj(cnpj)
        
        endpoint = f"/contasareceber/{cnpj}/reservas/{id_reserva}"
        
        self.logger.info(f"Cancelando reserva {id_reserva}")
        self._request('DELETE', endpoint)
    
    def estornar_saldo_reserva(
        self,
        id_reserva: int,
        valor: Decimal,
        descricao: str,
        cnpj_vendedor: Optional[str] = None
    ) -> Dict:
        """
        Estorna saldo de uma reserva de limite.
        
        Args:
            id_reserva: ID da reserva
            valor: Valor a ser estornado
            descricao: Descrição do estorno
            cnpj_vendedor: CNPJ do vendedor (usa o padrão se não fornecido)
            
        Returns:
            Dados do estorno criado
        """
        cnpj = cnpj_vendedor or self.cnpj_vendedor
        if not cnpj:
            raise KobConfigurationError("CNPJ do vendedor não configurado")
        
        cnpj = Validators.validate_cnpj(cnpj)
        valor_validado = Validators.validate_decimal(valor, "valor")
        
        endpoint = f"/contasareceber/{cnpj}/reservas/{id_reserva}/estornos"
        
        data = {
            "valor": float(valor_validado),
            "descricao": descricao
        }
        
        self.logger.info(f"Estornando R$ {valor_validado} da reserva {id_reserva}")
        return self._request('POST', endpoint, json_data=data)
    
    def consultar_estornos_reserva(
        self,
        id_reserva: int,
        cnpj_vendedor: Optional[str] = None
    ) -> List[Dict]:
        """
        Consulta estornos de uma reserva de limite.
        
        Args:
            id_reserva: ID da reserva
            cnpj_vendedor: CNPJ do vendedor (usa o padrão se não fornecido)
            
        Returns:
            Lista de estornos
        """
        cnpj = cnpj_vendedor or self.cnpj_vendedor
        if not cnpj:
            raise KobConfigurationError("CNPJ do vendedor não configurado")
        
        cnpj = Validators.validate_cnpj(cnpj)
        
        endpoint = f"/contasareceber/{cnpj}/reservas/{id_reserva}/estornos"
        
        self.logger.info(f"Consultando estornos da reserva {id_reserva}")
        return self._request('GET', endpoint) or []
   
    def criar_venda(
        self,
        data: Dict,
        cnpj_vendedor: Optional[str] = None
    ) -> Dict:
        """
        Cria uma nova venda.
        
        Args:
            data: Dados da venda
            cnpj_vendedor: CNPJ do vendedor (usa o padrão se não fornecido)
            
        Returns:
            Dados da venda criada
        """
        cnpj = cnpj_vendedor or self.cnpj_vendedor
        if not cnpj:
            raise KobConfigurationError("CNPJ do vendedor não configurado")
        
        cnpj = Validators.validate_cnpj(cnpj)
        
        endpoint = f"/contasareceber/{cnpj}/vendas"
        
        self.logger.info("Criando nova venda")
        return self._request('POST', endpoint, json_data=data)
    
    def consultar_venda(
        self,
        id_kob: str,
        cnpj_vendedor: Optional[str] = None
    ) -> Dict:
        """
        Consulta detalhes de uma venda.
        
        Args:
            id_kob: ID da venda no sistema KOB
            cnpj_vendedor: CNPJ do vendedor (usa o padrão se não fornecido)
            
        Returns:
            Detalhes da venda
        """
        cnpj = cnpj_vendedor or self.cnpj_vendedor
        if not cnpj:
            raise KobConfigurationError("CNPJ do vendedor não configurado")
        
        cnpj = Validators.validate_cnpj(cnpj)
        
        endpoint = f"/contasareceber/{cnpj}/vendas/{id_kob}"
        
        self.logger.info(f"Consultando venda {id_kob}")
        return self._request('GET', endpoint)

    def consultar_vendas(
        self,
        data_inicial: Optional[str] = None,
        data_final: Optional[str] = None,
        cnpj_vendedor: Optional[str] = None
    ) -> Dict:
        """
        Consulta detalhes de uma venda.
        
        Args:
            id_kob: ID da venda no sistema KOB
            cnpj_vendedor: CNPJ do vendedor (usa o padrão se não fornecido)
            
        Returns:
            Detalhes da venda
        """
        cnpj = cnpj_vendedor or self.cnpj_vendedor
        if not cnpj:
            raise KobConfigurationError("CNPJ do vendedor não configurado")
        
        cnpj = Validators.validate_cnpj(cnpj)
        dataFim=data_final or date.today().strftime('%Y-%m-%d')
        dataInicio = data_inicial or (date.today() -timedelta(60)).strftime('%Y-%m-%d')
        params = {}
        if dataInicio and dataFim:
            Validators.validate_date_range(dataInicio, dataFim)
            params['dataInicio'] = dataInicio
            params['dataFim'] = dataFim
        
        endpoint = f"/contasareceber/{cnpj}/vendas"
        
        self.logger.info(f"Consultando vendas")
        return self._request('GET', endpoint, params=params)
    
    def cancelar_venda(
        self,
        id_kob: str,
        cnpj_vendedor: Optional[str] = None
    ) -> None:
        """
        Cancela uma venda.
        
        Args:
            id_kob: ID da venda no sistema KOB
            cnpj_vendedor: CNPJ do vendedor (usa o padrão se não fornecido)
        """
        cnpj = cnpj_vendedor or self.cnpj_vendedor
        if not cnpj:
            raise KobConfigurationError("CNPJ do vendedor não configurado")
        
        cnpj = Validators.validate_cnpj(cnpj)
        
        endpoint = f"/contasareceber/{cnpj}/vendas/{id_kob}"
        
        self.logger.info(f"Cancelando venda {id_kob}")
        self._request('DELETE', endpoint)
    
    def enviar_evidencias(
        self,
        id_kob: str,
        evidencias: List[Dict],
        cnpj_vendedor: Optional[str] = None
    ) -> Dict:
        """
        Envia evidências para uma venda.
        
        Args:
            id_kob: ID da venda no sistema KOB
            evidencias: Lista de evidências
            cnpj_vendedor: CNPJ do vendedor (usa o padrão se não fornecido)
            
        Returns:
            Confirmação do envio
        """
        cnpj = cnpj_vendedor or self.cnpj_vendedor
        if not cnpj:
            raise KobConfigurationError("CNPJ do vendedor não configurado")
        
        cnpj = Validators.validate_cnpj(cnpj)
        
        endpoint = f"/contasareceber/{cnpj}/vendas/{id_kob}/evidencias"
        
        self.logger.info(f"Enviando evidências para venda {id_kob}")
        return self._request('POST', endpoint, json_data={"evidencias": evidencias})
    
    def listar_recebiveis(
        self,
        cnpj_vendedor: Optional[str] = None,
        data_inicio: Optional[str] = None,
        data_fim: Optional[str] = None
    ) -> List[Dict]:
        """
        Lista recebíveis do vendedor.
        
        Args:
            cnpj_vendedor: CNPJ do vendedor (usa o padrão se não fornecido)
            data_inicio: Data inicial (ISO-8601)
            data_fim: Data final (ISO-8601)
            
        Returns:
            Lista de recebíveis
        """
        cnpj = cnpj_vendedor or self.cnpj_vendedor
        if not cnpj:
            raise KobConfigurationError("CNPJ do vendedor não configurado")
        
        cnpj = Validators.validate_cnpj(cnpj)
        
        params = {}
        if data_inicio and data_fim:
            Validators.validate_date_range(data_inicio, data_fim)
            params['dataInicio'] = data_inicio
            params['dataFim'] = data_fim
        
        endpoint = f"/contasareceber/{cnpj}/recebiveis"
        
        self.logger.info("Listando recebíveis")
        return self._request('GET', endpoint, params=params) or []
    
    def listar_liquidacoes(
        self,
        cnpj_vendedor: Optional[str] = None,
        data_inicio: Optional[str] = None,
        data_fim: Optional[str] = None
    ) -> List[Dict]:
        """
        Lista liquidações do vendedor.
        
        Args:
            cnpj_vendedor: CNPJ do vendedor (usa o padrão se não fornecido)
            data_inicio: Data inicial (ISO-8601)
            data_fim: Data final (ISO-8601)
            
        Returns:
            Lista de liquidações
        """
        cnpj = cnpj_vendedor or self.cnpj_vendedor
        if not cnpj:
            raise KobConfigurationError("CNPJ do vendedor não configurado")
        
        cnpj = Validators.validate_cnpj(cnpj)
        
        params = {}
        if data_inicio and data_fim:
            Validators.validate_date_range(data_inicio, data_fim)
            params['dataInicio'] = data_inicio
            params['dataFim'] = data_fim
        
        endpoint = f"/contasareceber/{cnpj}/liquidacoes"
        
        self.logger.info("Listando liquidações")
        return self._request('GET', endpoint, params=params) or []

