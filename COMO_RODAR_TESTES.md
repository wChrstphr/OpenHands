# 🧪 Guia Completo - Como Rodar Testes no OpenHands

## 📋 Pré-requisitos

Certifique-se de que você tem:
- ✅ Python 3.12+ instalado
- ✅ Poetry instalado (`pip install poetry`)
- ✅ Dependências do projeto instaladas

## 🚀 Instalação Inicial

```bash
# 1. Navegar até a pasta do projeto
cd /home/chrstphr/FCTE/Testes/OpenHands

# 2. Instalar dependências
poetry install

# 3. Ativar o ambiente virtual (opcional, poetry já faz isso)
poetry shell
```

---

## 🎯 Comandos Básicos para Rodar Testes

### 1️⃣ Rodar TODOS os testes

```bash
poetry run pytest
```

**Output esperado:**
```
collected XXX items
............................. [ XX%]
======================== XXX passed in XXXs =========================
```

### 2️⃣ Rodar testes de um diretório específico

```bash
# Testes do controller (sua principal classe)
poetry run pytest tests/unit/controller/

# Testes de um arquivo específico
poetry run pytest tests/unit/controller/test_agent_controller.py

# Testes de uma classe específica
poetry run pytest tests/unit/controller/test_agent_controller.py::TestAgentController

# Testes de um método específico
poetry run pytest tests/unit/controller/test_agent_controller.py::test_set_agent_state
```

### 3️⃣ Rodar com verbosidade (mais detalhado)

```bash
# Mostrar nome completo de cada teste
poetry run pytest tests/unit/controller/ -v

# Mostrar ainda mais detalhes
poetry run pytest tests/unit/controller/ -vv

# Mostrar saída do teste (print statements)
poetry run pytest tests/unit/controller/ -s
```

---

## 🔍 Filtros Úteis

### Por nome do teste

```bash
# Rodar apenas testes que contêm "step" no nome
poetry run pytest -k "step" -v

# Rodar testes que contêm "step" mas NÃO contêm "budget"
poetry run pytest -k "step and not budget" -v

# Exemplos práticos para AgentController
poetry run pytest -k "agent_controller" -v
poetry run pytest -k "run_controller" -v
poetry run pytest -k "context_window" -v
```

### Por marcadores

```bash
# Se os testes têm marcadores @pytest.mark.asyncio
poetry run pytest -m asyncio

# Pular testes marcados como skip
poetry run pytest --co -q  # List all tests
```

---

## 📊 Análise de Cobertura

### Gerar relatório de cobertura de linhas

```bash
poetry run pytest tests/unit/controller/ \
    --cov=openhands/controller/agent_controller \
    --cov-report=term-missing
```

**Output mostra:**
```
Name                                Stmts   Miss  Cover   Missing
-------------------------------------------------------------------
openhands/controller/agent_controller.py   504   382    24%    ...
```

### Gerar relatório de cobertura com branches (decisões)

```bash
poetry run pytest tests/unit/controller/ \
    --cov=openhands/controller/agent_controller \
    --cov-branch \
    --cov-report=term-missing
```

### Gerar relatório HTML

```bash
poetry run pytest tests/unit/controller/ \
    --cov=openhands/controller/agent_controller \
    --cov-report=html \
    --cov-report=term

# Depois abrir em navegador
# open htmlcov/index.html  (macOS)
# xdg-open htmlcov/index.html  (Linux)
# start htmlcov/index.html  (Windows)
```

---

## ⏱️ Performance - Rodar Testes Mais Rápido

### Usar paralelização (mais threads)

```bash
# Usar 4 workers em paralelo
poetry run pytest -n 4

# Usar numero de CPUs do sistema
poetry run pytest -n auto
```

**Nota:** Pode precisar instalar `pytest-xdist`:
```bash
poetry add --group dev pytest-xdist
```

### Rodar apenas testes que falharam

```bash
# Primeira rodada marca quais falharam
poetry run pytest tests/unit/controller/

# Próxima rodada roda apenas os que falharam
poetry run pytest tests/unit/controller/ --lf

# Ou rodar falhas + uma amostra dos que passaram
poetry run pytest tests/unit/controller/ --ff
```

### Parar no primeiro erro

```bash
# Parar assim que um teste falha
poetry run pytest -x

# Parar após N falhas
poetry run pytest --maxfail=3
```

