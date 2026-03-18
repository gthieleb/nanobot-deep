# Ticket #23: Speech-to-Text (STT) Integration

**Status**: Pending  
**Priority**: HIGH  
**Phase**: Phase 3 - User Features  
**Branch**: `feature/speech-to-text`  
**Dependencies**: Ticket #19 (Lightweight Gateway)  
**Estimated Effort**: 10-12 hours  
**Target Release**: v0.5.0

---

## Objective

Implement native speech-to-text support in nanobot-deep gateway with configurable backends: Groq Whisper (cloud, existing) and faster-whisper (local, CTranslate2).

---

## Background

### Current State
- Upstream nanobot has Groq Whisper (`nanobot/providers/transcription.py`)
- `BaseChannel.transcribe_audio()` uses Groq
- nanobot-skills has faster-whisper skill (local)
- No backend selection in nanobot-deep

### Upstream Groq Implementation
- **File**: `nanobot/providers/transcription.py` (~50 lines)
- **Model**: `whisper-large-v3`
- **API**: Groq API (OpenAI-compatible)
- **Usage**: Called by `BaseChannel.transcribe_audio()`

### faster-whisper (from nanobot-skills)
- **Package**: `faster-whisper` (CTranslate2 backend)
- **Models**: tiny, base, small, medium, large-v3
- **Device**: CUDA, MPS, or CPU
- **Advantage**: Local, no API costs, privacy

### Desired State
- Native STT in gateway
- Configurable backend: groq or faster-whisper
- Language detection or specification
- Automatic voice message transcription
- Telegram/Slack voice message support

---

## Technical Approach

### Architecture
```
           ┌─────────────────┐
           │   STTManager    │
           └────────┬────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
┌───────▼───────┐       ┌───────▼───────┐
│ GroqWhisper   │       │ FasterWhisper │
│ (cloud)       │       │ (local)       │
└───────────────┘       └───────────────┘
```

### Backend Selection
| Backend | Pros | Cons |
|---------|------|------|
| Groq | Fast, accurate, no setup | API costs, cloud |
| faster-whisper | Local, free, private | Setup, GPU optional |

### Integration Strategy
1. **Reuse BaseChannel.transcribe_audio()**: Inherit Groq support
2. **Add FasterWhisperProvider**: New provider for local STT
3. **Create STTManager**: Backend selection and routing
4. **Configure in deepagents.json**: Backend selection

---

## Tasks

### 1. Analysis Phase
- [ ] Task 1.1: Analyze upstream transcription
  - File: `nanobot/providers/transcription.py`
  - Focus: API, response format
  - Acceptance: Understand Groq implementation

- [ ] Task 1.2: Analyze faster-whisper skill
  - File: `/tmp/nanobot-skills/faster-whisper/`
  - Focus: Models, device detection, output
  - Acceptance: Understand faster-whisper usage

- [ ] Task 1.3: Design STT interface
  - Interface: Common API for all backends
  - Acceptance: Interface designed

### 2. Implementation Phase
- [ ] Task 2.1: Create STT base interface
  - File: `src/stt/base.py`
  - Methods: `transcribe(file_path) -> str`
  - Acceptance: Base interface created

- [ ] Task 2.2: Create GroqWhisperProvider
  - File: `src/stt/groq.py`
  - Reuse: `nanobot.providers.transcription.GroqTranscriptionProvider`
  - Acceptance: Groq provider works

- [ ] Task 2.3: Create FasterWhisperProvider
  - File: `src/stt/faster_whisper.py`
  - Package: `faster-whisper`
  - Acceptance: faster-whisper provider works

- [ ] Task 2.4: Create STTManager
  - File: `src/stt/manager.py`
  - Features: Backend selection, config loading
  - Acceptance: Manager routes to correct backend

### 3. Integration Phase
- [ ] Task 3.1: Integrate with DeepChannel
  - Override: `transcribe_audio()` to use STTManager
  - Acceptance: Channel uses new STT

