# Documentação Técnica - KOB CAR API Client

## 1. Visão Geral

Este documento fornece uma visão técnica detalhada do **KOB CAR API Client**, um pacote Python projetado para facilitar a integração com a API de Contas a Receber (CAR) da KOB. Ele abstrai a complexidade das requisições HTTP, autenticação, validação e persistência de dados, oferecendo uma interface limpa e orientada a objetos.

## 2. Arquitetura do Projeto

A arquitetura foi projetada para ser modular e extensível. Os principais componentes estão localizados em `src/kob_car_api`.

```
kob-car-api/
└── src/
    └── kob_car_api/
        ├── __init__.py       # Expõe a interface pública do pacote
        ├── client.py         # O coração do cliente, orquestra as operações
        ├── auth.py           # Gerencia o ciclo de vida da autenticação e tokens
        ├── storage.py        # Módulos para persistência e processamento de dados
        ├── validators.py     # Funções para validação de dados de entrada
        ├── exceptions.py     # Hierarquia de exceções customizadas
        └── utils.py          # Funções auxiliares e de formatação
```

### 2.1. `client.py` - `KobCARClient`

É a classe principal e o ponto de entrada para todas as interações com a API. Suas responsabilidades incluem:

- **Configuração**: Carrega as credenciais e configurações a partir de variáveis de ambiente (`.env`) ou parâmetros no construtor.
- **Orquestração da Autenticação**: Utiliza o `AuthManager` para obter e renovar tokens de acesso.
- **Gerenciamento de Sessão**: Mantém uma `requests.Session` para reutilizar conexões e headers.
- **Interface de Endpoints**: Expõe métodos Python para cada endpoint da API CAR (ex: `get_compradores`, `criar_reserva`).
- **Tratamento de Requisições**: Encapsula a lógica de requisição no método `_request`, que lida com a construção de URLs, tratamento de timeouts, erros de conexão e renovação automática de token em caso de expiração (status 401).

### 2.2. `auth.py` - `AuthManager`

Classe dedicada exclusivamente ao processo de autenticação.

- **Obtenção de Token**: Implementa a chamada ao endpoint `/auth/login` para obter o Bearer Token.
- **Armazenamento de Token**: Mantém o token em memória para ser usado nas requisições subsequentes.
- **Ciclo de Vida**: Gerencia o estado de autenticação (autenticado ou não) e fornece o header de autorização.

### 2.3. `storage.py` - `DataStorage` e `DataProcessor`

Este módulo fornece ferramentas para ingestão, tratamento e gestão dos dados recebidos da API.

- **`DataStorage`**: Oferece métodos para salvar dados em múltiplos formatos:
    - `save_json()`: Salva dados em arquivos JSON.
    - `save_csv()`: Converte e salva dados em formato CSV, com achatamento opcional de dicionários aninhados.
    - `save_excel()`: Salva múltiplos conjuntos de dados em abas de um mesmo arquivo Excel.
    - `save_to_database()`: Persiste dados em um banco de dados SQLite usando `pandas` e `SQLAlchemy`.
- **`DataProcessor`**: Contém lógica para análise e transformação dos dados.
    - `aggregate_compradores()`: Calcula estatísticas sobre a lista de compradores.
    - `aggregate_recebiveis()`: Calcula estatísticas sobre a lista de recebíveis.
    - `filter_by_date_range()`: Filtra uma lista de registros por um campo de data.

### 2.4. `validators.py` - `Validators`

Uma classe com métodos estáticos para validar e sanitizar dados antes de enviá-los para a API. Isso previne erros `422 Unprocessable Entity` e garante a integridade dos dados.

- `validate_cnpj()`: Garante que o CNPJ tenha 14 dígitos numéricos.
- `validate_decimal()`: Converte e valida valores monetários.
- `validate_reserva_data()`: Valida um dicionário completo para a criação de uma reserva, verificando todos os campos obrigatórios e seus tipos.

### 2.5. `exceptions.py`

Define uma hierarquia de exceções customizadas para um tratamento de erros mais granular e informativo.

- `KobAPIException`: Exceção base.
- `KobAuthenticationError`: Para falhas no login (credenciais erradas).
- `KobAuthorizationError`: Para erros de permissão (status 403).
- `KobNotFoundError`: Para recursos não encontrados (status 404).
- `KobValidationError`: Para erros de validação de dados (status 422).


### 2.6. `common.py`

WIP Define as operações comuns dos procedimentos internos do AR 

## 3. Fluxo de uma Requisição

1.  O usuário instancia `client = KobCARClient()`.
2.  O cliente carrega as configurações do `.env`.
3.  O usuário chama um método, por exemplo, `client.get_compradores()`.
4.  O método `get_compradores` chama o método interno `_request()`.
5.  O `_request()` verifica se o cliente está autenticado usando `auth_manager.is_authenticated()`.
6.  Se não estiver, ele chama `self.authenticate()`, que por sua vez invoca `auth_manager.authenticate()`.
7.  O `AuthManager` faz a requisição `POST /auth/login`, obtém o token e o armazena.
8.  O `_request()` atualiza os headers da sessão com o novo token.
9.  A requisição original (`GET /contasareceber/{cnpj}/compradores`) é finalmente executada.
10. A resposta é analisada. Se for um erro conhecido (401, 403, 404, 422), uma exceção específica é lançada. Outros erros HTTP lançam `KobAPIError`.
11. Se a resposta for bem-sucedida (status 2xx), o corpo JSON é retornado como um dicionário ou lista de dicionários.

## 4. Gerenciamento de Dependências e Ambiente

- **Ambiente Virtual**: O uso de `venv` é fortemente recomendado para isolar as dependências do projeto.
- **`requirements.txt`**: Lista todas as dependências necessárias para produção e desenvolvimento.
- **`.env`**: Arquivo para armazenar credenciais e configurações de forma segura, mantido fora do controle de versão (via `.gitignore`).
- **`setup.py`**: Permite que o projeto seja instalado como um pacote Python (`pip install .`), facilitando sua reutilização em outros projetos.

## Exemplos de Uso
Pendente

