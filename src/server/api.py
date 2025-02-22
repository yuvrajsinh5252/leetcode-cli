from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

def create_leetcode_client(csrf_token: str, session_id: str):
    headers = {
        'Content-Type': 'application/json',
        'x-csrftoken': csrf_token,
        'cookie': f'csrftoken={csrf_token}; LEETCODE_SESSION={session_id}',
        'referer': 'https://leetcode.com',
    }

    transport = RequestsHTTPTransport(
        url='https://leetcode.com/graphql',
        headers=headers,
    )

    return Client(
        transport=transport,
        fetch_schema_from_transport=False
    )

def fetch_user_data(username: str = "yuvrajsinh5252"):
  client = create_leetcode_client("csrf_token", "session_id")
  variables = {"username": username}
  query = gql(
    """
    query userProblemsSolved($username: String!) {
      allQuestionsCount {
        difficulty
        count
      }
      matchedUser(username: $username) {
        problemsSolvedBeatsStats {
          difficulty
          percentage
        }
        submitStatsGlobal {
          acSubmissionNum {
            difficulty
            count
          }
        }
      }
    }
    """
  )

  try:
    result = client.execute(query, variable_values=variables)
    return result
  except Exception as e:
    print(f"Error fetching data: {str(e)}")
    return None

def fetch_problem_list(
    csrf_token: str,
    session_id: str,
    categorySlug: str,
    limit: int = 20,
    skip: int = 0,
    filters: dict = {}
):
    if filters and 'difficulty' in filters:
        filters['difficulty'] = filters['difficulty'].upper()

    client = create_leetcode_client(csrf_token, session_id)
    variables = {
        "categorySlug": categorySlug,
        "limit": limit,
        "skip": skip,
        "filters": filters
    }

    query = gql(
        """
        query problemsetQuestionList($categorySlug: String, $limit: Int, $skip: Int, $filters: QuestionListFilterInput) {
            problemsetQuestionList: questionList(
                categorySlug: $categorySlug
                limit: $limit
                skip: $skip
                filters: $filters
            ) {
                total: totalNum
                questions: data {
                    acRate
                    difficulty
                    freqBar
                    frontendQuestionId: questionFrontendId
                    isFavor
                    paidOnly: isPaidOnly
                    status
                    title
                    titleSlug
                    topicTags {
                        name
                        id
                        slug
                    }
                    hasSolution
                    hasVideoSolution
                }
            }
        }
        """
    )

    try:
        result = client.execute(query, variable_values=variables)
        return result
    except Exception as e:
        print(f"Error fetching data: {str(e)}")
        return None