- [ ] Task 3.2: Add Telegram voice handler
  - Handler: Voice message -> download -> transcribe -> respond
  - Acceptance: Telegram voice works

- [ ] Task 3.3: Add Slack voice handler
  - Handler: Audio file -> download -> transcribe -> respond
  - Acceptance: Slack audio works

### 4. Configuration Phase
- [ ] Task 4.1: Add STT config schema
  - File: `src/config/schema.py`
  - Fields: backend, language, model_size
  - Acceptance: Config schema defined

- [ ] Task 4.2: Add STT to deepagents.json
  - Example with both backends
  - Acceptance: Config documented

### 5. Dependencies
- [ ] Task 5.1: Add faster-whisper to pyproject.toml
  - Optional: `stt = ["faster-whisper"]` extra
  - Acceptance: Package installable

### 6. Testing
- [ ] Task 6.1: Unit tests for STTManager
  - File: `tests/unit/test_stt_manager.py`
  - Mock: Transcription providers
  - Acceptance: 90%+ coverage

- [ ] Task 6.2: Unit tests for FasterWhisperProvider
  - File: `tests/unit/test_stt_faster_whisper.py`
  - Mock: WhisperModel
  - Acceptance: 90%+ coverage

- [ ] Task 6.3: E2E tests for voice transcription
  - File: `tests/e2e/test_stt.py`
  - Mark: `@pytest.mark.live`
  - Scenario: Voice message transcribed
  - Acceptance: Live transcription works

### 7. Documentation
- [ ] Task 7.1: Document STT backends
  - File: `docs/features/speech-to-text.md`
  - Content: Groq vs faster-whisper, setup, config
  - Acceptance: Documentation complete

- [ ] Task 7.2: Update README
  - Section: Speech-to-text support
  - Acceptance: README updated

---

## Deliverables

### Code
- `src/stt/__init__.py` - Module exports
- `src/stt/base.py` - Base interface
- `src/stt/groq.py` - Groq provider (reuses upstream)
- `src/stt/faster_whisper.py` - faster-whisper provider
- `src/stt/manager.py` - STT manager
- Updated `src/channels/deep_channel.py` - Integration

### Tests
- `tests/unit/test_stt_manager.py`
- `tests/unit/test_stt_faster_whisper.py`
- `tests/e2e/test_stt.py`

### Documentation
- `docs/features/speech-to-text.md`
- Updated `README.md`

---

## Acceptance Criteria

### Functional Requirements
- [ ] Groq Whisper backend works
- [ ] faster-whisper backend works
- [ ] Backend selectable via config
- [ ] Language detection works
- [ ] Telegram voice messages transcribed
- [ ] Slack audio files transcribed

### Non-Functional Requirements
- [ ] Groq: <5s for 1min audio
- [ ] faster-whisper (GPU): <10s for 1min audio
- [ ] faster-whisper (CPU): <30s for 1min audio
- [ ] Graceful fallback on failure

### Quality Requirements
- [ ] Reuses upstream Groq provider
- [ ] Unit test coverage >= 90%
- [ ] E2E tests pass

---

## Implementation Notes

### Key Decisions
1. **Reuse Upstream**: Groq provider from nanobot
2. **Optional faster-whisper**: Extra dependency for local STT
3. **Manager Pattern**: Single interface for multiple backends

### faster-whisper Models
| Model | VRAM | Speed | Accuracy |
|-------|------|-------|----------|
| tiny | ~1 GB | Fastest | Lowest |
| base | ~1 GB | Fast | Good |
| small | ~2 GB | Medium | Better |
| medium | ~5 GB | Slow | High |
| large-v3 | ~10 GB | Slowest | Best |

Default: `base` (good balance for German)

### Configuration Example
```json
{
  "stt": {
    "backend": "faster-whisper",
    "language": "de",
    "model": "base",
    "device": "auto"
  }
}
```

---

## Related Tickets
- **Depends on**: #19 (Lightweight Gateway)
- **Related**: #24 (Text-to-Speech) - Voice I/O pair

---

Last updated: 2026-03-18
