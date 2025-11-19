#!/bin/bash

file="$1"

if [[ -z "$file" ]]; then
    echo "Укажите файл."
    exit 1
fi

if [ -f "$file" ]; then
    IFS=
    while read -r line; do
        echo "$line"
    done < $file

else
    echo "Файла '$file' не существует."
fi
