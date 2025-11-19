#!/bin/bash


echo "Установка python3, pip, git..."
sudo apt install python3 pip git

echo "Клонирование проекта..."
git clone https://github.com/divanov11/Django-To-Do-list-with-user-authentication.git
cd Django-To-Do-list-with-user-authentication

echo "Создание виртуального окружения..."
python3 -m venv ./.venv
source .venv/bin/activate

echo "Указание зависимостей..."
touch requirements.txt
echo "Django~=5.1.6" >> requirements.txt
echo "dotenv" >> requirements.txt

echo "Установка зависимостей..."
pip install -r requirements.txt

echo "Запуск сервера..."
python3 manage.py migrate
python3 manage.py makemigrations
python3 manage.py runserver

