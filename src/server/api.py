import requests
from .config import BASE_URL

def fetch_problem_list():
  """Fetches a list of LeetCode problems from the API."""
  query = {
    "query": """
    query {
      problemsetQuestionListV2(
        categorySlug: ""
        limit: 10
        skip: 0
      ) {
        questions {
          questionFrontendId
          title
          difficulty
          topicTags {
            name
          }
        }
      }
    }
    """
  }

  response = requests.post(BASE_URL, json=query)
  data = response.json()

  if "errors" in data:
    print("Error fetching problems:", data["errors"])
    return []

  return data["data"]["problemsetQuestionList"]["questions"]
