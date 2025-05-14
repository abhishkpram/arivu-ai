# arivu-ai

**arivu-ai** is a Flask-based web application for comparing YouTube channels and visualizing channel statistics, including subscriber history and comment sentiment analysis.

---

## Features

- **Get Info Page:**
  - Enter a YouTube username or @handle to view detailed channel information.
  - Displays all available YouTube API stats: title, description, custom URL, published date, country, subscriber count, view count, video count, privacy status, topic categories, branding, and more.
  - Shows a subscriber count history graph (if data is available).
  - Fetches and summarizes comments from the latest 50 videos, providing a sentiment-based comments summary (positive/negative/neutral).
  - All API results are cached in the `data/` folder and only refreshed when you click the "Refresh" button.

- **Compare Page:**
  - Compare two YouTube channels side-by-side on all available stats.
  - Winner is calculated for each stat (including correct logic for older channel as winner for published date).
  - UI/UX is modern, clean, and consistent, with a header bar for navigation and a back button.

- **Navigation:**
  - Header bar with navigation buttons for "Get Info", "Compare", and a back button.
  - Only two main pages: Get Info and Compare.

---

## Project Structure

- `app.py` — Main Flask application (all UI, logic, and API integration).
- `config.json` — Main configuration file (contains your YouTube API key; not committed).
- `config.sample.json` — Sample config file to copy and edit.
- `data/` — Stores all cached API results, channel data, and subscriber history.
- `README.md` — This file.
- `LICENSE` — MIT License.

---

## Getting Started

1. **Clone the repository:**
   ```powershell
   git clone <repository-url>
   cd arivu-ai
   ```

2. **Set up configuration:**
   - Copy `config.sample.json` to `config.json` and add your YouTube Data API key.
   - Example:
     ```json
     {
       "YOUTUBE_API_KEY": "YOUR_API_KEY_HERE"
     }
     ```

3. **Run the application:**
   ```powershell
   python app.py
   ```
   The app will be available at `http://127.0.0.1:5000/`.

---

## Usage

- **Get Info:**
  - Enter a YouTube username or @handle and click "Get Info".
  - View all channel stats, subscriber history graph, and comments summary.
  - Click "Refresh" to update data from the API and append to subscriber history.

- **Compare:**
  - After loading a channel, enter another username in the "Compare with..." box and click "Compare".
  - See a detailed, side-by-side comparison of all stats.
  - Use the navigation bar to switch between pages or go back.

---

## Notes
- All API results and stats are cached in the `data/` folder for performance and to avoid unnecessary API calls.
- Comments summary is based on simple keyword sentiment analysis of the latest 50 videos' comments.
- The UI is fully responsive and works well on desktop and mobile.
- Do not commit sensitive information in `config.json` or data files.

---

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
