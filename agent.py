"""Agent loop for computer use interactions with Claude."""

from anthropic import Anthropic

from config import Config
from tools.computer import ComputerTool


class ComputerUseAgent:
    """Agent that interacts with Claude API for computer use tasks."""

    def __init__(self, config: Config, confirm_callback=None):
        """
        Initialize the agent.

        Args:
            config: Configuration settings
            confirm_callback: Optional callback function that receives action description
                              and returns True to execute, False to skip, or raises
                              StopIteration to quit.
        """
        self.config = config
        self.client = Anthropic(api_key=config.api_key)
        self.computer = ComputerTool(config.display_width, config.display_height)
        self.confirm_callback = confirm_callback
        self.messages: list[dict] = []

    def _get_tools(self) -> list[dict]:
        """Get the tool definitions for the API request."""
        return [
            {
                "type": self.config.tool_version,
                "name": "computer",
                "display_width_px": self.config.display_width,
                "display_height_px": self.config.display_height,
            }
        ]

    def _create_tool_result(self, tool_use_id: str, result: dict) -> dict:
        """Create a tool result message."""
        if "error" in result:
            return {
                "type": "tool_result",
                "tool_use_id": tool_use_id,
                "content": result["error"],
                "is_error": True,
            }

        # Handle image results (screenshots)
        if result.get("type") == "image":
            return {
                "type": "tool_result",
                "tool_use_id": tool_use_id,
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": result["media_type"],
                            "data": result["data"],
                        },
                    }
                ],
            }

        # Handle text results
        return {
            "type": "tool_result",
            "tool_use_id": tool_use_id,
            "content": result.get("result", "Action completed"),
        }

    def _process_tool_calls(self, response_content: list) -> list[dict]:
        """Process tool calls from Claude's response."""
        tool_results = []

        for block in response_content:
            if block.type != "tool_use":
                continue

            tool_name = block.name
            tool_input = block.input
            tool_id = block.id

            if tool_name != "computer":
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_id,
                    "content": f"Unknown tool: {tool_name}",
                    "is_error": True,
                })
                continue

            action = tool_input.get("action", "")
            action_params = {k: v for k, v in tool_input.items() if k != "action"}

            # Get action description for logging/confirmation
            action_desc = self.computer.describe_action(action, **action_params)

            # Check for confirmation if callback provided
            if self.confirm_callback and action != "screenshot":
                try:
                    should_execute = self.confirm_callback(action_desc)
                    if not should_execute:
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": "Action skipped by user",
                        })
                        continue
                except StopIteration:
                    # User wants to quit
                    raise

            # Execute the action
            print(f"  Executing: {action_desc}")
            result = self.computer.execute(action, **action_params)
            tool_results.append(self._create_tool_result(tool_id, result))

        return tool_results

    def run(self, task: str) -> str:
        """
        Run the agent loop for a given task.

        Args:
            task: The task description for Claude to complete

        Returns:
            The final text response from Claude
        """
        # Initialize messages with the user task
        self.messages = [{"role": "user", "content": task}]

        # Add system prompt for better guidance
        system_prompt = """You are a computer use assistant that can control a macOS computer.
When performing tasks:
1. Always take a screenshot first to see the current state of the screen.
2. After each action, take another screenshot to verify the result.
3. Be precise with click coordinates - aim for the center of buttons and UI elements.
4. If something doesn't work, try alternative approaches.
5. Report your progress and any issues you encounter.
"""

        iterations = 0
        final_response = ""

        print(f"\nStarting agent with task: {task}")
        print(f"Screen dimensions: {self.config.display_width}x{self.config.display_height}")
        print("-" * 50)

        while iterations < self.config.max_iterations:
            iterations += 1
            print(f"\n[Iteration {iterations}/{self.config.max_iterations}]")

            # Call Claude API
            try:
                response = self.client.beta.messages.create(
                    model=self.config.model,
                    max_tokens=self.config.max_tokens,
                    system=system_prompt,
                    tools=self._get_tools(),
                    messages=self.messages,
                    betas=[self.config.beta_flag],
                )
            except Exception as e:
                print(f"API Error: {e}")
                return f"API Error: {e}"

            # Add assistant response to messages
            self.messages.append({"role": "assistant", "content": response.content})

            # Print any text response
            for block in response.content:
                if hasattr(block, "text"):
                    print(f"\nClaude: {block.text}")
                    final_response = block.text

            # Check if Claude is done (no tool use)
            if response.stop_reason == "end_turn":
                print("\n[Task completed]")
                break

            # Process tool calls
            try:
                tool_results = self._process_tool_calls(response.content)
            except StopIteration:
                print("\n[User quit]")
                break

            if not tool_results:
                print("\n[No more tool calls]")
                break

            # Add tool results to messages
            self.messages.append({"role": "user", "content": tool_results})

        if iterations >= self.config.max_iterations:
            print(f"\n[Max iterations ({self.config.max_iterations}) reached]")

        return final_response

    def get_conversation_log(self) -> list[dict]:
        """Get the full conversation log."""
        return self.messages
