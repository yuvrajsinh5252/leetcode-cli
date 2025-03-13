from typing import Dict, Any, Optional, List, Union
import time
from ..server.config import LEETCODE_BASE_URL, STATUS_CODES, MEMORY_WARNING_THRESHOLD, MEMORY_LIMIT_THRESHOLD, TEST_RESULT_TIMEOUT, SUBMISSION_RESULT_TIMEOUT

class SolutionManager:
    def __init__(self, session):
        self.session = session
        self.BASE_URL = LEETCODE_BASE_URL
        self._clean_session_cookies()

    def _clean_session_cookies(self):
        """Clean up duplicate cookies"""
        seen_cookies = {}
        if not hasattr(self.session, 'cookies'):
            return

        all_cookies = list(self.session.cookies)
        self.session.cookies.clear()

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

    def _resolve_question_slug(self, question_identifier: str) -> str:
        """Convert question number to title slug if needed"""
        if not question_identifier.isdigit():
            return question_identifier

        response = self.session.get(f"{self.BASE_URL}/api/problems/all/")
        if response.status_code == 200:
            problems = response.json().get('stat_status_pairs', [])
            for problem in problems:
                if str(problem['stat']['frontend_question_id']) == question_identifier:
                    return problem['stat']['question__title_slug']

        raise ValueError(f"Question number {question_identifier} not found")

    def _prepare_request_headers(self, title_slug: str, csrf_token: Optional[str] = None) -> Dict[str, str]:
        """Prepare common request headers"""
        if csrf_token is None:
            csrf_token = self._get_csrf_token()

        return {
            'referer': f"{self.BASE_URL}/problems/{title_slug}/",
            'content-type': 'application/json',
            'x-csrftoken': csrf_token,
            'x-requested-with': 'XMLHttpRequest',
            'origin': self.BASE_URL
        }

    def get_question_data(self, question_identifier: str) -> Dict[str, Any]:
        """Get question details using GraphQL
        Args:
            question_identifier: Can be either title slug (e.g. 'two-sum') or question number (e.g. '1')
        """
        try:
            title_slug = self._resolve_question_slug(question_identifier)
        except ValueError as e:
            return {"error": str(e)}

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
                "variables": {"titleSlug": title_slug}
            }
        )

        return response.json()

    def _format_output(self, output: Union[str, List, None]) -> str:
        """Format output that could be string or list"""
        if output is None:
            return "No output"
        if isinstance(output, list):
            return '\n'.join(str(item) for item in output)
        if isinstance(output, str):
            return output.strip('[]"')
        return str(output)

    def _process_submission_result(self, result: Dict[str, Any], is_test: bool = False) -> Dict[str, Any]:
        """Process submission/test results and return standardized output"""
        status_code_val = result.get('status_code')

        stdout = result.get('std_output_list', [])
        formatted_stdout = self._format_output(stdout) if stdout and any(stdout) else None

        if not result.get('run_success', True):
            if status_code_val == 20:
                return {
                    "success": False,
                    "status": "Compilation Error",
                    "error": result.get('compile_error', 'Unknown compilation error'),
                    "full_error": result.get('full_compile_error', ''),
                    "stdout": formatted_stdout
                }
            if status_code_val == 14:
                return {
                    "success": False,
                    "status": "Time Limit Exceeded",
                    "error": "Your code took too long to execute",
                    "runtime": result.get('status_runtime', 'N/A'),
                    "elapsed_time": result.get('elapsed_time', 'N/A'),
                    "stdout": formatted_stdout
                }
            if status_code_val == 15:
                return {
                    "success": False,
                    "status": "Runtime Error",
                    "error": result.get('runtime_error', 'Unknown runtime error'),
                    "full_error": result.get('full_runtime_error', ''),
                    "stdout": formatted_stdout
                }
            return {
                "success": False,
                "status": result.get('status_msg', 'Error'),
                "error": result.get('runtime_error', 'Unknown error'),
                "full_error": result.get('full_runtime_error', ''),
                "stdout": formatted_stdout
            }

        memory_usage = result.get('memory', 0)
        memory_str = result.get('status_memory', f"{memory_usage/1000000:.1f} MB" if memory_usage else 'N/A')

        memory_warning = None
        memory_limit_exceeded = False

        if memory_usage and memory_usage > MEMORY_LIMIT_THRESHOLD:
            memory_limit_exceeded = True
            memory_warning = "Memory Limit Exceeded: Your solution is using too much memory"
        elif memory_usage and memory_usage > MEMORY_WARNING_THRESHOLD:
            memory_warning = "Warning: High memory usage detected"

        if memory_limit_exceeded:
            return {
                "success": False,
                "status": "Memory Limit Exceeded",
                "error": "Your solution is using too much memory",
                "memory": memory_str,
                "memory_warning": memory_warning,
                "stdout": formatted_stdout
            }

        code_answers = result.get('code_answer', [])
        expected_answers = result.get('expected_code_answer', [])

        is_correct = True
        if expected_answers and (not is_test or result.get('correct_answer') is False):
            is_correct = False

        response = {
            "success": True,
            "status": "Accepted" if is_correct else "Wrong Answer",
            "runtime": result.get('status_runtime', result.get('runtime', 'N/A')),
            "memory": memory_str,
            "memory_warning": memory_warning,
            "total_testcases": result.get('total_testcases', 0),
            "passed_testcases": result.get('total_correct', 0),
            "stdout": formatted_stdout
        }

        if code_answers or expected_answers:
            response.update({
                "output": self._format_output(code_answers),
                "expected": self._format_output(expected_answers),
                "total_correct": sum(1 for a, b in zip(code_answers, expected_answers)
                                    if str(a).strip() == str(b).strip()) if code_answers and expected_answers else 0
            })

        return response

    def _get_result_with_polling(self, submission_id: str, timeout: int, is_test: bool = False) -> Dict[str, Any]:
        """Poll for results with timeout"""
        url = f"{self.BASE_URL}/submissions/detail/{submission_id}/check/"

        for _ in range(timeout):
            try:
                time.sleep(1)
                response = self.session.get(url)

                if response.status_code != 200:
                    continue

                result = response.json()
                if result.get('state') == 'SUCCESS':
                    return self._process_submission_result(result, is_test=is_test)
            except Exception as e:
                continue

        return {"success": False, "error": "Timeout waiting for results"}

    def _prepare_solution(self, title_slug: str, code: str, lang: str) -> Dict[str, Any]:
        """Common preparation for both test and submit operations"""
        try:
            try:
                title_slug = self._resolve_question_slug(title_slug)
            except ValueError as e:
                return {"success": False, "error": str(e)}

            self._clean_session_cookies()

            problem = self.get_question_data(title_slug)
            question_data = problem.get('data', {}).get('question')
            if not question_data:
                return {"success": False, "error": "Question data not found"}

            return {
                "success": True,
                "title_slug": title_slug,
                "question_id": question_data['questionId'],
                "test_cases": question_data.get('exampleTestcaseList', [])
            }
        except Exception as e:
            return {"success": False, "error": f"Error preparing solution: {str(e)}"}

    def submit_solution(self, title_slug: str, code: str, lang: str = "python3") -> Dict[str, Any]:
        """Submit a solution to LeetCode"""
        try:
            prep_result = self._prepare_solution(title_slug, code, lang)
            if not prep_result["success"]:
                return prep_result

            title_slug = prep_result["title_slug"]
            question_id = prep_result["question_id"]

            submit_url = f"{self.BASE_URL}/problems/{title_slug}/submit/"
            headers = self._prepare_request_headers(title_slug)

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
                    return self._get_result_with_polling(submission_id, SUBMISSION_RESULT_TIMEOUT, is_test=False)
                else:
                    return {"success": False, "error": "No submission ID received"}
            except ValueError as e:
                return {"success": False, "error": f"Failed to parse response: {str(e)}"}

        except Exception as e:
            return {"success": False, "error": f"Submission error: {str(e)}"}

    def test_solution(self, title_slug: str, code: str, lang: str = "python3", full: bool = False) -> Dict[str, Any]:
        """Test a solution with LeetCode test cases"""
        try:
            prep_result = self._prepare_solution(title_slug, code, lang)
            if not prep_result["success"]:
                return prep_result

            title_slug = prep_result["title_slug"]
            question_id = prep_result["question_id"]
            test_cases = prep_result["test_cases"]

            endpoint = 'submit' if full else 'interpret_solution'
            sid_key = 'submission_id' if full else 'interpret_id'
            url = f"{self.BASE_URL}/problems/{title_slug}/{endpoint}/"
            headers = self._prepare_request_headers(title_slug)

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
                    return self._get_result_with_polling(submission_id, TEST_RESULT_TIMEOUT, is_test=True)
                else:
                    return {"success": False, "error": "No submission ID received"}
            except ValueError as e:
                return {"success": False, "error": f"Failed to parse response: {str(e)}"}

        except Exception as e:
            return {"success": False, "error": f"Test error: {str(e)}"}