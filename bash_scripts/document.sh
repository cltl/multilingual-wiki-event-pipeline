#!/usr/bin/env bash

cd ..
pyreverse classes.py
dot -Tpdf classes.dot -o documentation/classes.pdf
rm classes.dot
