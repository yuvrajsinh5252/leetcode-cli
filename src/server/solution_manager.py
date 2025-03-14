import time
from typing import Any, Dict, List, Optional, Union

from ..server.config import (
    LEETCODE_BASE_URL,
    SUBMISSION_RESULT_TIMEOUT,
    TEST_RESULT_TIMEOUT,
)


class SolutionManager:
    def __init__(self, session):
        self.session = session
        self.BASE_URL = LEETCODE_BASE_URL
        self._clean_session_cookies()

    def _clean_session_cookies(self):
        """Clean up duplicate cookies"""
        seen_cookies = {}
        if not hasattr(self.session, "cookies"):
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
            if cookie.name == "csrftoken":
                return cookie.value
        return ""

    def _resolve_question_slug(self, question_identifier: str) -> str:
        """Convert question number to title slug if needed"""
        if not question_identifier.isdigit():
            return question_identifier

        response = self.session.get(f"{self.BASE_URL}/api/problems/all/")
        if response.status_code == 200:
            problems = response.json().get("stat_status_pairs", [])
            for problem in problems:
                if str(problem["stat"]["frontend_question_id"]) == question_identifier:
                    return problem["stat"]["question__title_slug"]

        raise ValueError(f"Question number {question_identifier} not found")

    def _prepare_request_headers(
        self, title_slug: str, csrf_token: Optional[str] = None
    ) -> Dict[str, str]:
        """Prepare common request headers"""
        if csrf_token is None:
            csrf_token = self._get_csrf_token()

        return {
            "referer": f"{self.BASE_URL}/problems/{title_slug}/",
            "content-type": "application/json",
            "x-csrftoken": csrf_token,
            "x-requested-with": "XMLHttpRequest",
            "origin": self.BASE_URL,
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
                    topicTags {
                        name
                    }
                    similarQuestionList {
                        title
                        titleSlug
                        difficulty
                        isPaidOnly
                    }
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

        try:
            response = self.session.post(
                f"{self.BASE_URL}/graphql",
                json={"query": query, "variables": {"titleSlug": title_slug}},
            )

            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def get_problem_solutions(
        self, question_identifier: str, best: bool
    ) -> Dict[str, Any]:
        """Get problem solutions using GraphQL
        Args:
            question_identifier: Can be either title slug (e.g. 'two-sum') or question number (e.g. '1')
        """

        try:
            title_slug = self._resolve_question_slug(question_identifier)
        except ValueError as e:
            return {"error": str(e)}

        query = """
            query ugcArticleSolutionArticles(
                $questionSlug: String!,
                $orderBy: ArticleOrderByEnum,
                $userInput: String,
                $tagSlugs: [String!],
                $skip: Int,
                $before: String,
                $after: String,
                $first: Int,
                $last: Int,
                $isMine: Boolean
            ) {
                ugcArticleSolutionArticles(
                    questionSlug: $questionSlug
                    orderBy: $orderBy
                    userInput: $userInput
                    tagSlugs: $tagSlugs
                    skip: $skip
                    first: $first
                    before: $before
                    after: $after
                    last: $last
                    isMine: $isMine
                ) {
                    totalNum
                    edges {
                        node {
                            title
                            slug
                            summary
                            author {
                                realName
                                userSlug
                                userName
                            }
                            articleType
                            summary
                            createdAt
                            updatedAt
                            topicId
                            hitCount
                            reactions {
                                count
                                reactionType
                            }
                            tags {
                                name
                                slug
                                tagType
                            }
                        }
                    }
                }
            }
        """

        variables = {
            "questionSlug": title_slug,
            "orderBy": "HOT",
            "userInput": "",
            "tagSlugs": [],
            "skip": 0,
            "first": 15,
        }

        try:
            response = self.session.post(
                f"{self.BASE_URL}/graphql",
                json={"query": query, "variables": variables},
            )

            if response.status_code != 200:
                raise Exception(f"Request failed with status {response.status_code}")

            return response.json()
        except Exception as e:
            raise e

    def _format_output(self, output: Union[str, List, None]) -> str:
        """Format output that could be string or list"""
        if output is None:
            return "No output"
        if isinstance(output, list):
            return "\n".join(str(item) for item in output)
        if isinstance(output, str):
            return output.strip('[]"')
        return str(output)

    def _get_result_with_polling(
        self, submission_id: str, timeout: int, is_test: bool = False
    ) -> Dict[str, Any]:
        """Poll for results with timeout"""
        url = f"{self.BASE_URL}/submissions/detail/{submission_id}/check/"

        for _ in range(timeout):
            try:
                time.sleep(1)
                response = self.session.get(url)

                if response.status_code != 200:
                    continue

                result = response.json()
                if result.get("state") == "SUCCESS":
                    return result
            except Exception:
                continue

        return {"success": False, "error": "Timeout waiting for results"}

    def _prepare_solution(
        self, title_slug: str, code: str, lang: str
    ) -> Dict[str, Any]:
        """Common preparation for both test and submit operations"""
        try:
            try:
                title_slug = self._resolve_question_slug(title_slug)
            except ValueError as e:
                return {"success": False, "error": str(e)}

            self._clean_session_cookies()

            problem = self.get_question_data(title_slug)
            question_data = problem.get("data", {}).get("question")
            if not question_data:
                return {"success": False, "error": "Question data not found"}

            return {
                "success": True,
                "title_slug": title_slug,
                "question_id": question_data["questionId"],
                "test_cases": question_data.get("exampleTestcaseList", []),
            }
        except Exception as e:
            return {"success": False, "error": f"Error preparing solution: {str(e)}"}

    def submit_solution(
        self, title_slug: str, code: str, lang: str = "python3"
    ) -> Dict[str, Any]:
        """Submit a solution to LeetCode"""
        try:
            prep_result = self._prepare_solution(title_slug, code, lang)
            if not prep_result["success"]:
                return prep_result

            title_slug = prep_result["title_slug"]
            question_id = prep_result["question_id"]

            submit_url = f"{self.BASE_URL}/problems/{title_slug}/submit/"
            headers = self._prepare_request_headers(title_slug)

            data = {"lang": lang, "question_id": question_id, "typed_code": code}

            response = self.session.post(submit_url, json=data, headers=headers)

            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Submission failed with status {response.status_code}",
                }

            try:
                result_data = response.json()
                submission_id = result_data.get("submission_id")
                if submission_id:
                    return self._get_result_with_polling(
                        submission_id, SUBMISSION_RESULT_TIMEOUT, is_test=False
                    )
                else:
                    return {"success": False, "error": "No submission ID received"}
            except ValueError as e:
                return {
                    "success": False,
                    "error": f"Failed to parse response: {str(e)}",
                }

        except Exception as e:
            return {"success": False, "error": f"Submission error: {str(e)}"}

    def test_solution(
        self, title_slug: str, code: str, lang: str = "python3", full: bool = False
    ) -> Dict[str, Any]:
        """Test a solution with LeetCode test cases"""
        try:
            prep_result = self._prepare_solution(title_slug, code, lang)
            if not prep_result["success"]:
                return prep_result

            title_slug = prep_result["title_slug"]
            question_id = prep_result["question_id"]
            test_cases = prep_result["test_cases"]

            endpoint = "submit" if full else "interpret_solution"
            sid_key = "submission_id" if full else "interpret_id"
            url = f"{self.BASE_URL}/problems/{title_slug}/{endpoint}/"
            headers = self._prepare_request_headers(title_slug)

            data = {
                "lang": lang,
                "question_id": str(question_id),
                "typed_code": code,
                "data_input": "\n".join(test_cases)
                if isinstance(test_cases, list)
                else test_cases,
                "test_mode": False,
                "judge_type": "small",
            }

            response = self.session.post(url, json=data, headers=headers)

            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Request failed with status {response.status_code}",
                }

            try:
                result_data = response.json()
                submission_id = result_data.get(sid_key)
                if submission_id:
                    return self._get_result_with_polling(
                        submission_id, TEST_RESULT_TIMEOUT, is_test=True
                    )
                else:
                    return {"success": False, "error": "No submission ID received"}
            except ValueError as e:
                return {
                    "success": False,
                    "error": f"Failed to parse response: {str(e)}",
                }

        except Exception as e:
            return {"success": False, "error": f"Test error: {str(e)}"}
