# arivu-ai

This repository contains the source code and configuration for the `arivu-ai` project.

## Project Structure

- `app.py` — Main application script.
- `config.json` — Main configuration file (excluded from version control; see below).
- `config.sample.json` — Sample configuration file to use as a template for your own `config.json`.
- `data/` — Directory for data files (excluded from version control).

## Getting Started

1. **Clone the repository:**
   ```powershell
   git clone <repository-url>
   cd arivu-ai
   ```

2. **Set up configuration:**
   - Copy `config.sample.json` to `config.json` and update it with your settings.
   - `config.json` is ignored by git for security.

3. **Add data files:**
   - Place your data files in the `data/` directory. This folder is also git-ignored.

4. **Run the application:**
   ```powershell
   python app.py
   ```

## Notes
- Do not commit sensitive information in `config.json` or data files.
- Use `config.sample.json` as a reference for required configuration fields.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
