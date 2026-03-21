# Telegram E2E Session Problem

## Problemstellung

Die Telethon-Authentisierung erstellt erfolgreich eine Session-Datei, aber pytest kann die Session beim Test-Aufruf nicht nutzen.

## Symptome

### Authentisierung Erfolgreich
```bash
$ python scripts/auth_telethon.py
Authenticating for phone: 491792999750
Waiting for verification code...
Check your Telegram app for code.
✓ Authentication successful!
Session file created: /home/gun/development/ai/nanobot/nanobot-deep/test_session_user.session
```

### Test-Fehler
```bash
$ pytest tests/e2e/test_telegram_basic.py -m live -v
ERROR: PhoneCodeInvalidError: The phone code entered was invalid
```

## Ursachenanalyse

### 1. Session-Datei Location

**Problem**: Die Session-Datei wird im Projekt-Root erstellt, aber pytest läuft von `tests/e2e/`.

**Auth-Skript** (`scripts/auth_telethon.py`):
```python
client = TelegramClient("test_session_user", api_id, api_hash)
# Erstellt: /home/gun/development/ai/nanobot/nanobot-deep/test_session_user.session
```

**Test-Fixture** (`tests/e2e/conftest.py`):
```python
client = TelegramClient("test_session_user", api_id, api_hash)
# Sucht: /home/gun/development/ai/nanobot/nanobot-deep/tests/e2e/test_session_user.session
```

### 2. FloodWaitError bei Multiplen Versuchen

- **Erster Versuch**: FloodWaitError (113 Sekunden)
- **Zweiter Versuch**: FloodWaitError (227 Sekunden)
- **Jeder weitere Versuch**: Erhöhte Wartezeit

**KONSEQUENZ**: Multiple fehlgeschlagene Authentisierungsversuche führen zu FloodWaitError.

### 3. PhoneCodeInvalidError nach Flood

Wenn FloodWait abgelaufen ist, werden nachfolgende Authentisierungsversuche mit PhoneCodeInvalidError fehlschlagen, weil:
- Der alte Code bereits abgelaufen ist
- Telegram floods den API
- Die Session-Datei wird neu erstellt (alte Session ungültig)

## Lösungen

### Lösung 1: Absolute Session-Datei Paths

```python
# scripts/auth_telethon.py
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
SESSION_PATH = PROJECT_ROOT / "tests" / "e2e" / "test_session_user"

client = TelegramClient(str(SESSION_PATH), api_id, api_hash)
```

```python
# tests/e2e/conftest.py
from pathlib import Path

SESSION_PATH = Path(__file__).parent / "test_session_user"

client = TelegramClient(str(SESSION_PATH), api_id, api_hash)
```

### Lösung 2: Session nach Authentisierung verschieben

```bash
# Nach erfolgreicher Authentisierung
mv test_session_user.session tests/e2e/
```

### Lösung 3: Umgebungsvariable für Session-Path

```bash
export TELEGRAM_SESSION_PATH=/home/gun/development/ai/nanobot/nanobot-deep/tests/e2e/test_session_user.session
```

## Empfohlener Ansatz

**Lösung 2** (Session verschieben nach Authentisierung) ist am einfachsten und zuverlässigsten:

1. Authentisierung durchführen
2. Session verschieben: `mv test_session_user.session tests/e2e/`
3. Tests laufen

## Status

- ✅ Authentisierung erfolgreich (mit Code 90589)
- ✅ Session-Datei erstellt
- ❌ Session-Datei im falschen Verzeichnis (tests/e2e/ statt Projekt-Root)
- ⚠️ FloodWait: 227 Sekunden bei erneuter Authentisierung

## Nächste Schritte

1. FloodWait abwarten (227 Sekunden)
2. Neuen Auth-Code von Telegram erhalten
3. Authentisierung durchführen
4. Session verschieben: `mv test_session_user.session tests/e2e/`
5. Tests ausführen: `pytest tests/e2e/test_telegram*.py -m live -v`
