#!/bin/sh

DIR="$(dirname "$(readlink -f "$0")")"
cd $DIR

if [ $# -eq 1 ]
    then
        if [ $1 = "start" ] || [ $1 = "stop" ] || [ $1 = "restart" ]
            then
                source/server_nms.py $1
            else
                echo "Unknown command $1"
                echo "Usage: $0 start|stop|restart"
        fi
    else
        echo "Running as non-daemon. To run as daemon execute as:"
        echo "$0 start|stop|restart"
        source/server_nms.py
fi
