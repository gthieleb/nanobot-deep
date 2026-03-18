# Ticket #10: Media Processing

**Status**: Pending  
**Priority**: MEDIUM  
**Phase**: Phase 3 - User Features  
**Branch**: `feature/media-processing`  
**Dependencies**: Ticket #8 (Human-in-the-Loop)  
**Estimated Effort**: 10-14 hours  
**Target Release**: v0.5.0

---

## Objective

Implement full media type support for images, audio, video, and documents, enabling agents to receive, process, and respond with rich media content in Telegram/Slack.

---

## Background

### Current State
- Limited media support (text only)
- No image processing
- No audio transcription
- No video processing
- No document parsing
- No media generation

### Desired State
- Full media type support (images, audio, video, documents)
- Image processing (analyze, describe, OCR)
- Audio transcription (speech-to-text)
- Video processing (analyze frames, transcribe)
- Document parsing (PDF, Word, Excel)
- Media generation (images via DALL-E)
- Unit tests for media processing
- E2E tests for media handling
- Documentation explaining media features

### Context from Planning Session
- **Decision**: Use multimodal models for media processing
  - Rationale: Native support, best quality
  - Alternative: Separate APIs (rejected - complexity)
- **Integration Point**: DeepAgent with multimodal models
- **Priority**: Phase 3 (parallel with other user features)
- **Use Case**: Analyze screenshots, transcribe voice messages, parse documents

---

## Technical Approach

### Architecture
- **Media Handler**: Receive and route media messages
- **Image Processor**: Multimodal model for image analysis
- **Audio Processor**: Whisper for transcription
- **Video Processor**: Frame extraction + analysis
- **Document Parser**: PDF/text extraction libraries
- **Media Generator**: DALL-E for image generation

### Implementation Strategy
1. **Research Phase**: Study multimodal models and APIs
2. **Design Phase**: Define media processing pipeline
3. **Image Phase**: Implement image processing
4. **Audio Phase**: Implement audio transcription
5. **Video Phase**: Implement video processing
6. **Document Phase**: Implement document parsing
7. **Generation Phase**: Implement media generation
8. **Testing Phase**: Unit + E2E tests
9. **Documentation Phase**: Media feature docs

### Key Decisions
- **Image Analysis**: GPT-4 Vision or Claude Vision
- **Audio Transcription**: OpenAI Whisper API
- **Video Processing**: Frame extraction + image analysis
- **Document Parsing**: PyPDF2, python-docx, openpyxl
- **Image Generation**: DALL-E 3 API

---

## Tasks

### 1. Analysis & Research
- [ ] Task 1.1: Study multimodal model capabilities
  - Models: GPT-4 Vision, Claude Vision, Gemini Vision
  - Focus: Image analysis, OCR, chart reading
  - Acceptance: Document model capabilities and limitations

- [ ] Task 1.2: Study Whisper transcription API
  - API: OpenAI Whisper, local Whisper models
  - Focus: Quality, speed, language support
  - Acceptance: Document transcription options

- [ ] Task 1.3: Study document parsing libraries
  - Libraries: PyPDF2, pdfplumber, python-docx, openpyxl
  - Focus: Text extraction, table parsing, structure preservation
  - Acceptance: Document parsing library capabilities

- [ ] Task 1.4: Study Telegram/Slack media APIs
  - Telegram: `get_file`, file downloads, media types
  - Slack: `files.info`, file downloads, media types
  - Acceptance: Document platform media handling

### 2. Design Phase
- [ ] Task 2.1: Define media processing pipeline
  - Stages: Receive → Validate → Process → Respond
  - File: `src/media/pipeline.py`
  - Acceptance: Media pipeline design document

- [ ] Task 2.2: Define media schema
  - Fields: media_type, url, bytes, metadata, processing_result
  - File: `src/media/schema.py`
  - Acceptance: Pydantic model for media

- [ ] Task 2.3: Define processor interface
  - Methods: can_process, process, get_result
  - File: `src/media/processor.py`
  - Acceptance: Abstract processor interface

### 3. Image Processing
- [ ] Task 3.1: Create image processor
  - Features: Analyze, describe, OCR, chart reading
  - File: `src/media/processors/image.py`
  - Acceptance: Image processor implementation

- [ ] Task 3.2: Add multimodal model integration
  - Integration: GPT-4 Vision or Claude Vision
  - File: `src/media/models/vision.py`
  - Acceptance: Vision model integration

- [ ] Task 3.3: Add Telegram image handling
  - Features: Receive image, download, process, respond
  - File: `src/media/handlers/telegram_image.py`
  - Acceptance: Telegram image handling

- [ ] Task 3.4: Add Slack image handling
  - Features: Receive image, download, process, respond
  - File: `src/media/handlers/slack_image.py`
  - Acceptance: Slack image handling

### 4. Audio Processing
- [ ] Task 4.1: Create audio processor
  - Features: Transcribe, detect language, speaker diarization
  - File: `src/media/processors/audio.py`
  - Acceptance: Audio processor implementation

- [ ] Task 4.2: Add Whisper integration
  - API: OpenAI Whisper API
  - File: `src/media/models/whisper.py`
  - Acceptance: Whisper integration

- [ ] Task 4.3: Add Telegram voice handling
  - Features: Receive voice message, transcribe, respond
  - File: `src/media/handlers/telegram_voice.py`
  - Acceptance: Telegram voice handling

- [ ] Task 4.4: Add Slack audio handling
  - Features: Receive audio file, transcribe, respond
  - File: `src/media/handlers/slack_audio.py`
  - Acceptance: Slack audio handling

