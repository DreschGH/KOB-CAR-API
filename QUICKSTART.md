# Guia de Início Rápido - KOB CAR API Client

Este guia fornece instruções passo a passo para você começar a usar o cliente Python da API KOB CAR em poucos minutos.

## Pré-requisitos

Antes de começar, certifique-se de ter instalado:

- **Python 3.8 ou superior**: Verifique com `python3 --version`
- **pip**: Gerenciador de pacotes Python (geralmente vem com Python)
- **Credenciais da API KOB**: Usuário, senha e CNPJ do vendedor

## Passo 1: Configurar o Ambiente Virtual

Navegue até o diretório do projeto e crie um ambiente virtual Python:

```bash
cd kob-car-api
python3 -m venv venv
```

Ative o ambiente virtual:

**No Linux/macOS:**
```bash
source venv/bin/activate
```

**No Windows:**
```cmd
venv\Scripts\activate
```

Você verá `(venv)` no início do prompt, indicando que o ambiente virtual está ativo.

## Passo 2: Instalar as Dependências

Com o ambiente virtual ativo, instale todas as dependências necessárias:

```bash
pip install -r requirements.txt
```

Ou instale o pacote em modo de desenvolvimento:

```bash
pip install -e .
```

## Passo 3: Configurar as Variáveis de Ambiente

Copie o arquivo de exemplo `.env.example` para `.env`:

```bash
cp .env.example .env
```

Edite o arquivo `.env` com suas credenciais reais:

```env
KOB_API_USER=seu_usuario@empresa.com.br
KOB_API_PASSWORD=sua_senha_segura
KOB_API_BASE_URL=https://api.kob.tech
KOB_CNPJ_VENDEDOR=00000000000000
```

**Importante:** Nunca compartilhe ou faça commit do arquivo `.env` com credenciais reais!

## Passo 4: Testar a Conexão

Crie um arquivo de teste simples `test_connection.py`:

```python
from kob_car_api import KobCARClient

client = KobCARClient(auto_authenticate=True)

compradores = client.get_compradores()
print(f"Total de compradores: {len(compradores)}")

if compradores:
    primeiro = compradores[0]
    nome = primeiro.get('pessoaJuridica', {}).get('nomeFantasia', 'N/A')
    print(f"Primeiro comprador: {nome}")
```

Execute o script:

```bash
python test_connection.py
```

Se tudo estiver configurado corretamente, você verá a quantidade de compradores e o nome do primeiro comprador.

## Solução de Problemas

### Erro de Autenticação
Se você receber um erro `KobAuthenticationError`:
- Verifique se o usuário e senha no `.env` estão corretos
- Confirme que sua conta tem acesso à API CAR

### Erro de Configuração
Se você receber um erro `KobConfigurationError`:
- Certifique-se de que o arquivo `.env` existe no diretório raiz do projeto
- Verifique se todas as variáveis obrigatórias estão preenchidas

### Erro de Conexão
Se você receber um erro `KobConnectionError`:
- Verifique sua conexão com a internet
- Confirme que a URL da API está correta (`https://api.kob.tech`)
- Verifique se não há firewall bloqueando a conexão

