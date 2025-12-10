"""Computer use tool implementation for macOS."""

import base64
import io
import subprocess
import tempfile
import time
from pathlib import Path
from typing import List, Optional, Tuple

import pyautogui
from PIL import Image

# Configure pyautogui for safety
pyautogui.FAILSAFE = True  # Move mouse to corner to abort
pyautogui.PAUSE = 0.1  # Small pause between actions


class ComputerTool:
    """Handles computer use actions on macOS."""

    def __init__(self, display_width: int, display_height: int):
        self.display_width = display_width
        self.display_height = display_height

    def execute(self, action: str, **params) -> dict:
        """Execute a computer use action and return the result."""
        action_handlers = {
            "screenshot": self._screenshot,
            "left_click": self._left_click,
            "right_click": self._right_click,
            "middle_click": self._middle_click,
            "double_click": self._double_click,
            "triple_click": self._triple_click,
            "left_click_drag": self._left_click_drag,
            "mouse_move": self._mouse_move,
            "type": self._type_text,
            "key": self._key_press,
            "scroll": self._scroll,
            "wait": self._wait,
        }

        handler = action_handlers.get(action)
        if not handler:
            return {"error": f"Unknown action: {action}"}

        try:
            return handler(**params)
        except Exception as e:
            return {"error": f"Action '{action}' failed: {str(e)}"}

    def _validate_coordinates(self, x: int, y: int) -> Tuple[bool, Optional[str]]:
        """Validate that coordinates are within display bounds."""
        if not (0 <= x < self.display_width):
            return False, f"X coordinate {x} is outside display bounds (0-{self.display_width - 1})"
        if not (0 <= y < self.display_height):
            return False, f"Y coordinate {y} is outside display bounds (0-{self.display_height - 1})"
        return True, None

    def _screenshot(self, **_) -> dict:
        """Capture a screenshot and return it as base64-encoded JPEG."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            # Use macOS screencapture command
            result = subprocess.run(
                ["screencapture", "-x", "-C", tmp_path],
                capture_output=True,
                timeout=10,
            )

            if result.returncode != 0:
                return {"error": f"Screenshot failed: {result.stderr.decode()}"}

            # Open with Pillow and resize to configured dimensions
            # (Retina displays capture at 2x resolution)
            img = Image.open(tmp_path)
            img = img.resize(
                (self.display_width, self.display_height),
                Image.Resampling.LANCZOS
            )

            # Convert to RGB (JPEG doesn't support alpha channel)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            # Save as JPEG with compression
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=80, optimize=True)

            # If still too large (>4MB), reduce quality
            if buffer.tell() > 4_000_000:
                buffer = io.BytesIO()
                img.save(buffer, format="JPEG", quality=60, optimize=True)

            base64_image = base64.standard_b64encode(buffer.getvalue()).decode("utf-8")

            return {
                "type": "image",
                "media_type": "image/jpeg",
                "data": base64_image,
            }
        finally:
            # Clean up temp file
            Path(tmp_path).unlink(missing_ok=True)

    def _left_click(self, coordinate: Optional[List[int]] = None, **_) -> dict:
        """Perform a left click at the specified coordinates."""
        if coordinate is None:
            return {"error": "coordinate is required for left_click"}

        x, y = coordinate
        valid, error = self._validate_coordinates(x, y)
        if not valid:
            return {"error": error}

        pyautogui.click(x, y, button="left")
        return {"result": f"Left clicked at ({x}, {y})"}

    def _right_click(self, coordinate: Optional[List[int]] = None, **_) -> dict:
        """Perform a right click at the specified coordinates."""
        if coordinate is None:
            return {"error": "coordinate is required for right_click"}

        x, y = coordinate
        valid, error = self._validate_coordinates(x, y)
        if not valid:
            return {"error": error}

        pyautogui.click(x, y, button="right")
        return {"result": f"Right clicked at ({x}, {y})"}

    def _middle_click(self, coordinate: Optional[List[int]] = None, **_) -> dict:
        """Perform a middle click at the specified coordinates."""
        if coordinate is None:
            return {"error": "coordinate is required for middle_click"}

        x, y = coordinate
        valid, error = self._validate_coordinates(x, y)
        if not valid:
            return {"error": error}

        pyautogui.click(x, y, button="middle")
        return {"result": f"Middle clicked at ({x}, {y})"}

    def _double_click(self, coordinate: Optional[List[int]] = None, **_) -> dict:
        """Perform a double click at the specified coordinates."""
        if coordinate is None:
            return {"error": "coordinate is required for double_click"}

        x, y = coordinate
        valid, error = self._validate_coordinates(x, y)
        if not valid:
            return {"error": error}

        pyautogui.doubleClick(x, y)
        return {"result": f"Double clicked at ({x}, {y})"}

    def _triple_click(self, coordinate: Optional[List[int]] = None, **_) -> dict:
        """Perform a triple click at the specified coordinates."""
        if coordinate is None:
            return {"error": "coordinate is required for triple_click"}

        x, y = coordinate
        valid, error = self._validate_coordinates(x, y)
        if not valid:
            return {"error": error}

        pyautogui.tripleClick(x, y)
        return {"result": f"Triple clicked at ({x}, {y})"}

    def _left_click_drag(
        self,
        start_coordinate: Optional[List[int]] = None,
        coordinate: Optional[List[int]] = None,
        **_,
    ) -> dict:
        """Perform a click and drag from start to end coordinates."""
        if start_coordinate is None or coordinate is None:
            return {"error": "start_coordinate and coordinate are required for left_click_drag"}

        start_x, start_y = start_coordinate
        end_x, end_y = coordinate

        valid, error = self._validate_coordinates(start_x, start_y)
        if not valid:
            return {"error": f"Start {error}"}

        valid, error = self._validate_coordinates(end_x, end_y)
        if not valid:
            return {"error": f"End {error}"}

        pyautogui.moveTo(start_x, start_y)
        pyautogui.drag(end_x - start_x, end_y - start_y, duration=0.5)
        return {"result": f"Dragged from ({start_x}, {start_y}) to ({end_x}, {end_y})"}

    def _mouse_move(self, coordinate: Optional[List[int]] = None, **_) -> dict:
        """Move the mouse cursor to the specified coordinates."""
        if coordinate is None:
            return {"error": "coordinate is required for mouse_move"}

        x, y = coordinate
        valid, error = self._validate_coordinates(x, y)
        if not valid:
            return {"error": error}

        pyautogui.moveTo(x, y)
        return {"result": f"Moved mouse to ({x}, {y})"}

    def _type_text(self, text: Optional[str] = None, **_) -> dict:
        """Type the specified text."""
        if text is None:
            return {"error": "text is required for type"}

        # Use pyautogui's typewrite for ASCII, write for unicode
        pyautogui.write(text, interval=0.02)
        return {"result": f"Typed: {text[:50]}{'...' if len(text) > 50 else ''}"}

    def _key_press(self, key: Optional[str] = None, **_) -> dict:
        """Press a key or key combination."""
        if key is None:
            return {"error": "key is required for key action"}

        # Handle key combinations like "ctrl+c", "cmd+v", etc.
        keys = key.lower().replace("ctrl", "command").split("+")

        if len(keys) == 1:
            # Single key press
            pyautogui.press(keys[0])
        else:
            # Key combination - hold modifiers and press the last key
            pyautogui.hotkey(*keys)

        return {"result": f"Pressed key: {key}"}

    def _scroll(
        self,
        coordinate: Optional[List[int]] = None,
        scroll_direction: Optional[str] = None,
        scroll_amount: int = 3,
        **_,
    ) -> dict:
        """Scroll at the specified coordinates."""
        if coordinate is None:
            return {"error": "coordinate is required for scroll"}
        if scroll_direction is None:
            return {"error": "scroll_direction is required for scroll"}

        x, y = coordinate
        valid, error = self._validate_coordinates(x, y)
        if not valid:
            return {"error": error}

        # Move to position first
        pyautogui.moveTo(x, y)

        # Determine scroll direction
        if scroll_direction == "up":
            pyautogui.scroll(scroll_amount)
        elif scroll_direction == "down":
            pyautogui.scroll(-scroll_amount)
        elif scroll_direction == "left":
            pyautogui.hscroll(-scroll_amount)
        elif scroll_direction == "right":
            pyautogui.hscroll(scroll_amount)
        else:
            return {"error": f"Invalid scroll direction: {scroll_direction}"}

        return {"result": f"Scrolled {scroll_direction} by {scroll_amount} at ({x}, {y})"}

    def _wait(self, duration: float = 1.0, **_) -> dict:
        """Wait for the specified duration in seconds."""
        time.sleep(duration)
        return {"result": f"Waited {duration} seconds"}

    def describe_action(self, action: str, **params) -> str:
        """Get a human-readable description of an action."""
        if action == "screenshot":
            return "Take a screenshot"
        elif action == "left_click":
            coord = params.get("coordinate", [0, 0])
            return f"Left click at ({coord[0]}, {coord[1]})"
        elif action == "right_click":
            coord = params.get("coordinate", [0, 0])
            return f"Right click at ({coord[0]}, {coord[1]})"
        elif action == "double_click":
            coord = params.get("coordinate", [0, 0])
            return f"Double click at ({coord[0]}, {coord[1]})"
        elif action == "mouse_move":
            coord = params.get("coordinate", [0, 0])
            return f"Move mouse to ({coord[0]}, {coord[1]})"
        elif action == "type":
            text = params.get("text", "")
            preview = text[:30] + "..." if len(text) > 30 else text
            return f"Type: '{preview}'"
        elif action == "key":
            return f"Press key: {params.get('key', '')}"
        elif action == "scroll":
            direction = params.get("scroll_direction", "down")
            amount = params.get("scroll_amount", 3)
            return f"Scroll {direction} by {amount}"
        elif action == "wait":
            return f"Wait {params.get('duration', 1.0)} seconds"
        elif action == "left_click_drag":
            start = params.get("start_coordinate", [0, 0])
            end = params.get("coordinate", [0, 0])
            return f"Drag from ({start[0]}, {start[1]}) to ({end[0]}, {end[1]})"
        else:
            return f"Unknown action: {action}"
