#!/bin/bash

data_file="1data.txt"

current_date="$(date "+%Y.%m.%d %H:%M:%S")"

> "$data_file"
echo "Дата и время: $current_date" >> "$data_file"
echo "Пользователи: $(who)" >> "$data_file"
echo "Время с последнего запуска: $(uptime -p)" >> "$data_file"

cat "$data_file"
