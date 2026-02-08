# ORIGINAL PROJECT CONVENTIONS (Kiro AI Agent)

> **Note**: This is the original project conventions document created by the Kiro AI agent during initial system development. These conventions represent early project-specific rules and settings.
>
> **Date**: Original design phase
> **Status**: Historical reference - may have been superseded by current practices

---

# Project Conventions and System-Specific Rules

## 🚨 FIRST ACTION IN EVERY CONTEXT WINDOW
**ALWAYS READ `START_HERE.md` FIRST** - It contains the most current project state, critical commands, and system-specific rules.

## Python Command
**CRITICAL**: On this Windows system, ALWAYS use `py` (not `python` or `python3`) as the command to run Python scripts.

This is documented in START_HERE.md and must be followed without exception.

Example:
```powershell
py script.py
py -m pip install package
```

## File Path Handling
When working with file paths that contain special characters (brackets `[]`, parentheses `()`, etc.), use .NET methods instead of PowerShell cmdlets to avoid wildcard interpretation issues:

- Use `[System.IO.File]::Copy()` instead of `Copy-Item`
- Use `[System.IO.Directory]::CreateDirectory()` instead of `New-Item -ItemType Directory`
- Use `[System.IO.Path]::GetDirectoryName()` instead of `Split-Path`

## AWS Configuration
- **S3 Bucket**: `jsmith-output`
- **AWS Profile**: `default` (requires SSO login: `aws sso login --profile default`)

## Project Structure
Sheet music files are organized as:
```
<artist>\<book title>\<artist> - <song title>.pdf
```

**Important**: NO "books" subfolder in the structure.

## Artist Name Rules
- For single-artist books: Use the book-level artist from the folder name (e.g., "ACDC")
- For Various Artists/Fake Books/Broadway/Movie collections: Use song-level artist names from the sheet music
