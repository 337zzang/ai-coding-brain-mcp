"""
token_optimizer.py - Optimize action sequences for minimal token usage
"""

import json
from typing import List, Dict, Any
import re

class TokenOptimizer:
    """Optimize action sequences to reduce token consumption"""

    def __init__(self):
        self.abbreviations = {
            "click": "C",
            "type": "T",
            "select": "S",
            "wait": "W",
            "scroll": "SC",
            "hover": "H",
            "screenshot": "SS"
        }

        self.selector_patterns = {
            r'#([a-zA-Z0-9_-]+)': r'#',  # ID selectors
            r'\.([a-zA-Z0-9_-]+)': r'.',  # Class selectors
            r'button\[type=['"]?submit['"]?\]': 'submit-btn',  # Common button
            r'input\[type=['"]?text['"]?\]': 'text-input',  # Text input
            r'input\[type=['"]?password['"]?\]': 'pwd-input',  # Password input
        }

    def compress_action(self, action: Dict[str, Any]) -> str:
        """Compress single action to minimal representation"""
        action_type = self.abbreviations.get(action["type"], action["type"])
        target = self._compress_target(action.get("target", {}))

        if action["type"] == "type":
            value = action.get("value", "")
            return f"{action_type}:{target}='{value}'"
        elif action["type"] == "wait":
            delay = action.get("options", {}).get("delay", 1000)
            return f"{action_type}:{delay}ms"
        else:
            return f"{action_type}:{target}"

    def _compress_target(self, target: Dict[str, Any]) -> str:
        """Compress target selector"""
        if target.get("selector"):
            selector = target["selector"]
            # Apply pattern replacements
            for pattern, replacement in self.selector_patterns.items():
                selector = re.sub(pattern, replacement, selector)
            return selector
        elif target.get("text"):
            return f"txt:'{target['text']}'"
        elif target.get("position"):
            return f"pos:{target['position']['x']},{target['position']['y']}"
        return "?"

    def compress_sequence(self, sequence: Dict[str, Any]) -> str:
        """Compress entire action sequence"""
        compressed_actions = []
        for i, action in enumerate(sequence.get("actions", []), 1):
            compressed = self.compress_action(action)
            compressed_actions.append(f"{i}.{compressed}")

        return ";".join(compressed_actions)

    def expand_compressed(self, compressed: str) -> List[str]:
        """Expand compressed format for readability"""
        actions = compressed.split(";")
        expanded = []

        reverse_abbr = {v: k for k, v in self.abbreviations.items()}

        for action in actions:
            parts = action.split(".", 1)
            if len(parts) == 2:
                step_num, action_str = parts
                action_parts = action_str.split(":", 1)
                if len(action_parts) == 2:
                    action_type = reverse_abbr.get(action_parts[0], action_parts[0])
                    target = action_parts[1]

                    if "=" in target:
                        target, value = target.split("=", 1)
                        expanded.append(f"Step {step_num}: {action_type} '{value.strip("'")}' in {target}")
                    else:
                        expanded.append(f"Step {step_num}: {action_type} {target}")

        return expanded

    def calculate_savings(self, original: str, compressed: str) -> Dict[str, Any]:
        """Calculate token and character savings"""
        original_chars = len(original)
        compressed_chars = len(compressed)

        # Approximate token count (rough estimate)
        original_tokens = len(original.split()) + len(json.dumps(json.loads(original)).split(","))
        compressed_tokens = len(compressed.split(";")) * 2  # Rough estimate

        return {
            "original_chars": original_chars,
            "compressed_chars": compressed_chars,
            "char_reduction": f"{(1 - compressed_chars/original_chars) * 100:.1f}%",
            "original_tokens_estimate": original_tokens,
            "compressed_tokens_estimate": compressed_tokens,
            "token_reduction_estimate": f"{(1 - compressed_tokens/original_tokens) * 100:.1f}%"
        }

# Example usage
def demonstrate_optimization():
    """Demonstrate token optimization"""
    sample_sequence = {
        "version": "1.0.0",
        "session_id": "demo_001",
        "actions": [
            {
                "type": "click",
                "target": {"selector": "#username"},
                "overlay": {"color": "blue", "label": "Click username"}
            },
            {
                "type": "type",
                "target": {"selector": "#username"},
                "value": "demo_user"
            },
            {
                "type": "click",
                "target": {"selector": "#password"}
            },
            {
                "type": "type",
                "target": {"selector": "#password"},
                "value": "secure_password"
            },
            {
                "type": "click",
                "target": {"selector": "button[type='submit']"}
            },
            {
                "type": "wait",
                "options": {"delay": 2000}
            }
        ]
    }

    optimizer = TokenOptimizer()

    # Original JSON
    original = json.dumps(sample_sequence, indent=2)

    # Compressed format
    compressed = optimizer.compress_sequence(sample_sequence)

    # Calculate savings
    savings = optimizer.calculate_savings(original, compressed)

    print("Original JSON length:", len(original), "characters")
    print("Compressed format:", compressed)
    print("Compressed length:", len(compressed), "characters")
    print("Savings:", savings)

    # Expand for readability
    expanded = optimizer.expand_compressed(compressed)
    print("\nHuman-readable expansion:")
    for action in expanded:
        print(f"  {action}")

    return compressed, savings

if __name__ == "__main__":
    demonstrate_optimization()
