from typing import Dict, Any
import time
import json
import typer

class SolutionManager:
    def __init__(self, session):
        self.session = session
        self.BASE_URL = "https://leetcode.com"
        self._clean_session_cookies()

    def _clean_session_cookies(self):
        """Clean up duplicate cookies"""
        seen_cookies = {}
        if not hasattr(self.session, 'cookies'):
            return

        all_cookies = list(self.session.cookies)
        self.session.cookies.clear()

        # Add back only the most recent cookie for each name
        for cookie in reversed(all_cookies):
            if cookie.name not in seen_cookies:
                seen_cookies[cookie.name] = True
                self.session.cookies.set_cookie(cookie)

    def _get_csrf_token(self):
        """Get CSRF token from cookies"""
        for cookie in self.session.cookies:
            if cookie.name == 'csrftoken':
                return cookie.value
        return ''

    def get_question_data(self, question_identifier: str) -> Dict[str, Any]:
        """Get question details using GraphQL
        Args:
            question_identifier: Can be either title slug (e.g. 'two-sum') or question number (e.g. '1')
        """
        if question_identifier.isdigit():
            response = self.session.get(f"{self.BASE_URL}/api/problems/all/")
            if response.status_code == 200:
                problems = response.json().get('stat_status_pairs', [])
                for problem in problems:
                    if str(problem['stat']['frontend_question_id']) == question_identifier:
                        question_identifier = problem['stat']['question__title_slug']
                        break
                else:
                    return {"error": f"Question number {question_identifier} not found"}

        query = """
            query questionData($titleSlug: String!) {
                question(titleSlug: $titleSlug) {
                    questionId
                    title
                    titleSlug
                    content
                    difficulty
                    exampleTestcaseList
                    sampleTestCase
                    stats
                    metaData
                    codeSnippets {
                        lang
                        langSlug
                        code
                    }
                }
            }
        """

        response = self.session.post(
            f"{self.BASE_URL}/graphql",
            json={
                "query": query,
                "variables": {"titleSlug": question_identifier}
            }
        )

        return response.json()

    def submit_solution(self, title_slug: str, code: str, lang: str = "python3") -> Dict[str, Any]:
        """Submit a solution to LeetCode"""
        try:
            self._clean_session_cookies()

            # Get question ID
            question_data = self.get_question_data(title_slug)
            question_data = question_data.get('data', {}).get('question')
            if not question_data:
                return {"success": False, "error": "Question data not found"}

            question_id = question_data['questionId']
            submit_url = f"{self.BASE_URL}/problems/{title_slug}/submit/"

            csrf_token = self._get_csrf_token()
            typer.echo(f"Using CSRF token: {csrf_token}")

            headers = {
                'referer': f"{self.BASE_URL}/problems/{title_slug}/",
                'content-type': 'application/json',
                'x-csrftoken': csrf_token,
                'x-requested-with': 'XMLHttpRequest',
                'origin': self.BASE_URL
            }

            data = {
                "lang": lang,
                "question_id": question_id,
                "typed_code": code
            }

            typer.echo(f"Sending request to {submit_url}")
            response = self.session.post(submit_url, json=data, headers=headers)

            if response.status_code != 200:
                typer.echo(f"Error response: {response.text}", err=True)
                return {"success": False, "error": f"Submission failed with status {response.status_code}"}

            try:
                result_data = response.json()
                submission_id = result_data.get('submission_id')
                if submission_id:
                    typer.echo(f"Got submission ID: {submission_id}")
                    return self.get_submission_result(submission_id)
                else:
                    typer.echo("No submission ID in response", err=True)
                    return {"success": False, "error": "No submission ID received"}
            except ValueError as e:
                typer.echo(f"Failed to parse response: {response.text}", err=True)
                return {"success": False, "error": f"Failed to parse response: {str(e)}"}

        except Exception as e:
            typer.echo(f"Submission error: {str(e)}", err=True)
            return {"success": False, "error": f"Submission error: {str(e)}"}

    def test_solution(self, title_slug: str, code: str, lang: str = "python3", full: bool = False) -> Dict[str, Any]:
        """Test a solution with LeetCode test cases"""
        try:
            self._clean_session_cookies()

            # Get question data first
            problem = self.get_question_data(title_slug)
            question_data = problem.get('data', {}).get('question')
            if not question_data:
                return {"success": False, "error": "Question data not found"}

            question_id = question_data['questionId']
            test_cases = question_data['exampleTestcaseList']

            endpoint = 'submit' if full else 'interpret_solution'
            sid_key = 'submission_id' if full else 'interpret_id'

            url = f"{self.BASE_URL}/problems/{title_slug}/{endpoint}/"

            csrf_token = self.session.cookies.get('csrftoken', '')
            typer.echo(f"Using CSRF token: {csrf_token}")

            headers = {
                'referer': f"{self.BASE_URL}/problems/{title_slug}/",
                'content-type': 'application/json',
                'x-csrftoken': csrf_token,
                'x-requested-with': 'XMLHttpRequest',
                'origin': self.BASE_URL
            }

            data = {
                'lang': lang,
                'question_id': str(question_id),
                'typed_code': code,
                'data_input': "\n".join(test_cases) if isinstance(test_cases, list) else test_cases,
                'test_mode': False,
                'judge_type': 'small'
            }

            typer.echo(f"Sending request to {url}")
            response = self.session.post(url, json=data, headers=headers)

            if response.status_code != 200:
                typer.echo(f"Error response: {response.text}", err=True)
                return {"success": False, "error": f"Request failed with status {response.status_code}"}

            try:
                result_data = response.json()
                submission_id = result_data.get(sid_key)
                if submission_id:
                    typer.echo(f"Got submission ID: {submission_id}")
                    return self.get_test_result(submission_id)
                else:
                    typer.echo("No submission ID in response", err=True)
                    return {"success": False, "error": "No submission ID received"}
            except ValueError as e:
                typer.echo(f"Failed to parse response: {response.text}", err=True)
                return {"success": False, "error": f"Failed to parse response: {str(e)}"}

        except Exception as e:
            typer.echo(f"Test error: {str(e)}", err=True)
            return {"success": False, "error": f"Test error: {str(e)}"}

    def _format_output(self, output) -> str:
        """Format output that could be string or list"""
        if isinstance(output, list):
            return '\n'.join(str(item) for item in output)
        if isinstance(output, str):
            return output.strip('[]"')
        return str(output)

    def get_test_result(self, submission_id: str, timeout: int = 30) -> Dict[str, Any]:
        """Poll for results with timeout"""
        url = f"{self.BASE_URL}/submissions/detail/{submission_id}/check/"
        typer.echo(f"Polling for results at {url}")

        for i in range(timeout):
            try:
                time.sleep(1)
                typer.echo(f"Attempt {i+1}/{timeout}...")

                response = self.session.get(url)
                if response.status_code != 200:
                    continue

                result = response.json()
                typer.echo(f"Got response: {json.dumps(result, indent=2)}")

                if result.get('state') == 'SUCCESS':
                    return {
                        "success": True,
                        "status": result.get('status_msg', 'Unknown'),
                        "input": result.get('input', 'N/A'),
                        "output": self._format_output(result.get('code_answer', [])),
                        "expected": self._format_output(result.get('expected_code_answer', [])),
                        "runtime": result.get('status_runtime', 'N/A'),
                        "memory": result.get('status_memory', 'N/A'),
                        "total_correct": result.get('total_correct', 0),
                        "total_testcases": result.get('total_testcases', 0)
                    }
            except Exception as e:
                typer.echo(f"Error checking result: {str(e)}", err=True)
                continue

        return {"success": False, "error": "Timeout waiting for results"}

    def get_submission_result(self, submission_id: str) -> Dict[str, Any]:
        """Poll for submission results"""
        check_url = f"{self.BASE_URL}/submissions/detail/{submission_id}/check/"

        for _ in range(20):  #
            response = self.session.get(check_url)
            if response.status_code != 200:
                return {"success": False, "error": f"Failed to get results: {response.status_code}"}

            result = response.json()
            if result.get('state') == 'SUCCESS':
                return {
                    "success": True,
                    "status": result.get('status_msg', 'Unknown'),
                    "runtime": result.get('runtime', 'N/A'),
                    "memory": result.get('memory', 'N/A'),
                    "total_testcases": result.get('total_testcases', 0),
                    "passed_testcases": result.get('total_correct', 0)
                }

            time.sleep(1)

        return {"success": False, "error": "Timeout waiting for results"}