---

## 🧹 Limpeza de Cache

Se estiver tendo problemas, limpe o cache:

```bash
# Remove cache do pytest
rm -rf .pytest_cache

# Remove cache do Python
find . -type d -name __pycache__ -exec rm -rf {} +

# Remove arquivos compilados
find . -name "*.pyc" -delete

# Depois rode os testes novamente
poetry run pytest tests/unit/controller/ -v
```

---

## 🎓 Comandos Para Seu Trabalho Acadêmico

### Rodar testes MC/DC (seus 27 testes)

```bash
# Assumindo que você adicionou os testes a test_agent_controller.py
poetry run pytest tests/unit/controller/test_agent_controller.py \
    -k "ct01 or ct02 or ct03 or ct04 or ct05 or ct06 or ct07 or ct08 or ct09 or ct10" \
    -v

# Ou mais simples: rodar todos
poetry run pytest tests/unit/controller/test_agent_controller.py -v
```

### Gerar relatório completo para o trabalho

```bash
# Testes + Cobertura + HTML
poetry run pytest tests/unit/controller/test_agent_controller.py \
    -v \
    --cov=openhands/controller/agent_controller \
    --cov-branch \
    --cov-report=html \
    --cov-report=term-missing \
    -s 2>&1 | tee test_results.txt

# Depois você tem:
# - test_results.txt (saída dos testes)
# - htmlcov/index.html (relatório visual)
```

### Rodar apenas testes de integração

```bash
# Testes que realmente executam o código (não apenas mocks)
poetry run pytest -k "run_controller or context_window" -v
```

---

## ✅ Checklist - Antes de Submeter seu Trabalho

```bash
# 1. Limpar cache
rm -rf .pytest_cache __pycache__

# 2. Instalar dependências (caso algo tenha mudado)
poetry install

# 3. Rodar TODOS os testes (check se não quebrou nada)
poetry run pytest tests/unit/controller/ -v

# 4. Verificar cobertura dos seus testes MC/DC
poetry run pytest tests/unit/controller/test_agent_controller.py \
    --cov=openhands/controller/agent_controller \
    --cov-report=term-missing -v

# 5. Gerar documentação final
poetry run pytest tests/unit/controller/test_agent_controller.py \
    -v \
    -s 2>&1 | tee results_final.txt
```

---

## 🐛 Troubleshooting

### Erro: "Module not found"

```bash
# Solução: Instalar dependências
poetry install
poetry shell
```

### Erro: "pytest not found"

```bash
# Solução: Usar poetry run
poetry run pytest  # Sempre use "poetry run pytest"
```

### Erro: "Port already in use"

Alguns testes podem usar portas. Feche outras aplicações ou:

```bash
# Kill processes on port 8000
lsof -i :8000 | grep -v PID | awk '{print $2}' | xargs kill -9
```

### Testes muito lentos

```bash
# Usar paralelização
poetry run pytest -n auto

# Ou pular testes lentos (se marcados)
poetry run pytest -m "not slow"
```

---

## 📈 Exemplo Prático - Seu Caso

Para seus **27 testes MC/DC**, use:

```bash
# 1. Rodar todos os testes do controller (baseline)
poetry run pytest tests/unit/controller/ -v --tb=short 2>&1 | tee baseline.txt

# 2. Se adicionar seus testes ao arquivo existente:
poetry run pytest tests/unit/controller/test_agent_controller.py -v \
    --cov=openhands/controller/agent_controller \
    --cov-report=term-missing 2>&1 | tee results_com_mcdc.txt

# 3. Comparar diferenças
diff baseline.txt results_com_mcdc.txt | head -20
```

---

## 🎯 Resumo Rápido

| Comando | Descrição |
|---------|-----------|
| `poetry run pytest` | Rodar todos os testes |
| `poetry run pytest -v` | Rodar com verbose |
| `poetry run pytest -k "pattern"` | Filtrar por padrão |
| `poetry run pytest --cov=module` | Com cobertura |
| `poetry run pytest -x` | Parar no primeiro erro |
| `poetry run pytest -n auto` | Paralelizar |
| `poetry run pytest -s` | Mostrar prints |
| `poetry run pytest --tb=short` | Output menor |

---

Pronto! Agora você sabe rodar os testes do projeto OpenHands! 🚀
