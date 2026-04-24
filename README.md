# BD Agent Web Interface

A simple web interface for the Business Development meeting preparation agent.

## Features

- Clean, modern web interface with Hebrew support
- Dropdown selection of clients
- Real-time meeting preparation summaries in Hebrew
- Responsive design that works on mobile and desktop

## Quick Start

### Option 1: Run Script (Windows)
Double-click `run.bat` to start the application.

### Option 2: Command Line
1. Make sure you have Python 3.7+ installed
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the Flask application:
   ```bash
   python app.py
   ```

## Usage

1. Open your web browser and go to `http://localhost:5000`
2. Select a client from the dropdown menu
3. Click "הכן סיכום פגישה" (Prepare Meeting Summary)
4. The summary will appear below with:
   - Last meeting date
   - Products the client sells
   - Open issues
   - Preparation suggestions

## Project Structure

- `app.py` - Flask web application
- `run.bat` - Windows batch file to start the app
- `agent/agent.py` - Original command-line agent
- `data/clients.json` - Client data
- `requirements.txt` - Python dependencies
- `README.md` - This documentation