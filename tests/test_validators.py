"""
Testes unitários para o módulo de validadores.
"""

import pytest
from decimal import Decimal
from kob_car_api.validators import Validators
from kob_car_api.exceptions import KobValidationError


class TestValidators:
    """Testes para a classe Validators."""
    
    def test_validate_cnpj_valid(self):
        """Testa validação de CNPJ válido."""
        # CNPJ sem formatação
        result = Validators.validate_cnpj("12345678000199")
        assert result == "12345678000199"
        
        # CNPJ com formatação
        result = Validators.validate_cnpj("12.345.678/0001-99")
        assert result == "12345678000199"
    
    def test_validate_cnpj_invalid_length(self):
        """Testa validação de CNPJ com tamanho inválido."""
        with pytest.raises(KobValidationError):
            Validators.validate_cnpj("123456")
    
    def test_validate_cnpj_empty(self):
        """Testa validação de CNPJ vazio."""
        with pytest.raises(KobValidationError):
            Validators.validate_cnpj("")
    
    def test_validate_decimal_valid(self):
        """Testa validação de decimal válido."""
        result = Validators.validate_decimal("100.50")
        assert result == Decimal("100.50")
        
        result = Validators.validate_decimal(100.50)
        assert result == Decimal("100.50")
    
    def test_validate_decimal_negative(self):
        """Testa validação de decimal negativo."""
        with pytest.raises(KobValidationError):
            Validators.validate_decimal("-10.50")
    
    def test_validate_percentage_valid(self):
        """Testa validação de percentual válido."""
        result = Validators.validate_percentage("50.5")
        assert result == Decimal("50.5")
    
    def test_validate_percentage_out_of_range(self):
        """Testa validação de percentual fora do intervalo."""
        with pytest.raises(KobValidationError):
            Validators.validate_percentage("150")
    
    def test_validate_reserva_data_valid(self):
        """Testa validação de dados de reserva válidos."""
        data = {
            "referenciaConciliacao": "REF-001",
            "descricao": "Teste",
            "valorBase": "1000.00",
            "percentualMajoracaoValorBase": "10.0",
            "cnpjComprador": "12345678000199",
            "codigoCondicaoPagamento": "30DD"
        }
        
        result = Validators.validate_reserva_data(data)
        assert result["valorBase"] == 1000.00
        assert result["cnpjComprador"] == "12345678000199"
    
    def test_validate_reserva_data_missing_field(self):
        """Testa validação de dados de reserva com campo faltando."""
        data = {
            "referenciaConciliacao": "REF-001",
            # descricao está faltando
            "valorBase": "1000.00",
            "percentualMajoracaoValorBase": "10.0",
            "cnpjComprador": "12345678000199",
            "codigoCondicaoPagamento": "30DD"
        }
        
        with pytest.raises(KobValidationError):
            Validators.validate_reserva_data(data)
