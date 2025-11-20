# 🎯 Guia Rápido - Medindo Cobertura de Testes

## 📊 Comando Básico

Para rodar os testes e gerar relatório HTML de cobertura:

```bash
poetry run pytest tests/unit/controller/test_agent_controller.py \
    --cov=openhands/controller/agent_controller \
    --cov-report=html \
    --cov-report=term-missing
```

## 🌳 Para Cobertura de BRANCHES (decisões)

Adicione a flag `--cov-branch`:

```bash
poetry run pytest tests/unit/controller/test_agent_controller.py \
    --cov=openhands/controller/agent_controller \
    --cov-branch \
    --cov-report=html \
    --cov-report=term-missing
```

## 📁 Onde encontrar os relatórios

Após executar o comando, os relatórios serão salvos em:

- **Relatório HTML**: `htmlcov/index.html`
- **Relatório no terminal**: Aparece automaticamente após os testes

## 🔍 Visualizar o relatório HTML

### No terminal:
```bash
# Abrir no navegador padrão
xdg-open htmlcov/index.html

# Ou simplesmente navegue até:
firefox htmlcov/index.html
```

### Manualmente:
1. Navegue até a pasta: `/home/chrstphr/FCTE/Testes/OpenHands/htmlcov/`
2. Abra o arquivo `index.html` no seu navegador

## 📈 Interpretando os Resultados

### No Relatório HTML você verá:

1. **Statements (Stmts)**: Número total de linhas de código
2. **Miss**: Linhas não executadas pelos testes
3. **Cover**: Percentual de cobertura de linhas (%)
4. **Missing**: Quais linhas não foram testadas

### Com `--cov-branch` você verá TAMBÉM:

5. **Branch**: Número total de branches (decisões)
6. **BrPart**: Branches parcialmente cobertos
7. **Branch Cover**: Percentual de cobertura de branches (%)

## 🎯 Exemplo de Uso - Comparação Antes/Depois

### 1️⃣ Cobertura ANTES (sem seus testes MC/DC):

```bash
# Execute apenas os testes existentes (sem MC/DC)
poetry run pytest tests/unit/controller/test_agent_controller.py \
    --cov=openhands/controller/agent_controller \
    --cov-branch \
    --cov-report=html:htmlcov_antes \
    --cov-report=term-missing
```

Resultado salvo em: `htmlcov_antes/index.html`

### 2️⃣ Adicione seus testes MC/DC ao arquivo

Copie seus 27 casos de teste para dentro de `test_agent_controller.py`

### 3️⃣ Cobertura DEPOIS (com testes MC/DC):

```bash
# Execute com seus testes incluídos
poetry run pytest tests/unit/controller/test_agent_controller.py \
    --cov=openhands/controller/agent_controller \
    --cov-branch \
    --cov-report=html:htmlcov_depois \
    --cov-report=term-missing
```

Resultado salvo em: `htmlcov_depois/index.html`

### 4️⃣ Compare os resultados:

Abra os dois arquivos HTML lado a lado:
- `htmlcov_antes/index.html`
- `htmlcov_depois/index.html`

Você verá o aumento em:
- **Line Coverage** (cobertura de linhas)
- **Branch Coverage** (cobertura de decisões) ⭐ **MAIS IMPORTANTE para MC/DC**

## 🎓 Para seu Relatório Acadêmico

Você deve reportar:

1. **Cobertura de Linhas (%)**: Antes e Depois
2. **Cobertura de Branches (%)**: Antes e Depois ⭐
3. **Linhas das decisões testadas**:
   - 926-938 (Context Window)
   - 951-956 (Action Type)
   - 983-984 (Security)
   - 995-996 (Confirmation)

## 🔧 Comandos Úteis Adicionais

### Ver apenas um resumo rápido:
```bash
poetry run pytest tests/unit/controller/test_agent_controller.py \
    --cov=openhands/controller/agent_controller \
    --cov-report=term
```

### Gerar relatório XML (para CI/CD):
```bash
poetry run pytest tests/unit/controller/test_agent_controller.py \
    --cov=openhands/controller/agent_controller \
    --cov-report=xml
```

### Ver linhas específicas não cobertas:
```bash
poetry run pytest tests/unit/controller/test_agent_controller.py \
    --cov=openhands/controller/agent_controller \
    --cov-report=term-missing
```

## ✅ Checklist de Validação

- [ ] Executei os testes sem MC/DC
- [ ] Salvei o relatório HTML "antes"
- [ ] Adicionei meus 27 testes MC/DC
- [ ] Executei os testes com MC/DC
- [ ] Salvei o relatório HTML "depois"
- [ ] Comparei as porcentagens de cobertura
- [ ] Documentei os resultados no relatório acadêmico

## 📊 Exemplo de Resultado Esperado

```
Nome: agent_controller.py
Stmts   : 500
Miss    : 100 → 50 (melhorou!)
Cover   : 80% → 90% (melhorou!)
Branch  : 150
BrPart  : 30 → 10 (melhorou!)
Branch% : 80% → 93% (melhorou!)
```

---

**Dica**: A cobertura de **branches** é mais importante para MC/DC do que a cobertura de linhas!
