# Setting Up VS Code and GitHub Copilot for Semantic Commits

This guide will help you set up VS Code and GitHub Copilot to work with semantic commits in the hms_tz app.

## Prerequisites

- VS Code installed
- GitHub Copilot extension installed and configured
- Git installed and configured

## Installation Steps

### 1. Install Required VS Code Extensions

Install the following extensions in VS Code:

- **Conventional Commits** by vivaxy (extension ID: `vivaxy.vscode-conventional-commits`)
- **GitHub Copilot** by GitHub (extension ID: `GitHub.copilot`)
- **GitHub Copilot Chat** by GitHub (extension ID: `GitHub.copilot-chat`)

You can install these extensions by:
1. Opening VS Code
2. Going to the Extensions view (Ctrl+Shift+X)
3. Searching for each extension by name
4. Clicking "Install"

### 2. Configure VS Code Settings

The `.vscode/settings.json` file has been updated with the following configurations:

```json
{
    // Git commit message settings
    "git.inputValidationSubjectLength": 72,
    "git.inputValidationLength": 500,
    "git.inputValidation": "always",
    
    // Conventional Commits settings
    "conventionalCommits.scopes": [
        "nhif",
        "healthcare",
        "patient",
        "billing",
        "ui",
        "api",
        "config",
        "docs"
    ],
    "conventionalCommits.gitmoji": false,
    
    // GitHub Copilot settings
    "github.copilot.enable": {
        "*": true,
        "plaintext": true,
        "markdown": true,
        "scminput": true  // Enable Copilot for commit messages
    }
}
```

These settings:
- Enable input validation for Git commit messages
- Define scopes for conventional commits
- Enable GitHub Copilot for commit messages

### 3. Using Semantic Commits with VS Code

#### Method 1: Using the Conventional Commits Extension

1. Stage your changes in Git
2. Click on the Source Control icon in VS Code
3. Instead of typing a commit message directly, click on the "Conventional Commits" icon (usually appears near the commit message input)
4. Follow the prompts to select:
   - Type of change (feat, fix, docs, etc.)
   - Scope (optional)
   - Short description
   - Body (optional)
   - Breaking changes (optional)
   - Issues closed (optional)

#### Method 2: Using GitHub Copilot

1. Stage your changes in Git
2. Click on the Source Control icon in VS Code
3. Start typing a commit message
4. GitHub Copilot will suggest completions based on your changes and commit history
5. Make sure the suggestions follow the semantic commit format: `type(scope): description`
6. Accept suggestions that match the semantic commit format

### 4. Valid Commit Types

Based on our commitlint.config.js, the following types are allowed:

- `build`: Changes that affect the build system or external dependencies
- `chore`: Routine tasks, maintenance, or refactors that don't change production code
- `ci`: Changes to CI configuration files and scripts
- `docs`: Documentation only changes
- `feat`: A new feature
- `fix`: A bug fix
- `perf`: A code change that improves performance
- `refactor`: A code change that neither fixes a bug nor adds a feature
- `revert`: Reverting a previous commit
- `style`: Changes that do not affect the meaning of the code (white-space, formatting, etc.)
- `test`: Adding missing tests or correcting existing tests
- `patch`: Small patches or adjustments to existing functionality

## Troubleshooting

### Husky Hooks Not Running

If husky hooks are not running when you commit from VS Code:

1. Make sure husky is properly installed:
   ```bash
   cd hms_tz
   npm install husky --save-dev
   npm run prepare
   ```

2. Check if the commit-msg hook is executable:
   ```bash
   chmod +x .husky/commit-msg
   ```

### GitHub Copilot Not Suggesting Semantic Commits

If GitHub Copilot is not suggesting semantic commits:

1. Make sure the `scminput` setting is enabled in your VS Code settings
2. Try providing a partial commit message that follows the semantic format, e.g., `feat: `
3. Review your recent commit history to ensure you have examples of semantic commits

## Resources

- [Conventional Commits Specification](https://www.conventionalcommits.org/)
- [GitHub Copilot Documentation](https://docs.github.com/en/copilot)
- [Husky Documentation](https://typicode.github.io/husky/)
