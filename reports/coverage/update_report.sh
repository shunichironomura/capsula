#!/bin/bash

set -Cue -o pipefail

project_root="$(dirname "$(dirname "$(dirname "$0")")")"
echo "Project root: \"$(realpath $project_root)\""

pushd "$project_root"
  echo "Running coverage report update..."
  poetry run coverage erase
  poetry run coverage run -m pytest tests/
  poetry run coverage xml -o reports/coverage/coverage.xml
  poetry run coverage html -d reports/coverage/html
  poetry run genbadge coverage -i reports/coverage/coverage.xml -o reports/coverage/coverage-badge.svg
popd
