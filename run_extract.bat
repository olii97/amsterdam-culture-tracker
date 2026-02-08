@echo off
cd /d "%~dp0"
python extract_events.py >> extract_log.txt 2>&1
