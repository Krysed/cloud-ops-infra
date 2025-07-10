#!/usr/bin/env bash

set -euo pipefail

venv_directory=".venv"
install_scripts_path="$(pwd)/install_scripts"

linux_deps=("pip" "pipx" "curl" "jq" "python3" "uvicorn" "docker" "terraform" "kubectl" "minikube")
install_command="sudo apt-get install -y"

function install_tech () 
{   
    com="$1 --version"
    if [[ "$1" == "kubectl" ]]; then
        com="kubectl version --client"
    fi
    if ! $com &> /dev/null; then
        echo "$1 could not be found, installing.."
        install_script="${install_scripts_path}/install_${1}.sh"

        if [[ -f $install_script ]];then
            "${install_scripts_path}/install_${1}.sh"
        else
            echo "Attempting install using package manager."
            "$install_command $1"
        fi
        if [[ $? -eq 0 ]];then
            echo "$1 has been installed successfully."
        else
            echo "Failed to install $1."
        fi
    else
        echo "$1 already installed."
    fi
}

function setup_venv ()
{
    if [[ ! -d $venv_directory ]]; then
        echo "Setting up Python venv"
        python3 -m venv "$venv_directory"
    else
        echo "Python venv already exists, skipping."
    fi
}

function check_and_move_dir ()
{
    if [[ ! -d $1 ]];then
        mv "$2" "$1"
    fi
}

if [[ $0 -ne "" ]];then
    echo "Start the script by running source ./setup.sh"
    exit 0
fi
for elem in "${linux_deps[@]}"; do
    install_tech "${elem}"
done

setup_venv

wget https://www.tooplate.com/zip-templates/2136_kool_form_pack.zip
unzip 2136_kool_form_pack.zip
rm 2136_kool_form_pack.zip

check_and_move_dir "$(pwd)/frontend/static/images/" "2136_kool_form_pack/images/"
check_and_move_dir "$(pwd)/frontend/static/videos/" "2136_kool_form_pack/videos/"
check_and_move_dir "$(pwd)/frontend/static/fonts/" "2136_kool_form_pack/fonts/"
rm -rf 2136_kool_form_pack/
