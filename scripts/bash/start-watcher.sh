#!/usr/bin/env bash

set -e

# Recherche de la racine du projet
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$REPO_ROOT"

echo "🚀 Démarrage du Watcher de spécifications (specs/*.md)..."
python3 scripts/python/spec_watcher.py