#!/bin/bash

python3 generate.py Khuzdul
echo
python3 generate.py Quenya --neo-words
echo
python3 generate.py Quenya
echo
python3 generate.py Sindarin --neo-words
echo
python3 generate.py Sindarin
