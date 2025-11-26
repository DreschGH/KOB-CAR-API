"""
Validadores de dados para a API KOB CAR.
"""

import re
from decimal import Decimal, InvalidOperation
from typing import Any, Optional
from datetime import datetime

from .exceptions import KobValidationError


class Validators:
    """Classe com métodos estáticos para validação de dados."""
    
    @staticmethod
    def validate_cnpj(cnpj: str) -> str:
        """
        Valida e formata um CNPJ.
        
        Args:
            cnpj: CNPJ a ser validado (com ou sem formatação)
            
        Returns:
            CNPJ sem formatação (apenas números)
            
        Raises:
            KobValidationError: Se o CNPJ for inválido
        """
        if not cnpj:
            raise KobValidationError("CNPJ não pode ser vazio")
        

        cnpj_clean = re.sub(r'[^0-9]', '', cnpj)
        

        if len(cnpj_clean) != 14:
            raise KobValidationError(
                f"CNPJ deve conter 14 dígitos. Recebido: {len(cnpj_clean)} dígitos"
            )
        
        return cnpj_clean
    
    @staticmethod
    def validate_cpf(cpf: str) -> str:
        """
        Valida e formata um CPF.
        
        Args:
            cpf: CPF a ser validado (com ou sem formatação)
            
        Returns:
            CPF sem formatação (apenas números)
            
        Raises:
            KobValidationError: Se o CPF for inválido
        """
        if not cpf:
            raise KobValidationError("CPF não pode ser vazio")
        

        cpf_clean = re.sub(r'[^0-9]', '', cpf)
        

        if len(cpf_clean) != 11:
            raise KobValidationError(
                f"CPF deve conter 11 dígitos. Recebido: {len(cpf_clean)} dígitos"
            )
        
        return cpf_clean
    
    @staticmethod
    def validate_decimal(value: Any, field_name: str = "valor") -> Decimal:
        """
        Valida e converte um valor para Decimal.
        
        Args:
            value: Valor a ser validado
            field_name: Nome do campo (para mensagens de erro)
            
        Returns:
            Valor como Decimal
            
        Raises:
            KobValidationError: Se o valor for inválido
        """
        if value is None:
            raise KobValidationError(f"{field_name} não pode ser nulo")
        
        try:
            decimal_value = Decimal(str(value))
            

            if decimal_value < 0:
                raise KobValidationError(f"{field_name} não pode ser negativo")
            
            return decimal_value
            
        except (InvalidOperation, ValueError) as e:
            raise KobValidationError(
                f"{field_name} inválido: {value}. Deve ser um número válido."
            ) from e
    
    @staticmethod
    def validate_percentage(value: Any, field_name: str = "percentual") -> Decimal:
        """
        Valida um valor percentual.
        
        Args:
            value: Valor percentual a ser validado
            field_name: Nome do campo (para mensagens de erro)
            
        Returns:
            Valor como Decimal
            
        Raises:
            KobValidationError: Se o valor for inválido
        """
        decimal_value = Validators.validate_decimal(value, field_name)
        
        if decimal_value < 0 or decimal_value > 100:
            raise KobValidationError(
                f"{field_name} deve estar entre 0 e 100. Recebido: {decimal_value}"
            )
        
        return decimal_value
    
    @staticmethod
    def validate_required_string(value: Optional[str], field_name: str) -> str:
        """
        Valida que uma string obrigatória não está vazia.
        
        Args:
            value: Valor a ser validado
            field_name: Nome do campo (para mensagens de erro)
            
        Returns:
            String validada
            
        Raises:
            KobValidationError: Se o valor for vazio ou nulo
        """
        if not value or not value.strip():
            raise KobValidationError(f"{field_name} é obrigatório e não pode ser vazio")
        
        return value.strip()
    
    @staticmethod
    def validate_date_range(start_date: str, end_date: str, max_days: int = 60) -> tuple:
        """
        Valida um intervalo de datas.
        
        Args:
            start_date: Data inicial (ISO-8601)
            end_date: Data final (ISO-8601)
            max_days: Número máximo de dias permitido no intervalo
            
        Returns:
            Tupla com as datas validadas
            
        Raises:
            KobValidationError: Se o intervalo for inválido
        """
        try:
            start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        except ValueError as e:
            raise KobValidationError(
                f"Formato de data inválido. Use ISO-8601 (YYYY-MM-DD ou YYYY-MM-DDTHH:MM:SS)"
            ) from e
        
        if start > end:
            raise KobValidationError("Data inicial não pode ser posterior à data final")
        
        delta = (end - start).days
        if delta > max_days:
            raise KobValidationError(
                f"Intervalo de datas não pode exceder {max_days} dias. Intervalo atual: {delta} dias"
            )
        
        return (start_date, end_date)
    
    @staticmethod
    def validate_reserva_data(data: dict) -> dict:
        """
        Valida dados para criação de uma reserva de limite.
        
        Args:
            data: Dicionário com dados da reserva
            
        Returns:
            Dicionário validado
            
        Raises:
            KobValidationError: Se os dados forem inválidos
        """
        validated = {}
        

        validated['referenciaConciliacao'] = Validators.validate_required_string(
            data.get('referenciaConciliacao'), 'referenciaConciliacao'
        )
        
        validated['descricao'] = Validators.validate_required_string(
            data.get('descricao'), 'descricao'
        )
        
        validated['valorBase'] = float(Validators.validate_decimal(
            data.get('valorBase'), 'valorBase'
        ))
        

        if validated['valorBase'] <= 0:
            raise KobValidationError("valorBase deve ser maior que zero")
        
        validated['percentualMajoracaoValorBase'] = float(Validators.validate_percentage(
            data.get('percentualMajoracaoValorBase', 0), 'percentualMajoracaoValorBase'
        ))
        
        validated['cnpjComprador'] = Validators.validate_cnpj(
            data.get('cnpjComprador')
        )
        
        validated['codigoCondicaoPagamento'] = Validators.validate_required_string(
            data.get('codigoCondicaoPagamento'), 'codigoCondicaoPagamento'
        )
        
        return validated
    
    @staticmethod
    def validate_venda_data(data: dict) -> dict:
        """
        Valida dados para criação de uma venda.
        
        Args:
            data: Dicionário com dados da venda
            
        Returns:
            Dicionário validado
            
        Raises:
            KobValidationError: Se os dados forem inválidos
        """
        validated = {}
        


        
        return validated

