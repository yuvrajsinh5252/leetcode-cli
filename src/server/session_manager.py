import json
from pathlib import Path
from typing import Dict, Optional

import typer


class SessionManager:
    def __init__(self):
        self.config_dir = Path(typer.get_app_dir("leetcode-cli"))
        self.config_file = self.config_dir / "session.json"
        self._ensure_config_dir()

    def _ensure_config_dir(self):
        """Ensure the config directory exists"""
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def save_session(self, csrftoken: str, session_token: str, user_name: str):
        """Save the session token and username to file"""
        data = {
            "csrftoken": csrftoken,
            "session_token": session_token,
            "user_name": user_name,
        }
        with open(self.config_file, "w") as f:
            json.dump(data, f)

    def load_session(self) -> Optional[Dict[str, str]]:
        """Load the session token and username from file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, "r") as f:
                    return json.load(f)
        except Exception:
            pass
        return None

    def clear_session(self):
        """Clear the stored session"""
        if self.config_file.exists():
            self.config_file.unlink()
