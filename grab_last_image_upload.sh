#!/bin/bash

# Images sent via IPhone Airdrop to Downloads folder
last_image_file=$(ls -tr ~/Downloads/IMG* | tail -1)
open -g ${last_image_file}

read -p 'Tool Name: ' tool_name 
filename="${tool_name}.jpg"
src_filepath="images/src/${filename}"
cp ${last_image_file} ${src_filepath}

/usr/local/bin/python3 tool_trace.py convert ${src_filepath}
kill $(pgrep -nx  Preview)
