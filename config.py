"""Configuration settings for the computer-use MVP."""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Load .env.local from the project directory
_env_file = Path(__file__).parent / ".env.local"
if _env_file.exists():
    load_dotenv(_env_file)


def get_screen_dimensions() -> tuple[int, int]:
    """Get the primary screen dimensions on macOS."""
    try:
        from Quartz import CGDisplayBounds, CGMainDisplayID

        main_display = CGMainDisplayID()
        bounds = CGDisplayBounds(main_display)
        width = int(bounds.size.width)
        height = int(bounds.size.height)
        return width, height
    except ImportError:
        # Fallback to reasonable defaults
        return 1920, 1080


@dataclass
class Config:
    """Configuration for the computer-use agent."""

    # API settings
    api_key: str = field(default_factory=lambda: os.environ.get("ANTHROPIC_API_KEY", ""))
    model: str = "claude-sonnet-4-5"
    beta_flag: str = "computer-use-2025-01-24"
    tool_version: str = "computer_20250124"

    # Display settings (auto-detected)
    display_width: int = field(default_factory=lambda: get_screen_dimensions()[0])
    display_height: int = field(default_factory=lambda: get_screen_dimensions()[1])

    # Agent settings
    max_tokens: int = 4096
    max_iterations: int = 10

    # Safety settings
    confirm_actions: bool = True

    def __post_init__(self):
        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found. "
                "Set it in .env.local file or as environment variable."
            )


# Default configuration instance
def get_config(**overrides) -> Config:
    """Get configuration with optional overrides."""
    return Config(**overrides)
