#!/bin/bash

set -euo pipefail

declare -r VENV_DIR=./venv
declare -r REQUIREMENTS_SRC=requirements_src.txt
declare -r REQUIREMENTS=requirements.txt

function show_help() {
    echo "Tool for venv environment"
    echo "Use: ./venv.sh COMMAND"
    echo "Available commands:"
    echo "  help - show this help"
    echo "  create - create a venv environment"
    echo "  update - update a venv environment"
    echo "  remove - remove a venv environment"
    echo "  shell - start shell with a venv environment"
    echo "  requirements - create a requirements.txt file"
}

function update_venv() {
    local packages=""
    local name=""
    while read -r name
    do
        packages="$packages $name"
    done < "$REQUIREMENTS_SRC"
    source ./venv/bin/activate
    pip install -U pip
    pip install -U $packages
}

function create_venv() {
    python3 -mvenv "$VENV_DIR"
    update_venv
}

function remove_venv() {
    rm -r "$VENV_DIR"
}

function shell_venv() {
    source "$VENV_DIR"/bin/activate
    echo "Your are in venv environment. Use command exit for exit."
    bash
}

function create_requirements() {
    source "$VENV_DIR"/bin/activate
    pip freeze > "$REQUIREMENTS"
}

if [[ $# != 0  ]]
then
    command=$1
else
    command=help
fi

case "$command" in
    help) show_help;;
    shell) shell_venv;;
    create) create_venv;;
    update) update_venv;;
    remove) remove_venv;;
    requirements) create_requirements;;
    *) show_help;;
esac

