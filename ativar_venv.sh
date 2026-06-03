#!/bin/bash
# Ativa o venv e entra em src/ num novo shell.
# Uso: ./ativar_venv.sh
# Saia com Ctrl+D ou "exit" para voltar ao shell original.

cd "$(dirname "$0")/src" || { echo "Pasta src/ não encontrada"; exit 1; }
source ../venv/bin/activate || { echo "Venv não encontrado. Crie com: python3 -m venv venv && pip install -r requirements.txt"; exit 1; }

echo "Venv ativo. Você está em src/"
echo "Para sair: exit"
exec bash -i
