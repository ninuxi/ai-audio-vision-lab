#!/bin/bash
set -e

mkdir -p /tmp/pd_render

pd -nogui -noaudio -send "; pd dsp 1" main.pd &
PD_PID=$!

python bot.py

kill $PD_PID
