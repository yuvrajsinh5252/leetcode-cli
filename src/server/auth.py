from typing import Any, Dict

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
            result = self.login_with_session(
                saved_session["csrftoken"], saved_session["session_token"]
            )
            return result["success"]
        return False

    def verify_csrf_token(self, csrf_token: str) -> Dict[str, Any]:
        """Verify CSRF token by making a request to LeetCode's GraphQL endpoint"""
        try:
            if not csrf_token:
                return {"success": False, "message": "CSRF token is required"}

            self.session.cookies.set("csrftoken", csrf_token, domain="leetcode.com")

            response = self.session.post(
                f"{self.BASE_URL}/graphql",
                json={"query": "query { userStatus { isSignedIn username } }"},
                headers={
                    "X-CSRFToken": csrf_token,
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                },
            )

            self.session.cookies.clear(domain="leetcode.com")

            if response.status_code == 200:
                data = response.json()
                if "errors" not in data:
                    return {"success": True, "message": "CSRF token verified"}

            return {"success": False, "message": "Invalid CSRF token"}

        except Exception as e:
            return {"success": False, "message": f"CSRF verification error: {str(e)}"}

    def login_with_session(
        self, csrf_token: str, leetcode_session: str
    ) -> Dict[str, Any]:
        """Login using verified CSRF token and session token"""
        try:
            if not csrf_token or not leetcode_session:
                return {
                    "success": False,
                    "message": "Both CSRF and LEETCODE_SESSION tokens are required",
                }

            self.session.cookies.set(
                "LEETCODE_SESSION", leetcode_session, domain="leetcode.com"
            )

            response = self.session.get(
                f"{self.BASE_URL}/api/problems/all/",
                headers={
                    "X-CSRFToken": csrf_token,
                    "Accept": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                },
            )

            if response.status_code == 200:
                user_data = response.json()
                if user_data.get("user_name"):
                    self.is_authenticated = True
                    self.session_manager.save_session(
                        csrf_token, leetcode_session, user_data["user_name"]
                    )
                    return {
                        "success": True,
                        "message": "Successfully logged in",
                        "user_name": user_data["user_name"],
                    }

            self.session_manager.clear_session()
            return {"success": False, "message": "Invalid session credentials"}

        except Exception as e:
            self.session_manager.clear_session()
            return {"success": False, "message": f"Login error: {str(e)}"}

    def get_session(self) -> requests.Session:
        """Return the authenticated session."""
        return self.session
