# Sterowanie odtwarzaczem mediów gestami dłoni

## Opis

Aplikacja umożliwia zdalne sterowanie odtwarzaczem mediów za pomocą rozpoznawania gestów dłoni. Serwer przetwarza obraz z kamery klienta i wysyła odpowiednie klawisze multimedialne.

Obsługiwane gesty:

| Gest | Akcja |
|------|-------|
| Pointing Up + ruch w prawo | Następny utwór |
| Pointing Up + ruch w lewo | Poprzedni utwór |
| Closed Fist | Odtwarzanie / pauza |
| Thumb Up | Głośność w górę |
| Thumb Down | Głośność w dół |

## Wymagania wstępne

- Python 3.10 lub nowszy
- [uv](https://docs.astral.sh/uv/getting-started/installation/) – menedżer pakietów
- Modele MediaPipe umieszczone w folderze `model/`:
  - `model/gesture_recognizer.task`
  - `model/hand_landmarker.task`

Modele możesz pobrać ze strony [Google MediaPipe](https://ai.google.dev/edge/mediapipe/solutions/vision/gesture_recognizer).

---

## Sposób 1 – uruchamianie z uv (tryb deweloperski)

### 1. Zainstaluj uv

```bash
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Zainstaluj zależności

W katalogu projektu uruchom:

```bash
uv sync
```

uv automatycznie tworzy wirtualne środowisko i instaluje wszystkie zależności z pliku `pyproject.toml`.

### 3. Uruchom serwer

```bash
uv run server_demo.py
```

Opcjonalnie z własnym adresem IP i portem:

```bash
uv run server_demo.py --ip 192.168.1.10 --port 9999
```

### 4. Uruchom klienta (w osobnym terminalu)

```bash
uv run client_demo.py
```

Opcjonalnie ze wskazaniem adresu serwera:

```bash
uv run client_demo.py --ip 192.168.1.10 --port 9999
```

> **Uwaga:** serwer i klient muszą być uruchomione w osobnych terminalach.

---

## Sposób 2 – instalacja z paczki wheel

### 1. Zbuduj paczkę

```bash
# Windows
build.bat

# macOS / Linux
chmod +x build.sh
./build.sh
```

Plik `.whl` zostanie wygenerowany w folderze `dist/`.

### 2. Zainstaluj paczkę

```bash
pip install dist/hand_tracking_media_player_control-0.1.0-*.whl
```

Lub przy użyciu uv:

```bash
uv pip install dist/hand_tracking_media_player_control-0.1.0-*.whl
```

### 3. Uruchom skrypty

Po instalacji paczki uruchom skrypty z katalogu projektu (wymagana obecność folderu `model/`):

```bash
python server_demo.py
python client_demo.py
```

---

## Struktura projektu

```
handTrackingMediaPlayerControl/
├── helpers/
│   ├── __init__.py
│   ├── UDP_factory.py          # Klasy klienta i serwera UDP
│   └── mediapipe_recognizer.py # Rozpoznawanie gestów MediaPipe
├── model/
│   ├── gesture_recognizer.task
│   └── hand_landmarker.task
├── server_demo.py              # Punkt startowy serwera
├── client_demo.py              # Punkt startowy klienta
├── pyproject.toml              # Konfiguracja projektu i zależności
├── build.bat                   # Skrypt budowania (Windows)
└── build.sh                    # Skrypt budowania (macOS/Linux)
```
