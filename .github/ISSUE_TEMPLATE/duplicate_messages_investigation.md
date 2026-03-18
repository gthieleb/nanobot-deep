---
name: Duplicate/Disappearing Messages Investigation
about: Track investigation of duplicate short messages that disappear
title: "[BUG] Kurze Telegram-Antworten erscheinen doppelt und verschwinden wieder"
labels: bug, investigation, telegram
assignees: ''
---

## Problem Beschreibung

Kurze Bot-Antworten bei Telegram erscheinen kurzzeitig doppelt und verschwinden dann wieder. Längere Antworten scheinen nicht betroffen zu sein.

**Verhalten:**
- Kurze Antwort (z.B. "Ja", "Bist du noch da?") erscheint
- Erscheint kurzzeitig als zweite Nachricht
- Zweite Nachricht verschwindet nach ~1 Sekunde
- Finale Nachricht bleibt bestehen

## Hypothese

Vermutlich werden **Telegram Draft Messages** kurzzeitig als separate Messages angezeigt, bevor sie durch die finale Message ersetzt werden. Dies ist möglicherweise normales Telegram-Verhalten, könnte aber für User verwirrend sein.

## Untersuchungsergebnisse

### ✅ Bereits ausgeschlossen

- [x] **Message Bus Race Conditions**: Queue-Implementierung sauber, nur ein Consumer
- [x] **Telegram Channel Duplikate**: `send()` sendet nur eine Message pro `OutboundMessage`  
- [x] **Gateway Duplikate**: Nur ein `publish_outbound()` pro Agent-Response
- [x] **nanobot-deep Code**: Keine Duplikat-Logik gefunden

### ❓ Zu untersuchen

- [ ] **Telegram Draft Message API**: Werden Drafts als separate Messages angezeigt?
- [ ] **python-telegram-bot Framework**: Version-spezifisches Verhalten?
- [ ] **Nachrichten-Längen-Schwellwert**: Ab welcher Länge keine Duplikate?
- [ ] **Telegram Client-Verhalten**: Desktop vs. Mobile vs. Web?
- [ ] **Slack Vergleich**: Tritt das Problem auch bei Slack auf?

## Reproduktion

### Test-Tool

Ein Test-Tool wurde erstellt um das Verhalten systematisch zu analysieren:

```bash
# 1. Gateway starten
nanobot-deep gateway --verbose > gateway.log 2>&1 &

# 2. Test-Tool starten
python tests/manual/test_duplicate_messages.py

# 3. Test-Messages senden
# Siehe Tool-Output für empfohlene Test-Cases
```

**Test-Cases:**
- **Sehr kurz**: "Ja", "Nein", "OK" (wahrscheinlich Duplikat)
- **Kurz**: "Bist du noch da?" (möglicherweise Duplikat)
- **Mittel**: "Was kannst du?" (vermutlich kein Duplikat)
- **Lang**: Frage mit >100 Zeichen (kein Duplikat erwartet)

### Zu dokumentieren

Für jede Test-Message bitte notieren:

1. **User-Message**: Was wurde gesendet
2. **Bot-Response Länge**: Anzahl Zeichen
3. **Duplikat beobachtet?**: Ja/Nein
4. **Verschwinde-Zeit**: Wie lange war das Duplikat sichtbar?
5. **Telegram Client**: Mobile/Desktop/Web
6. **Draft-Messages sichtbar?**: "..." oder Typing-Indicator?

## Technische Details

### Log-Analyse

Relevante Log-Patterns:

```bash
# Zeige Message-Flow für letzte Antwort
grep -E "Processing message|sendMessageDraft|sendMessage[^D]|Response published" gateway.log | tail -20

# Zähle Draft vs. Final Messages
grep "sendMessageDraft" gateway.log | wc -l
grep "sendMessage[^D]" gateway.log | grep -v Draft | wc -l
```

### Code-Stellen

**Telegram Channel** (`nanobot/channels/telegram.py`):
- `send()` method (L233-298): Sendet finale Message
- `_typing_loop()` (L508-514): Typing-Indicator
- Keine Draft-Message Logik im nanobot Code

**Message Bus** (`nanobot/bus/queue.py`):
- `publish_outbound()` (L28-30): Simple Queue put
- `consume_outbound()` (L32-34): Simple Queue get

**Gateway** (`nanobot_deep/gateway.py`):
- `_process_inbound()` (L99-134): Ein publish pro Response

### python-telegram-bot Framework

Die `sendMessageDraft` Calls im Log kommen vom Framework selbst:

```python
# Framework sendet automatisch Draft-Updates während Response-Generierung
# Dies ist für "Typing..."-Animation gedacht
# Bei kurzen Messages könnte Draft als separate Message erscheinen
```

## Mögliche Lösungen

### Option 1: Draft Messages deaktivieren

Falls Drafts das Problem sind, könnte man sie deaktivieren:

```python
# In telegram channel config
config.telegram.enable_drafts = False  # falls verfügbar
```

### Option 2: Mindest-Delay für kurze Messages

Bei sehr kurzen Responses künstlich verzögern, damit Draft nicht sichtbar wird:

```python
if len(response.content) < 50:
    await asyncio.sleep(0.5)  # Draft verschwindet bevor finale kommt
```

### Option 3: Framework Update

Prüfen ob neuere Version von `python-telegram-bot` das Verhalten ändert.

### Option 4: Akzeptieren als Feature

Falls es tatsächlich nur Draft→Final Übergang ist, könnte es akzeptables UX sein.

## Environment

- **nanobot-deep**: v0.1.0 (nach ChatLiteLLM + AsyncSqliteSaver fixes)
- **python-telegram-bot**: [TODO: Version prüfen]
- **Telegram Client**: [TODO: dokumentieren]
- **OS**: Linux/WSL2

## Nächste Schritte

- [ ] Test-Tool ausführen und Daten sammeln
- [ ] Längen-Schwellwert identifizieren
- [ ] Verschiedene Telegram Clients testen
- [ ] Slack-Vergleich durchführen
- [ ] python-telegram-bot Version prüfen
- [ ] Entscheiden: Bug-Fix oder Feature-as-is

## Zusätzliche Notizen

Basierend auf bisheriger Analyse ist dies **wahrscheinlich kein kritischer Bug**, sondern Telegram's Draft-Message Feature in Aktion. Könnte aber UX-Verbesserung durch Anpassung geben.
