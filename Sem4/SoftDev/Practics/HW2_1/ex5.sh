#!/bin/bash

directory="$1"

if [ -z "$directory" ]; then
    echo "Укажите директорию."
    exit 1
fi

if [ -d "$directory" ]; then
    echo "Объем диска, занимаемого директорией '$directory':"
    du -sh "$directory"
else
    echo "Директория '$directory' не существует."
fi

