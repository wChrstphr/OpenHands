#!/bin/bash

# Script para comparar cobertura antes e depois dos testes MC/DC

echo "=================================================="
echo "  ANÁLISE DE COBERTURA - AgentController._step()  "
echo "=================================================="
echo ""

# 1. Cobertura SEM os testes MC/DC (apenas testes existentes)
echo "1️⃣  Executando testes EXISTENTES (sem MC/DC)..."
echo "   Arquivo: test_agent_controller.py"
echo ""

poetry run pytest tests/unit/controller/test_agent_controller.py \
    --cov=openhands/controller/agent_controller \
    --cov-report=term \
    --cov-report=html:htmlcov_before \
    -q 2>&1 | grep -E "TOTAL|agent_controller.py|passed|failed"

echo ""
echo "📊 Relatório HTML salvo em: htmlcov_before/index.html"
echo ""

# 2. Cobertura COM os testes MC/DC
echo "=================================================="
echo "2️⃣  Executando testes COM MC/DC..."
echo "   Arquivo: test_agent_controller_step.py"
echo ""

poetry run pytest tests/unit/controller/test_agent_controller_step.py \
    --cov=openhands/controller/agent_controller \
    --cov-report=term \
    --cov-report=html:htmlcov_after \
    -q 2>&1 | grep -E "TOTAL|agent_controller.py|passed|failed"

echo ""
echo "📊 Relatório HTML salvo em: htmlcov_after/index.html"
echo ""

# 3. Cobertura COM TODOS os testes (existentes + MC/DC)
echo "=================================================="
echo "3️⃣  Executando TODOS os testes (existentes + MC/DC)..."
echo ""

poetry run pytest \
    tests/unit/controller/test_agent_controller.py \
    tests/unit/controller/test_agent_controller_step.py \
    --cov=openhands/controller/agent_controller \
    --cov-report=term \
    --cov-report=html:htmlcov_combined \
    -q 2>&1 | grep -E "TOTAL|agent_controller.py|passed|failed"

echo ""
echo "📊 Relatório HTML salvo em: htmlcov_combined/index.html"
echo ""

# 4. Resumo das linhas específicas do método _step()
echo "=================================================="
echo "📈 RESUMO - Linhas do método _step():"
echo "=================================================="
echo ""
echo "Decisões testadas:"
echo "  • Linhas 926-938: Detecção de erro de contexto (10 testes)"
echo "  • Linhas 951-956: Verificação de tipo de ação (7 testes)"
echo "  • Linhas 983-984: Lógica de confirmação (5 testes)"
echo "  • Linhas 995-996: Aguardando confirmação (3 testes)"
echo ""
echo "Total de casos de teste MC/DC: 25 + 2 integração = 27 testes"
echo ""
echo "=================================================="
echo "✅ Análise completa! Abra os arquivos HTML para visualização detalhada:"
echo ""
echo "   Antes (sem MC/DC):  file://$(pwd)/htmlcov_before/index.html"
echo "   Depois (MC/DC):     file://$(pwd)/htmlcov_after/index.html"
echo "   Combinado (todos):  file://$(pwd)/htmlcov_combined/index.html"
echo "=================================================="
