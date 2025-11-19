#!/bin/bash

function search()
{
    file="$1"
    if [[ -d "$file" ]]; then
        for file_ in "$file"/*
        do
            search "$file_"
        done
        return
    fi
    if [[ "$file" != *.py ]]; then
        return
    fi
    
    result="$result"$'\n'"$(grep -E "^.*import.*$" "$file" | sed -E "s/^from (.*) import.*$/\1/g" | sed -E "s/^import //g" | sed -E "s/^([^\.]+)\..*$/\1/g" | sed -E "s/^\..*$//g")"
}

search "$1"
libs="$(echo "$result" | sort -u | tail -n +4)"
while IFS= read -r lib;
do
    grep -q "$lib" < builtin_libs.txt
    if ! grep -q "$lib" < "builtin_libs.txt"; then
        echo "$lib"
    fi 
done <<< "$libs"
