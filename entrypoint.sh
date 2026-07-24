#!/bin/bash
set -e

mkdir -p /tmp/pd_render

# Pd (vanilla) non ha un oggetto per il timestamp di orologio: i "print" in
# main.pd (pd_render_start/stop/done, vedi fase DSP) escono su stdout senza
# orario. Li prefissiamo qui con la data di sistema cosi' finiscono nello
# stesso log stream, timestampato, di bot.py -- niente da cambiare nel
# patch Pd stesso. Uso "process substitution" (> >(...)), non una pipe con
# subshell, cosi' $! resta il PID di pd stesso e "kill $PD_PID" alla fine
# continua a funzionare come prima.
#
# -path: i pacchetti Debian pd-osc/pd-mrpeach-net installano gli oggetti in
# sottocartelle (/usr/lib/pd/extra/osc, /usr/lib/pd/extra/mrpeach/net) che
# Pd non cerca di default (cerca solo <dir>/<nome>.pd_linux e
# <dir>/<nome>/<nome>.pd_linux, mai una sottocartella con nome diverso
# dall'oggetto) -- verificato con "pd -verbose", causava "couldn't create"
# su udpreceive/unpackOSC/routeOSC/pipelist e quindi nessuna sintesi. "-lib"
# non è l'alternativa giusta: non esiste un binario libreria unico
# mrpeach.pd_linux/OSC.pd_linux da caricare, ogni oggetto e' un .pd_linux
# separato.
pd -nogui -noaudio \
    -path /usr/lib/pd/extra/osc -path /usr/lib/pd/extra/mrpeach/net \
    -send "; pd dsp 1" main.pd \
    > >(while IFS= read -r line; do
            printf '%s PD: %s\n' "$(date '+%Y-%m-%d %H:%M:%S.%3N')" "$line"
        done) 2>&1 &
PD_PID=$!

python bot.py

kill $PD_PID
