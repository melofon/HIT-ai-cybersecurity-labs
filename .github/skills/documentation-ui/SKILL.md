---
name: documentation-ui
description: >
  Use this skill for documentation and ui. Triggers on: markdown files, documentation, user interfaces, comments, prompts.
---

## Purpose
Ensure that all user interfaces and documentation in this repository are written in English only.

## Workflow
1. When creating or editing any documentation (README, instructions, comments, etc.), write exclusively in English.
2. When implementing user interfaces (web, CLI, agent messages), ensure all prompts, labels, and outputs are in English.
3. If you find any Russian or non-English text, translate it to English and update the file.
4. Review pull requests and code reviews for language compliance.
5. If a new file or feature is added, check that all user-facing text is in English.

## Completion Criteria
- No non-English text remains in documentation or user interfaces.
- All new contributions follow the English-only rule.

## Example Prompts
- "Check if all documentation and UI messages are in English."
- "Translate all comments and user-facing text to English."
- "Review this PR for English-only compliance."

## Related Customizations
- Add a pre-commit hook to scan for non-English text.
- Add a CI check for language compliance in documentation and UI.

---
**All user interfaces, comments and documentation in this repository must be in English.**
