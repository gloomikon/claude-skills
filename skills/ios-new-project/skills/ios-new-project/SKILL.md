---
name: ios-new-project
description: Create a new iOS project from KOMA template. Use when 
  user says "create a new iOS project", "start a new app", "new iOS app",
  or "create new project".
---
# Create New iOS Project from KOMA Template

## Steps
1. Ask for the project name if not provided
2. Create directory and init git:
```bash
   mkdir <ProjectName> && cd <ProjectName>
   git init
```
3. Download and run the template script:
```bash
   curl -fsSL https://raw.githubusercontent.com/KOMA-Inc/ProjectTemplateScript/main/create_project.sh -o create_project.sh
   chmod +x create_project.sh
   ./create_project.sh <ProjectName>
```
4. Set up Claude Code for the project — create `.claude/settings.json`:
```json
{
  "extraKnownMarketplaces": {
    "gloomikon-claude-skills": {
      "source": {
        "source": "github",
        "repo": "gloomikon/claude-skills"
      }
    }
  },
  "enabledPlugins": {
    "swiftui@gloomikon-claude-skills": true,
    "core-data@gloomikon-claude-skills": true
  }
}
```
5. Create `.claude/mcp.json`:
```json
{
  "mcpServers": {
    "apple-docs": {
      "command": "npx",
      "args": ["-y", "@kimsungwhee/apple-docs-mcp@latest"]
    }
  }
}
```
6. Remind the user to update placeholders:
   - `AppConstant.swift` — API keys for Amplitude and Adjust
   - `PurchaseManager.swift` — RevenueCat API key
   - `AppStorage.swift` — Keychain service name
   - `Configs/<ProjectName>/Common.xcconfig` — bundle identifier
   - `Resources/GoogleService-Info.plist` — Firebase config

## Notes
- Template clones ProjectTemplate, renames to match project name
- Sets bundle ID to `com.gloomikon.<projectname_lowercase>`
- Generates Xcode project via xcodegen
- Prerequisites: git, xcodegen (`brew install xcodegen`)
