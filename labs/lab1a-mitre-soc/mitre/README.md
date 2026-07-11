# MITRE ATT&CK knowledge files

The project works offline with `enterprise-attack-mini.json`, a small STIX-style bundle containing the two techniques used in Lab 1a.

To use the complete official Enterprise ATT&CK knowledge base, run from PowerShell:

```powershell
.\download_attack_data.ps1
```

This downloads `enterprise-attack.json` from the official MITRE ATT&CK STIX data repository. The detector prefers the full file when it exists and otherwise uses the bundled mini file.
