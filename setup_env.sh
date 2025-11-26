
echo "========================================="
echo "KOB CAR API Client - Configuração"
echo "========================================="
echo ""

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado. Por favor, instale Python 3.8 ou superior."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "✓ Python encontrado: $PYTHON_VERSION"

echo ""
echo "Criando ambiente virtual..."
python3 -m venv venv

if [ $? -eq 0 ]; then
    echo "✓ Ambiente virtual criado com sucesso"
else
    echo "❌ Erro ao criar ambiente virtual"
    exit 1
fi

echo ""
echo "Ativando ambiente virtual..."
source venv/bin/activate

echo ""
echo "Atualizando pip..."
pip install --upgrade pip > /dev/null 2>&1

echo ""
echo "Instalando dependências..."
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✓ Dependências instaladas com sucesso"
else
    echo "❌ Erro ao instalar dependências"
    exit 1
fi

echo ""
if [ ! -f .env ]; then
    echo "⚠️  Arquivo .env não encontrado"
    echo "Copiando .env.example para .env..."
    cp .env.example .env
    echo "✓ Arquivo .env criado"
    echo ""
    echo "⚠️  IMPORTANTE: Edite o arquivo .env com suas credenciais antes de usar o cliente!"
else
    echo "✓ Arquivo .env encontrado"
fi
mkdir -p data logs

echo ""
echo "========================================="
echo "✓ Configuração concluída com sucesso!"
echo "========================================="
echo ""
echo "Para começar a usar:"
echo "  1. Ative o ambiente virtual: source venv/bin/activate"
echo "  2. Configure suas credenciais no arquivo .env"
echo "  3. Execute um exemplo: python examples/basic_usage.py"
echo ""
