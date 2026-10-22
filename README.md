# P.A.T — Personal AI Technology

**Version:** 2.0.0
**Project type:** Personal AI Assistant
**Status:** Development in progress

## 1. Project Overview

P.A.T (Personal AI Technology) is a personal assistant project designed to combine conversational interaction, voice input and output, persistent memory, task planning, and supported computer automation in one application.

The project aims to provide a friendly, practical assistant that can understand user requests, respond conversationally, and carry out supported tasks with clear feedback.

## 2. Main Features

- **Voice interaction:** Microphone input and spoken responses.
- **Local speech recognition:** Uses Faster-Whisper to transcribe recorded speech locally after the model is available.
- **Text-to-speech:** Uses `pyttsx3` for spoken output.
- **Conversation context:** Maintains a limited history of recent messages.
- **Persistent memory:** Saves supported user information in a local JSON file.
- **Intent detection:** Identifies recognized command categories.
- **Task planning:** Creates step-based plans for supported tasks.
- **Application tools:** Includes supported actions such as opening Calculator, Notepad, and browser pages.
- **File utilities:** Supports listing files and folders, counting items, and working with specified paths.
- **System information:** Can report basic operating-system and Python information.
- **Arithmetic:** Supports basic arithmetic through a restricted expression evaluator.

*Feature availability depends on the current implementation and successful integration of the project modules.*

## 3. Technology Stack

| Component | Technology |
|---|---|
| Programming language | Python |
| Speech recognition | Faster-Whisper |
| Speech output | pyttsx3 |
| Microphone/audio input | SpeechRecognition and PyAudio |
| Persistent memory | JSON |
| Task and intent logic | Python modules |
| Development environment | Windows / Python virtual environment |

## 4. Project Structure

```text
PAT-source/
├── assistant.py
├── commands.py
├── config.py
├── main.py
├── memory.py
├── voice.py
├── README.md
├── ai/
│   ├── __init__.py
│   ├── ai_engine.py
│   ├── context.py
│   ├── intent_engine.py
│   ├── planner.py
│   ├── reasoning_engine.py
│   ├── response.py
│   └── task_engine.py
└── tools/
    ├── app_tools.py
    └── file_tools.py
```

## 5. Installation

### Requirements

- A compatible Python installation
- Microphone for voice input
- Speakers or headphones for speech output
- Internet access for initial package/model downloads, where required
- Sufficient disk space and RAM for the selected speech-recognition model

### Create a virtual environment

From the `PAT-source` directory, open a terminal and run:

```powershell
py -3.13 -m venv .venv313
```

Activate it:

```powershell
.\.venv313\Scripts\Activate.ps1
```

If PowerShell activation is unavailable, use Command Prompt:

```bat
.venv313\Scripts\activate.bat
```

Install the project's dependencies using the repository's dependency file if one is available:

```powershell
python -m pip install --upgrade pip
python -m pip install -r ..\requirements.txt
```

If the dependency file is stored elsewhere, adjust the path to match its actual location.

## 6. Configuration

P.A.T supports environment variables for selected voice settings.

| Variable | Purpose | Default |
|---|---|---|
| `PAT_MICROPHONE_INDEX` | Selects the microphone device index | `1` |
| `PAT_WHISPER_MODEL` | Selects the Faster-Whisper model | `small` |
| `PAT_WHISPER_DEVICE` | Selects the inference device | `cpu` |
| `PAT_WHISPER_COMPUTE_TYPE` | Selects the model compute type | `int8` |

For example, in PowerShell:

```powershell
$env:PAT_WHISPER_MODEL = "tiny"
$env:PAT_MICROPHONE_INDEX = "1"
```

The `tiny` model may be faster on a CPU, while `small` may provide better recognition in some situations. Actual performance depends on the hardware and audio quality.

## 7. Running P.A.T

From the `PAT-source` directory, with the virtual environment activated:

```powershell
python main.py
```

The application should initialize the assistant and voice interface, display its greeting, and begin listening for user input.

Use `help` to view supported commands. Use `exit` or `quit` to request a normal exit.

## 8. Privacy and Safety

- Speech transcription is designed to use a local Faster-Whisper model.
- The initial model download may require internet access.
- Text-to-speech and microphone access require the appropriate local permissions.
- Persistent memory is stored locally in a JSON file.
- Avoid storing passwords, API keys, financial credentials, or other secrets in the memory file.
- Computer-control actions must be limited to supported tools.
- Destructive operations such as shutdown and restart should require explicit confirmation before being enabled.
- Always verify the target path before opening or modifying files.

## 9. Current Limitations

- Intent detection and conversational responses are primarily rule-based; the current pipeline is not, by itself, a full large language model.
- Voice recognition accuracy varies with language, accent, microphone quality, noise, and the selected model.
- Not every natural-language request will map to a supported action.
- Some computer-control operations may be unavailable or deliberately disabled.
- Task planning does not guarantee that a task has executed successfully; action results must be checked.
- Full feature integration and final testing are still pending.

## 10. Development and Testing Plan

1. Complete the remaining module implementations.
2. Review imports and interfaces across all modules.
3. Verify command routing and action-result handling.
4. Test memory persistence and conversation context.
5. Test microphone recognition and spoken output.
6. Test supported application and file operations.
7. Check error handling, permissions, and cleanup.
8. Perform end-to-end testing before presenting the project as complete.

## 11. Project Goal

The long-term goal is to develop P.A.T into a reliable, friendly personal assistant that combines conversation, memory, voice interaction, planning, and safe computer automation.

**P.A.T — Personal AI Technology**
*Your personal assistant, built step by step.*
