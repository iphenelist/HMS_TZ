# Semantic Commit Messages Guide

## Format
```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

## Types
- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, semicolons, etc.)
- `refactor`: Code changes that neither fix bugs nor add features
- `test`: Adding or modifying tests
- `chore`: Changes to the build process, tools, etc.
- `perf`: Performance improvements
- `build`: Changes to build system or external dependencies
- `ci`: Changes to CI configuration files and scripts
- `revert`: Revert a previous commit
- `patch`: Small patches or adjustments

## Scope
The scope is optional and can be anything specifying the place of the commit change, e.g., `nhif`, `patient`, `appointment`, etc.

## Examples
- `feat(nhif): add integration with NHIF API`
- `fix(patient): resolve issue with patient registration`
- `docs: update README with new installation instructions`
- `style: format code according to style guide`
- `refactor(appointment): simplify appointment scheduling logic`
- `test(lab): add tests for lab result processing`
- `chore: update dependencies`

## Why Use Semantic Commits?
1. **Automatic Versioning**: Enables tools to automatically determine version numbers
2. **Automatic Changelog Generation**: Makes it easy to generate changelogs
3. **Clear Communication**: Helps team members understand the purpose of changes
4. **Easier Code Reviews**: Makes it clear what the intention of the change is
5. **Better History**: Makes the project history more navigable and useful

## Installation
The project is set up with commitlint and husky to enforce semantic commit messages. When you try to commit, your commit message will be checked against the semantic commit format.

To install the necessary dependencies:
```bash
cd hms_tz
npm install
```

This will install commitlint and husky, which will enforce semantic commit messages.
