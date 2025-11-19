#!/bin/bash

directory=$1

if [ -z "$directory" ]; then
    echo "Укажите путь к каталогу."
    exit 1
fi

if [ -d "$directory" ]; then
    ls -l "$directory"
else
    echo "Каталога '$directory' не существует."
fi

