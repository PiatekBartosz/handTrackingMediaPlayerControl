@echo off
echo Budowanie paczki wheel...
uv build
if %ERRORLEVEL% neq 0 (
    echo Blad podczas budowania paczki!
    exit /b %ERRORLEVEL%
)
echo.
echo Gotowe! Paczka zostala zapisana w folderze dist\
echo Mozesz ja zainstalowac poleceniem:
echo     pip install dist\hand_tracking_media_player_control-*.whl
