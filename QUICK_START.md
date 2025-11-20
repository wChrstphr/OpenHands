# ⚡ Início Rápido - Rodar Testes

## 🚀 TL;DR (Muito Longo, Não Li)

```bash
# Instalar
poetry install

# Rodar todos os testes
poetry run pytest

# Rodar com verbosidade
poetry run pytest -v

# Rodar com cobertura
poetry run pytest --cov=openhands/controller/agent_controller
```

## 📍 Localização Atual

Você está em: `/home/chrstphr/FCTE/Testes/OpenHands`

## ✅ Status Atual

```
✅ 77 testes passando
⏭️  1 teste pulado
```

## 🎯 Comandos Mais Usados

### Rodar testes do AgentController

```bash
poetry run pytest tests/unit/controller/test_agent_controller.py -v
```

### Rodar apenas testes com "step" no nome

```bash
poetry run pytest -k "step" -v
```

### Rodar e gerar relatório HTML

```bash
poetry run pytest tests/unit/controller/ \
    --cov=openhands/controller/agent_controller \
    --cov-report=html
```

### Rodar com output mais legível

```bash
poetry run pytest tests/unit/controller/ -v --tb=short -s
```

---

📖 **Para mais detalhes**, veja `COMO_RODAR_TESTES.md`
