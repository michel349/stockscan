@echo off
start python app.py
timeout /t 4 /nobreak >nul
start http://localhost:5000
