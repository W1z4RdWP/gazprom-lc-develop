#!/bin/bash

set -e

echo "Обновляем списки пакетов..."
sudo apt update

echo "Устанавливаем необходимые зависимости для добавления репозиториев..."
sudo apt install -y software-properties-common

echo "Добавляем PPA с Python 3.12..."
sudo add-apt-repository -y ppa:deadsnakes/ppa

echo "Обновляем списки пакетов после добавления PPA..."
sudo apt update

echo "Устанавливаем Python 3.12 и pip..."
sudo apt install -y python3.12 python3.12-venv python3.12-dev python3-pip

echo "Обновляем pip для Python 3.12..."
python3.12 -m pip install --upgrade pip

echo "Проверяем установленную версию Python 3.12..."
python3.12 --version

echo "Установка Python 3.12 завершена."