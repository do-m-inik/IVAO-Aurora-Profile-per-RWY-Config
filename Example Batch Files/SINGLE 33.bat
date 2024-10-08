@echo off
cd C:\Users\<USERNAME>\<PATH TO>\IVAO-Aurora-Profile-per-RWY-Config\program
python program.py --rwyconfig "33-23" --configfile "config.txt"
start /d "C:\Aurora" Aurora.exe
