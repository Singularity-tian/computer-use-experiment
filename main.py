#!/usr/bin/env python3
"""CLI entry point for the computer-use MVP."""

import argparse
import sys

from agent import ComputerUseAgent
from config import get_config


def confirm_action(action_desc: str) -> bool:
    """
    Prompt user to confirm an action.

    Returns True to execute, False to skip.
    Raises StopIteration to quit.
    """
    while True:
        response = input(f"\n  [Action] {action_desc}\n  Confirm? [y/n/q]: ").lower().strip()
        if response == "y":
            return True
        elif response == "n":
            print("  Skipped.")
            return False
        elif response == "q":
            raise StopIteration
        else:
            print("  Please enter 'y' (yes), 'n' (no), or 'q' (quit)")


def interactive_mode(agent: ComputerUseAgent):
    """Run the agent in interactive mode."""
    print("\n=== Computer Use Agent - Interactive Mode ===")
    print("Enter tasks for Claude to perform. Type 'quit' or 'exit' to stop.\n")

    while True:
        try:
            task = input("Task: ").strip()
            if not task:
                continue
            if task.lower() in ("quit", "exit"):
                print("Goodbye!")
                break

            agent.run(task)
            print("\n" + "=" * 50 + "\n")

        except KeyboardInterrupt:
            print("\n\nInterrupted. Goodbye!")
            break
        except EOFError:
            print("\nGoodbye!")
            break


def main():
    parser = argparse.ArgumentParser(
        description="Computer Use MVP - Let Claude control your Mac",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py "Take a screenshot"
  python main.py "Open Safari and search for Claude AI"
  python main.py --interactive
  python main.py --no-confirm "Open TextEdit"

Safety:
  By default, you'll be asked to confirm each action.
  Use --no-confirm to skip confirmations (use with caution).
  Press Ctrl+C at any time to stop.
        """,
    )

    parser.add_argument(
        "task",
        nargs="?",
        help="Task for Claude to perform (omit for interactive mode)",
    )
    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Run in interactive mode",
    )
    parser.add_argument(
        "--no-confirm",
        action="store_true",
        help="Skip action confirmations (faster but less safe)",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=10,
        help="Maximum number of agent iterations (default: 10)",
    )
    parser.add_argument(
        "--model",
        default="claude-sonnet-4-5",
        choices=["claude-sonnet-4-5", "claude-opus-4-5"],
        help="Claude model to use (default: claude-sonnet-4-5)",
    )

    args = parser.parse_args()

    # Get configuration
    try:
        config = get_config(
            max_iterations=args.max_iterations,
            model=args.model,
            confirm_actions=not args.no_confirm,
        )
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    print(f"Screen: {config.display_width}x{config.display_height}")
    print(f"Model: {config.model}")
    print(f"Confirmations: {'disabled' if args.no_confirm else 'enabled'}")

    # Create agent with optional confirmation callback
    confirm_callback = confirm_action if not args.no_confirm else None
    agent = ComputerUseAgent(config, confirm_callback=confirm_callback)

    # Run in appropriate mode
    if args.interactive or not args.task:
        interactive_mode(agent)
    else:
        try:
            agent.run(args.task)
        except KeyboardInterrupt:
            print("\n\nInterrupted. Goodbye!")
            sys.exit(130)


if __name__ == "__main__":
    main()
