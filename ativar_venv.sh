#!/bin/bash
# Ativa o venv e entra em src/ num novo shell.
# Uso: ./ativar_venv.sh
# Saia com Ctrl+D ou "exit" para voltar ao shell original.

cd "$(dirname "$0")/src" || { echo "Pasta src/ nao encontrada"; exit 1; }
source ../venv/bin/activate || { echo "Venv nao encontrado. Crie com: python3 -m venv venv && pip install -r requirements.txt"; exit 1; }

echo ""
echo "Venv ativo. Voce esta em src/"
echo ""
echo "Comandos uteis:"
echo "  python Run.py                     # Executa o sistema completo (voltar uma pasta)"
echo "  python Servidor.py                # Apenas o servidor central"
echo "  python DispositivoSemaforo.py     # Apenas um semaforo (standalone)"
echo "  python Cruzamento.py              # Apenas o cruzamento (2 semaforos)"
echo "  python Ambulancia.py              # Apenas a ambulancia"
echo ""
echo "Para sair do venv: exit"
echo ""
exec bash -i
