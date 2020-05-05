#!/bin/bash
echo "Moving to folder"
# Move to the correct directory
cd /usr/src/bpscboi/

echo "Installing requirements"
# Install requirements
pip3 install -r requirements.txt

echo "Starting the discord bot"
# Start the discord bot
python3 -u ./BigPineyScheduleBot.py