@echo off
echo Backend baslatiliyor...
start cmd /k "uvicorn backend:app --reload"

echo HTTP server baslatiliyor...
start cmd /k "python -m http.server 8080"

echo Tarayici aciliyor...
start "" "http://127.0.0.1:8080/home_page.html"

echo Tum servisler baslatildi.
pause
