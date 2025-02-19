from typing import Dict
import requests
from .session_manager import SessionManager

class Auth:
    def __init__(self):
        self.session = requests.Session()
        self.BASE_URL = "https://leetcode.com"
        self.is_authenticated = False
        self.session_manager = SessionManager()
        self._load_saved_session()

    def _load_saved_session(self):
        """Try to load and validate saved session"""
        saved_session = self.session_manager.load_session()
        if saved_session:
            result = self.login_with_session(saved_session['session_token'])
            return result["success"]
        return False

    def login_with_session(self, leetcode_session: str) -> Dict[str, any]: # type: ignore
        """
        Login to LeetCode using LEETCODE_SESSION token.
        Returns a dictionary with success status and message.
        """
        try:
            self.session.cookies.set('LEETCODE_SESSION', leetcode_session, domain='leetcode.com')

            response = self.session.get(
                f"{self.BASE_URL}/api/problems/all/",
                headers={
                    'Accept': 'application/json',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )

            if response.status_code == 200:
                user_data = response.json()
                if user_data.get('user_name'):
                    self.is_authenticated = True
                    # Save the valid session
                    self.session_manager.save_session(leetcode_session, user_data['user_name'])
                    return {
                        "success": True,
                        "message": "Successfully logged in",
                        "user_name": user_data['user_name']
                    }
                else:
                    self.session_manager.clear_session()
                    return {
                        "success": False,
                        "message": "Invalid session token"
                    }
            else:
                self.session_manager.clear_session()
                return {
                    "success": False,
                    "message": f"Login failed with status code: {response.status_code}"
                }

        except Exception as e:
            self.session_manager.clear_session()
            return {"success": False, "message": f"Login error: {str(e)}"}

    def get_session(self) -> requests.Session:
        """Return the authenticated session."""
        return self.session