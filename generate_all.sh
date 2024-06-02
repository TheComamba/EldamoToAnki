#!/bin/bash

python3 generate.py --language Khuzdul
echo
python3 generate.py --language Quenya --neo-words
echo
python3 generate.py --language Quenya
echo
python3 generate.py --language Sindarin --neo-words
echo
python3 generate.py --language Sindarin
