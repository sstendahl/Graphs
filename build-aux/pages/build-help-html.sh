#!/usr/bin/env bash

mkdir -p public/help/C
yelp-build html help/C/* -o public/help/C

while read lang; do
    msgfmt help/$lang/$lang.po -o help/$lang/graphs-$lang.gmo
    itstool -m help/$lang/graphs-$lang.gmo --lang $lang -o help/$lang help/C/*.page help/C/legal.xml
    mkdir -p public/help/$lang
    yelp-build html help/$lang/* -o public/help/$lang
done < help/LINGUAS

cp help/LINGUAS public/help
cp build-aux/pages/help-index.html public/help/index.html