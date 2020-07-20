#!/usr/bin/env bash

nohup gunicorn3 --bind 0.0.0.0:5000 app:APP &
