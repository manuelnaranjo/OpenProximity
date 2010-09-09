#! /bin/bash

bash clean.sh
python setup.py bdist_egg
bash clean.sh
