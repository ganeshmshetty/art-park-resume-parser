#!/usr/bin/env bash
set -euo pipefail

mkdir -p data/onet data/catalog

if [[ -d "data/db_30_1_text" ]]; then
	python3 scripts/build_onet_skills.py
else
	echo "O*NET text dump not found at data/db_30_1_text"
	echo "Place O*NET files there, then run: python3 scripts/build_onet_skills.py"
fi

echo "Place generated course catalog JSON in data/catalog."
