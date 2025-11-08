#!/bin/bash

# Обновление списка пакетов
sudo apt update

# Установка необходимых пакетов для работы с репозиториями через HTTPS
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common

# Добавление GPG-ключа официального репозитория Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -

# Добавление репозитория Docker в список источников apt
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"

# Обновление списка пакетов после добавления нового репозитория
sudo apt update

# Установка Docker Engine
sudo apt install -y docker-ce

# Запуск и добавление Docker в автозагрузку
sudo systemctl start docker
sudo systemctl enable docker

# Добавление текущего пользователя в группу docker для работы без sudo
sudo usermod -aG docker $USER

# Вывод установленной версии Docker для проверки
docker --version

echo "Docker успешно установлен. Чтобы изменения вступили в силу, перезайдите в систему или выполните: newgrp docker"