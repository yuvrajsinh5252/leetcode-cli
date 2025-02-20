from typing import Dict, Any
import time

class SolutionManager:
    def __init__(self, session):
        self.session = session
        self.BASE_URL = "https://leetcode.com"

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
        # First get the question ID
        question_data = self.get_question_data(title_slug)
        question_id = question_data['data']['question']['questionId']

        submit_url = f"{self.BASE_URL}/problems/{title_slug}/submit/"

        data = {
            "lang": lang,
            "question_id": question_id,
            "typed_code": code
        }

        response = self.session.post(submit_url, json=data)
        if response.status_code != 200:
            return {"success": False, "error": f"Submission failed: {response.status_code}"}

        submission_id = response.json().get('submission_id')
        if not submission_id:
            return {"success": False, "error": "No submission ID received"}

        return self.get_submission_result(submission_id)

    def test_solution(self, title_slug: str, code: str, lang: str = "python3") -> Dict[str, Any]:
        """Test a solution with LeetCode test cases"""
        try:
            # First get the question data
            question_data = self.get_question_data(title_slug)
            question = question_data['data']['question']
            question_id = question['questionId']
            test_cases = question['exampleTestcases']

            test_url = f"{self.BASE_URL}/problems/{title_slug}/interpret_solution/"

            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': f'{self.BASE_URL}/problems/{title_slug}/'
            }

            data = {
                "lang": lang,
                "question_id": question_id,
                "typed_code": code,
                "data_input": test_cases,
                "judge_type": "large"
            }

            response = self.session.post(test_url, json=data, headers=headers, timeout=30)

            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Test request failed. Make sure your code is valid {lang} code."
                }

            interpret_id = response.json().get('interpret_id')
            if not interpret_id:
                return {"success": False, "error": "No interpret ID received"}

            return self.get_test_result(interpret_id)

        except Exception as e:
            return {"success": False, "error": f"Test error: {str(e)}"}

    def get_submission_result(self, submission_id: str) -> Dict[str, Any]:
        """Poll for submission results"""
        check_url = f"{self.BASE_URL}/submissions/detail/{submission_id}/check/"

        for _ in range(20):  # Try for 20 seconds
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

    def get_test_result(self, interpret_id: str) -> Dict[str, Any]:
        """Poll for test results"""
        check_url = f"{self.BASE_URL}/submissions/detail/{interpret_id}/check/"

        headers = {
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        max_attempts = 10
        for attempt in range(max_attempts):
            try:
                response = self.session.get(check_url, headers=headers)
                if response.status_code != 200:
                    return {"success": False, "error": f"Failed to get results: {response.status_code}"}

                result = response.json()

                # Check for compilation errors first
                if result.get('status_msg') == 'Compile Error':
                    return {
                        "success": False,
                        "error": f"Compilation Error:\n{result.get('compile_error', 'Unknown compilation error')}"
                    }

                if result.get('state') == 'SUCCESS':
                    status_msg = result.get('status_msg', 'Unknown')
                    return {
                        "success": True,
                        "status": status_msg,
                        "input": result.get('input', 'N/A'),
                        "output": result.get('code_output', 'N/A').strip('[]"'),
                        "expected": result.get('expected_output', 'N/A').strip('[]"'),
                        "runtime": result.get('status_runtime', 'N/A'),
                        "memory": result.get('memory', 'N/A'),
                    }

                # If not success yet, wait before next attempt
                if attempt < max_attempts - 1:
                    time.sleep(2)

            except Exception as e:
                return {"success": False, "error": f"Error checking results: {str(e)}"}

        return {"success": False, "error": "Timeout waiting for test results"}