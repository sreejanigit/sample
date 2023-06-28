#!/bin/bash

export LOG_FILE="/tmp/script-log.txt"

SEPERATOR="******************************************************************************"

export_to_env() {
    echo "export $1=$2" >> ~/env.sh
    source ~/env.sh
}

log_text() {
 
    echo "$SEPERATOR"
    echo -e "\033[44;1;37m[$1]\033[0m - \033[1m $2 \033[0m"
    echo "$SEPERATOR"
}

print_error() {

    echo "$SEPERATOR"
    echo -e "\033[41;1m Error: Script failed - $0\033[0m"
    echo " Failed Command - $@"
    echo " Output: $(tail -n 7 /tmp/script-log.txt | head -n 1)"
    echo " cat /tmp/script-log.txt for Detailed Logs"
    echo "$SEPERATOR"
}
