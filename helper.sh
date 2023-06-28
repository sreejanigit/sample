#!/bin/bash

source ./utils.sh 

exec 2>> "${LOG_FILE}"

set -ex

START_TIME=$(date +%s)

trap 'print_error $BASH_COMMAND' ERR

trap 'END_TIME=$(date +%s); SECONDS=$(($END_TIME - $START_TIME)); mins=$((SECONDS / 60)); secs=$((SECONDS % 60)); log_text "Script execution time: ${mins}m ${secs}s - $0"' EXIT
