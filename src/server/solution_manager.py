from typing import Dict, Any
import time

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
                    questionFrontendId
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
            if title_slug.isdigit():
                response = self.session.get(f"{self.BASE_URL}/api/problems/all/")
                if response.status_code == 200:
                    problems = response.json().get('stat_status_pairs', [])
                    for problem in problems:
                        if str(problem['stat']['frontend_question_id']) == title_slug:
                            title_slug = problem['stat']['question__title_slug']
                            break
                    else:
                        return {"success": False, "error": f"Question number {title_slug} not found"}

            self._clean_session_cookies()

            # Get question ID
            question_data = self.get_question_data(title_slug)
            question_data = question_data.get('data', {}).get('question')
            if not question_data:
                return {"success": False, "error": "Question data not found"}

            question_id = question_data['questionFrontendId']
            submit_url = f"{self.BASE_URL}/problems/{title_slug}/submit/"

            csrf_token = self._get_csrf_token()

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

            response = self.session.post(submit_url, json=data, headers=headers)

            if response.status_code != 200:
                return {"success": False, "error": f"Submission failed with status {response.status_code}"}

            try:
                result_data = response.json()
                submission_id = result_data.get('submission_id')
                if submission_id:
                    return self.get_submission_result(submission_id)
                else:
                    return {"success": False, "error": "No submission ID received"}
            except ValueError as e:
                return {"success": False, "error": f"Failed to parse response: {str(e)}"}

        except Exception as e:
            return {"success": False, "error": f"Submission error: {str(e)}"}

    def test_solution(self, title_slug: str, code: str, lang: str = "python3", full: bool = False) -> Dict[str, Any]:
        """Test a solution with LeetCode test cases"""
        try:
            if title_slug.isdigit():
                response = self.session.get(f"{self.BASE_URL}/api/problems/all/")
                if response.status_code == 200:
                    problems = response.json().get('stat_status_pairs', [])
                    for problem in problems:
                        if str(problem['stat']['frontend_question_id']) == title_slug:
                            title_slug = problem['stat']['question__title_slug']
                            break
                    else:
                        return {"success": False, "error": f"Question number {title_slug} not found"}

            self._clean_session_cookies()

            # Get question data first
            problem = self.get_question_data(title_slug)
            question_data = problem.get('data', {}).get('question')
            if not question_data:
                return {"success": False, "error": "Question data not found"}

            question_id = question_data['questionFrontendId']
            test_cases = question_data['exampleTestcaseList']

            endpoint = 'submit' if full else 'interpret_solution'
            sid_key = 'submission_id' if full else 'interpret_id'

            url = f"{self.BASE_URL}/problems/{title_slug}/{endpoint}/"

            csrf_token = self.session.cookies.get('csrftoken', '')

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

            response = self.session.post(url, json=data, headers=headers)

            if response.status_code != 200:
                return {"success": False, "error": f"Request failed with status {response.status_code}"}

            try:
                result_data = response.json()
                submission_id = result_data.get(sid_key)
                if submission_id:
                    return self.get_test_result(submission_id)
                    return temp
                else:
                    return {"success": False, "error": "No submission ID received"}
            except ValueError as e:
                return {"success": False, "error": f"Failed to parse response: {str(e)}"}

        except Exception as e:
            return {"success": False, "error": f"Test error: {str(e)}"}

    def _format_output(self, output) -> str:
        """Format output that could be string or list"""
        if isinstance(output, list):
            return '\n'.join(str(item) for item in output)
        if isinstance(output, str):
            return output.strip('[]"')
        return str(output)

    def _process_submission_result(self, result: Dict[str, Any], is_test: bool = False) -> Dict[str, Any]:
        """Process submission/test results and return standardized output"""
        if not result.get('run_success', True):
            if result.get('compile_error'):
                return {
                    "success": False,
                    "status": "Compilation Error",
                    "error": result.get('compile_error', 'Unknown compilation error'),
                    "full_error": result.get('full_compile_error', '')
                }
            if result.get('status_code') == 14:
                return {
                    "success": False,
                    "status": "Time Limit Exceeded",
                    "error": "Your code took too long to execute",
                    "runtime": result.get('status_runtime', 'N/A')
                }
            return {
                "success": False,
                "status": "Runtime Error",
                "error": result.get('runtime_error', 'Unknown runtime error'),
                "full_error": result.get('full_runtime_error', '')
            }

        response = {
            "success": True,
            "status": result.get('status_msg', 'Accepted'),
            "runtime": result.get('status_runtime', result.get('runtime', 'N/A')),
            "memory": result.get('status_memory', result.get('memory', 'N/A')),
            "total_testcases": result.get('total_testcases', 0),
            "passed_testcases": result.get('total_correct', 0)
        }

        if is_test:
            code_answers = result.get('code_answer', [])
            expected_answers = result.get('expected_code_answer', [])
            is_correct = all(a == b for a, b in zip(code_answers, expected_answers))

            response.update({
                "status": "Accepted" if is_correct else "Wrong Answer",
                "output": self._format_output(code_answers),
                "expected": self._format_output(expected_answers),
                "total_correct": sum(1 for a, b in zip(code_answers, expected_answers) if a == b)
            })

        return response

    def get_test_result(self, submission_id: str, timeout: int = 30) -> Dict[str, Any]:
        """Poll for test results with timeout"""
        url = f"{self.BASE_URL}/submissions/detail/{submission_id}/check/"

        for _ in range(timeout):
            try:
                time.sleep(1)
                response = self.session.get(url)

                if response.status_code != 200:
                    continue

                result = response.json()
                if result.get('state') == 'SUCCESS':
                    return self._process_submission_result(result, is_test=True)
            except Exception as e:
                continue

        return {"success": False, "error": "Timeout waiting for results"}

    def get_submission_result(self, submission_id: str, timeout: int = 20) -> Dict[str, Any]:
        """Poll for submission results"""
        url = f"{self.BASE_URL}/submissions/detail/{submission_id}/check/"

        for _ in range(timeout):
            try:
                response = self.session.get(url)
                if response.status_code != 200:
                    continue

                result = response.json()
                if result.get('state') == 'SUCCESS':
                    return self._process_submission_result(result, is_test=False)

                time.sleep(1)
            except Exception as e:
                continue

        return {"success": False, "error": "Timeout waiting for results"}