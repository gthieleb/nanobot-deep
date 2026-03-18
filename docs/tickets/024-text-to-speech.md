# Ticket #24: Text-to-Speech (TTS) Integration

**Status**: Pending  
**Priority**: HIGH  
**Phase**: Phase 3 - User Features  
**Branch**: `feature/text-to-speech`  
**Dependencies**: Ticket #19 (Lightweight Gateway)  
**Estimated Effort**: 10-12 hours  
**Target Release**: v0.5.0

---

## Objective

Implement native text-to-speech support in nanobot-deep gateway with Piper TTS (local, German models) as primary backend and OpenAI TTS as optional cloud fallback.

---

## Background

### Current State
- No TTS support in nanobot-deep
- nanobot-skills has OpenAI TTS (`voice-messages/tts_generator.py`)
- No Piper TTS integration
- No voice response capability

### Piper TTS (Preferred)
- **Repository**: https://github.com/rhasspy/piper
- **Models**: Multiple languages including German (`de_DE`)
- **Advantages**: 
  - Local, no API costs
  - Privacy (no data sent to cloud)
  - High-quality German voices
  - Fast inference on CPU
- **Models**:
  - `de_DE-thorsten-low` (fastest, smallest)
  - `de_DE-thorsten-medium` (balanced)
  - `de_DE-thorsten-high` (best quality)
  - `de_DE-ramona-low` (female voice)

### OpenAI TTS (Optional Fallback)
- **Models**: `tts-1`, `tts-1-hd`
- **Voices**: alloy, echo, fable, onyx, nova, shimmer
- **Languages**: Multiple including German
- **Limit**: 4096 characters per request
- **Note**: Good quality but cloud-based, costs money

### Desired State
- Native TTS in gateway
- Piper TTS as primary (local, German focus)
- OpenAI TTS as optional fallback
- Language configurable (German default)
- Voice response mode toggle
- Telegram/Slack voice response support

---

## Technical Approach

### Architecture
```
           ┌─────────────────┐
           │   TTSManager    │
           └────────┬────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
┌───────▼───────┐       ┌───────▼───────┐
│ PiperTTS      │       │ OpenAITTS     │
│ (local)       │       │ (cloud)       │
│ German focus  │       │ Optional      │
└───────────────┘       └───────────────┘
```

### Backend Selection
| Backend | Pros | Cons |
|---------|------|------|
| Piper | Local, free, German models | Setup, limited voices |
| OpenAI | Easy, multiple voices | Cloud, costs, privacy |

### Integration Strategy
1. **Create PiperProvider**: New provider for Piper TTS
2. **Create OpenAIProvider**: Port from nanobot-skills
3. **Create TTSManager**: Backend selection and routing
4. **Voice Response Mode**: Toggle to enable/disable
5. **Configure in deepagents.json**: Backend and language

---

## Tasks

### 1. Analysis Phase
- [ ] Task 1.1: Research Piper TTS
  - Source: https://github.com/rhasspy/piper
  - Focus: Installation, models, API, German voices
  - Acceptance: Understand Piper usage

- [ ] Task 1.2: Analyze nanobot-skills OpenAI TTS
  - File: `/tmp/nanobot-skills/voice-messages/tts_generator.py`
  - Focus: API, voice selection, output
  - Acceptance: Understand OpenAI TTS usage

- [ ] Task 1.3: Design TTS interface
  - Interface: Common API for all backends
  - Acceptance: Interface designed

### 2. Implementation Phase
- [ ] Task 2.1: Create TTS base interface
  - File: `src/tts/base.py`
  - Methods: `synthesize(text) -> bytes`, `synthesize_to_file(text, path)`
  - Acceptance: Base interface created

- [ ] Task 2.2: Create PiperTTSProvider
  - File: `src/tts/piper.py`
  - Package: `piper-tts` or subprocess
  - Models: Download German models
  - Acceptance: Piper provider works

- [ ] Task 2.3: Create OpenAITTSProvider
  - File: `src/tts/openai.py`
  - Port: From nanobot-skills
  - Acceptance: OpenAI provider works

- [ ] Task 2.4: Create TTSManager
  - File: `src/tts/manager.py`
  - Features: Backend selection, language config
  - Acceptance: Manager routes to correct backend

### 3. Voice Response Mode
- [ ] Task 3.1: Add voice mode toggle
  - Command: `/voice on`, `/voice off`
  - File: `src/commands/voice.py`
  - Acceptance: Toggle works

- [ ] Task 3.2: Add voice mode persistence
  - Storage: Per-session or per-user
  - Acceptance: Mode persists

- [ ] Task 3.3: Integrate with message flow
  - Logic: If voice mode on, TTS the response
  - Acceptance: Voice responses sent

