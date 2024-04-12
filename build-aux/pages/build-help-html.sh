#!/usr/bin/env bash

mkdir -p public/help/C
yelp-build html help/C/* -o public/help/C

while read lang; do
    mkdir -p public/help/$lang
    yelp-build html help/$lang/* -o public/help/$lang
done < help/LINGUAS

cp help/LINGUAS public/help
cp build-aux/pages/help-index.html public/help/index.html