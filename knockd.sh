#!/bin/bash

CHANNEL="knockd"
IPSET_LIST="KNOCK"

# Create IPSET list if it doesn't exist
ipset create $IPSET_LIST hash:ip timeout 1800 -exist

# Function to validate IPv4 addresses
is_valid_ipv4() {
    local IP=$1
    local RES=1

    if [[ $IP =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        IFS='.' read -r -a OCTETS <<< "$IP"
        [[ ${OCTETS[0]} -le 255 && ${OCTETS[1]} -le 255 && ${OCTETS[2]} -le 255 && ${OCTETS[3]} -le 255 ]]
        RES=$?
    fi

    return $RES
}


redis-cli --csv subscribe $CHANNEL | while read LINE; do
    if [[ $LINE == *"message"* ]]; then
        IP=$(echo $LINE | awk -F',' '{print $3}' | tr -d '"')
        if is_valid_ipv4 $IP; then
            ipset add $IPSET_LIST $IP -exist
            echo "Added $IP to $IPSET_LIST"
        else
            echo "ignore $LINE"
        fi
    fi
done