### 4. Channel Integration
- [ ] Task 4.1: Add Telegram voice response
  - Method: Send audio file as voice message
  - Format: OGG for Telegram
  - Acceptance: Telegram voice works

- [ ] Task 4.2: Add Slack voice response
  - Method: Upload audio file
  - Format: MP3 for Slack
  - Acceptance: Slack audio works

### 5. Configuration Phase
- [ ] Task 5.1: Add TTS config schema
  - File: `src/config/schema.py`
  - Fields: backend, language, voice, model
  - Acceptance: Config schema defined

- [ ] Task 5.2: Add TTS to deepagents.json
  - Example with Piper and OpenAI options
  - Acceptance: Config documented

### 6. Dependencies
- [ ] Task 6.1: Add piper-tts to pyproject.toml
  - Package: `piper-tts` or similar
  - Optional: `tts = ["piper-tts"]` extra
  - Acceptance: Package installable

- [ ] Task 6.2: Document model download
  - Models: de_DE models download location
  - Acceptance: Model setup documented

### 7. Testing
- [ ] Task 7.1: Unit tests for TTSManager
  - File: `tests/unit/test_tts_manager.py`
  - Mock: TTS providers
  - Acceptance: 90%+ coverage

- [ ] Task 7.2: Unit tests for PiperProvider
  - File: `tests/unit/test_tts_piper.py`
  - Mock: Piper subprocess
  - Acceptance: 90%+ coverage

- [ ] Task 7.3: E2E tests for voice responses
  - File: `tests/e2e/test_tts.py`
  - Mark: `@pytest.mark.live`
  - Scenario: Response as voice message
  - Acceptance: Live TTS works

### 8. Documentation
- [ ] Task 8.1: Document TTS backends
  - File: `docs/features/text-to-speech.md`
  - Content: Piper vs OpenAI, setup, models, config
  - Acceptance: Documentation complete

- [ ] Task 8.2: Document German model setup
  - File: `docs/features/piper-german-models.md`
  - Content: How to download and use German models
  - Acceptance: German model docs complete

- [ ] Task 8.3: Update README
  - Section: Text-to-speech support
  - Acceptance: README updated

---

## Deliverables

### Code
- `src/tts/__init__.py` - Module exports
- `src/tts/base.py` - Base interface
- `src/tts/piper.py` - Piper provider
- `src/tts/openai.py` - OpenAI provider
- `src/tts/manager.py` - TTS manager
- `src/commands/voice.py` - Voice mode command
- Updated channel handlers

### Tests
- `tests/unit/test_tts_manager.py`
- `tests/unit/test_tts_piper.py`
- `tests/e2e/test_tts.py`

### Documentation
- `docs/features/text-to-speech.md`
- `docs/features/piper-german-models.md`
- Updated `README.md`

---

## Acceptance Criteria

### Functional Requirements
- [ ] Piper TTS backend works
- [ ] OpenAI TTS backend works
- [ ] Backend selectable via config
- [ ] German models available and working
- [ ] Voice response mode toggle works
- [ ] Telegram voice responses sent
- [ ] Slack audio responses sent

### Non-Functional Requirements
- [ ] Piper: <2s for 100 chars on CPU
- [ ] Piper: <0.5s for 100 chars on GPU
- [ ] OpenAI: <3s for 100 chars
- [ ] Graceful fallback on failure

### Quality Requirements
- [ ] Unit test coverage >= 90%
- [ ] E2E tests pass
- [ ] German voice quality acceptable

---

## Implementation Notes

### Key Decisions
1. **Piper First**: Primary backend for German focus
2. **OpenAI Optional**: Fallback for specific use cases
3. **Language Config**: Default German, configurable

### Piper German Models
| Model | Quality | Size | Speed |
|-------|---------|------|-------|
| de_DE-thorsten-low | Good | ~20 MB | Fastest |
| de_DE-thorsten-medium | Better | ~50 MB | Fast |
| de_DE-thorsten-high | Best | ~100 MB | Medium |
| de_DE-ramona-low | Good (female) | ~20 MB | Fast |

Default: `de_DE-thorsten-medium` (best balance)

### Configuration Example
```json
{
  "tts": {
    "backend": "piper",
    "language": "de",
    "voice": "thorsten-medium",
    "fallback_backend": "openai"
  }
}
```

### Model Download
```bash
# Download German models
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/de/de_DE/thorsten/medium/de_DE-thorsten-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/de/de_DE/thorsten/medium/de_DE-thorsten-medium.onnx.json
```

---

## Related Tickets
- **Depends on**: #19 (Lightweight Gateway)
- **Related**: #23 (Speech-to-Text) - Voice I/O pair

---

Last updated: 2026-03-18
