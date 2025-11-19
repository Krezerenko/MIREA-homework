#!/bin/bash

directory="$1"

if [ -z "$directory" ]; then
    echo "Укажите путь."
    exit 1
fi

if [ -d "$directory" ]; then
    for file in $directory/*
    do
        if [ -x "$file" ]; then
            echo "$file исполняемый"
        fi
    done
else
    echo "Директории '$directory' не существует."
fi

