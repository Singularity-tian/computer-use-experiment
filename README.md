# Computer Use MVP

A CLI tool that lets Claude control your Mac using the computer-use capability.

## Setup

1. **Install dependencies**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure API key**

   Create a `.env.local` file:
   ```bash
   ANTHROPIC_API_KEY='your-api-key-here'
   ```

3. **Grant permissions**

   On first run, macOS will ask for:
   - Screen Recording permission (for screenshots)
   - Accessibility permission (for mouse/keyboard control)

   Go to System Settings > Privacy & Security to enable these.

## Usage

```bash
# Activate virtual environment
source venv/bin/activate

# Run a task (with confirmation prompts)
python main.py "Open TextEdit and type 'Hello World'"

# Run without confirmations (faster but less safe)
python main.py --no-confirm "Take a screenshot"

# Interactive mode
python main.py --interactive

# Use a different model
python main.py --model claude-opus-4-5 "Your task here"

# Set max iterations
python main.py --max-iterations 20 "Complex task"
```

## Safety

- **Confirmations enabled by default**: Each action requires `y/n/q` confirmation
- **Failsafe**: Move mouse to any corner to abort (pyautogui failsafe)
- **Ctrl+C**: Press anytime to stop the agent
- **Max iterations**: Default limit of 10 iterations per task
