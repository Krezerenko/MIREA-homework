#!/bin/bash

for file in ./*
do
    if [ -d "$file" ]; then
        echo "$file директория"
    elif [ -f "$file" ]; then
        echo "$file файл"
    fi
done

