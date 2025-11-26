# KOB CAR API Client

Cliente Python para consumo da API CAR (Contas a Receber) da plataforma KOB, uma solução completa para gestão de vendas e transações financeiras entre empresas.

## Descrição

Este projeto fornece uma interface Python completa e robusta para interagir com a API CAR do KOB, incluindo funcionalidades para gerenciamento de compradores, reservas de limite, vendas, evidências e recebíveis. O cliente implementa autenticação automática, tratamento de erros, validação de dados e persistência local.

## Funcionalidades

O cliente implementa todas as principais operações da API CAR:

- **Autenticação**: Gerenciamento automático de tokens Bearer com renovação
- **Gestão de Compradores**: Listagem e consulta de compradores vinculados ao vendedor
- **Gestão de Reservas de Limite**: Criação, consulta, cancelamento e estorno de reservas
- **Gestão de Vendas**: Criação, consulta e cancelamento de vendas
- **Manipulação de Evidências**: Upload de documentos comprobatórios de vendas
- **Acompanhamento de Recebíveis**: Consulta de parcelas e liquidações
- **Persistência de Dados**: Armazenamento local de dados em JSON, CSV e banco SQLite
- **Logging**: Sistema completo de logs para auditoria e debugging

## Estrutura do Projeto

```
kob-car-api/
├── src/
│   └── kob_car_api/
│       ├── __init__.py
│       ├── client.py          # Cliente principal da API
│       ├── auth.py             # Gerenciamento de autenticação
│       ├── exceptions.py       # Exceções customizadas
│       ├── validators.py       # Validadores de dados
│       ├── storage.py          # Persistência de dados
│       ├── common.py           # Operações Comuns
│       └── utils.py            # Funções utilitárias
├── data/                       # Dados persistidos
├── logs/                       # Arquivos de log
├── docs/                       # Documentação adicional
├── .env.example                # Exemplo de variáveis de ambiente
├── .gitignore
├── requirements.txt            # Dependências do projeto
├── setup.py                    # Configuração de instalação
└── README.md
```

## Instalação

### Pré-requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)

### Configuração do Ambiente Virtual

```bash

cd kob-car-api
python3 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
```

### Configuração de Variáveis de Ambiente

Copie o arquivo `.env.example` para `.env` e configure suas credenciais:

```env
KOB_API_USER=seu_usuario@empresa.com.br
KOB_API_PASSWORD=sua_senha_segura
KOB_API_BASE_URL=https://api.kob.tech
KOB_CNPJ_VENDEDOR=00000000000000
```

## Tratamento de Erros

O cliente implementa exceções customizadas para diferentes cenários:

```python
from kob_car_api import KobCARClient
from kob_car_api.exceptions import (
    KobAuthenticationError,
    KobAPIError,
    KobValidationError,
    KobNotFoundError
)

client = KobCARClient()

try:
    client.authenticate()
    compradores = client.get_compradores()
except KobAuthenticationError as e:
    print(f"Erro de autenticação: {e}")
except KobAPIError as e:
    print(f"Erro na API: {e.status_code} - {e.message}")
except KobValidationError as e:
    print(f"Erro de validação: {e}")
```

## Logging

O sistema de logging está configurado para registrar todas as operações:

```python
import logging
from kob_car_api import KobCARClient

logging.basicConfig(level=logging.INFO)
client = KobCARClient()

```
