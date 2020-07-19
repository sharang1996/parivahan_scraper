#!/usr/bin/env bash

gunicorn3 --bind 0.0.0.0:5000 app:APP & disown