### 5. Video Processing
- [ ] Task 5.1: Create video processor
  - Features: Frame extraction, analysis, transcription
  - File: `src/media/processors/video.py`
  - Acceptance: Video processor implementation

- [ ] Task 5.2: Add frame extraction
  - Library: ffmpeg or opencv
  - File: `src/media/utils/frames.py`
  - Acceptance: Frame extraction utility

- [ ] Task 5.3: Add video transcription
  - Features: Extract audio, transcribe, combine with frames
  - Acceptance: Video transcription support

### 6. Document Processing
- [ ] Task 6.1: Create PDF processor
  - Features: Text extraction, table parsing, OCR if needed
  - File: `src/media/processors/pdf.py`
  - Acceptance: PDF processor implementation

- [ ] Task 6.2: Create Word processor
  - Features: Text extraction, formatting preservation
  - File: `src/media/processors/word.py`
  - Acceptance: Word processor implementation

- [ ] Task 6.3: Create Excel processor
  - Features: Sheet extraction, table parsing, formula evaluation
  - File: `src/media/processors/excel.py`
  - Acceptance: Excel processor implementation

- [ ] Task 6.4: Add document handling
  - Features: Receive document, parse, respond
  - File: `src/media/handlers/documents.py`
  - Acceptance: Document handling

### 7. Media Generation
- [ ] Task 7.1: Create image generator
  - API: DALL-E 3 or Stable Diffusion
  - File: `src/media/generators/image.py`
  - Acceptance: Image generator implementation

- [ ] Task 7.2: Add generation tool
  - Tool: Generate image from description
  - File: `src/tools/generate_image.py`
  - Acceptance: Image generation tool

- [ ] Task 7.3: Add response with images
  - Features: Send generated image to Telegram/Slack
  - Acceptance: Image response support

### 8. Testing
- [ ] Task 8.1: Unit tests for image processor
  - File: `tests/unit/test_media_image.py`
  - Coverage: Analysis, OCR, validation
  - Acceptance: 90%+ coverage

- [ ] Task 8.2: Unit tests for audio processor
  - File: `tests/unit/test_media_audio.py`
  - Coverage: Transcription, language detection
  - Acceptance: 90%+ coverage

- [ ] Task 8.3: Unit tests for document processors
  - File: `tests/unit/test_media_documents.py`
  - Coverage: Parsing, extraction, formatting
  - Acceptance: 90%+ coverage

- [ ] Task 8.4: E2E tests for media handling
  - File: `tests/e2e/test_media.py`
  - Mark: `@pytest.mark.live`
  - Scenario: Send image, verify analysis
  - Acceptance: Live media processing works

### 9. Documentation
- [ ] Task 9.1: Write media features docs
  - File: `docs/media-features.md`
  - Content: Supported types, commands, examples
  - Acceptance: Media feature documentation

- [ ] Task 9.2: Update README with media section
  - Section: Media support, types, examples
  - Acceptance: README includes media overview

---

## Deliverables

### Code
- `src/media/` directory with:
  - `__init__.py` - Module exports
  - `schema.py` - Media schemas
  - `pipeline.py` - Processing pipeline
  - `processor.py` - Abstract processor
  - `processors/` - Media processors
    - `__init__.py`
    - `image.py`
    - `audio.py`
    - `video.py`
    - `pdf.py`
    - `word.py`
    - `excel.py`
  - `handlers/` - Platform handlers
    - `__init__.py`
    - `telegram_image.py`
    - `telegram_voice.py`
    - `slack_image.py`
    - `slack_audio.py`
    - `documents.py`
  - `generators/` - Media generators
    - `__init__.py`
    - `image.py`
  - `models/` - Model integrations
    - `__init__.py`
    - `vision.py`
    - `whisper.py`
  - `utils/` - Utilities
    - `__init__.py`
    - `frames.py`
- `src/tools/generate_image.py` - Image generation tool

### Tests
- `tests/unit/test_media_image.py`
- `tests/unit/test_media_audio.py`
- `tests/unit/test_media_documents.py`
- `tests/e2e/test_media.py`

### Documentation
- `docs/media-features.md` - Feature documentation
- Updated `README.md` - Media section

---

## Acceptance Criteria

### Functional Requirements
- [ ] Images can be analyzed and described
- [ ] Voice messages can be transcribed
- [ ] Videos can be analyzed (frames)
- [ ] PDFs can be parsed for text
- [ ] Word documents can be extracted
- [ ] Excel sheets can be read
- [ ] Images can be generated

### Non-Functional Requirements
- [ ] Image analysis completes in <10 seconds
- [ ] Audio transcription completes in <30 seconds
- [ ] Document parsing completes in <5 seconds
- [ ] Large files handled gracefully
- [ ] Error handling for unsupported formats

### Quality Requirements
- [ ] Unit test coverage >= 90%
- [ ] E2E tests pass with live APIs
- [ ] All code passes linting (ruff)
- [ ] All code passes type checking (pyright)

---

## Implementation Notes

### Key Decisions
1. **Vision Models**: Use native multimodal models
2. **Whisper**: OpenAI Whisper API for quality
3. **Documents**: Python libraries for parsing
4. **Generation**: DALL-E 3 for image generation

### Pitfalls to Avoid
- **Large Files**: Handle size limits gracefully
- **Rate Limits**: Respect API rate limits
- **Memory Usage**: Stream large files
- **Format Support**: Validate formats strictly

---

## Related Tickets
- **Depends on**: #8 (Human-in-the-Loop) - Phase 2 complete
- **Parallel with**: #9, #11, #12 (Phase 3)
- **Related**: #8 (HITL) - Media approval for sensitive content

---

Last updated: 2026-03-18
