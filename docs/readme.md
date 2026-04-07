# Monitoring Aggregator

This project assembles server data from several different servers like cpu utilization and ram usage and displays each server as a separate card on the same screen.

## Agent

The agent directory contains an agent.py file. This is what needs to be installed on every machine to link up to this system. It fetches all the stats from the machine using psutil, which works on mac, linux, and windows apparently.
The file for the cpu temp can only be found on mac and linux, however, so whenever the maching is a windows machine an install of the library "wmi" is needed on the windows machine. Wmi can fetch the cpu temp.

## Backend

The backend directory contains a main.py file. This will be the file to recover the data from the individual servers. Its task is to relay it to the frontend container cleanly.