#! /bin/bash

bash clean.sh
python setup.py sdist -v
bash clean.sh
