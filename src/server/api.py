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

def fetch_user_profile(username: str = "yuvrajsinh5252"):
  client = create_leetcode_client("csrf_token", "session_id")
  queries = {
    "userProfile": """
      query userPublicProfile($username: String!) {
        matchedUser(username: $username) {
          contestBadge { name expired hoverText icon }
          username githubUrl twitterUrl linkedinUrl
          profile {
            ranking userAvatar realName aboutMe school websites
            countryName company jobTitle skillTags postViewCount
            postViewCountDiff reputation reputationDiff solutionCount
            solutionCountDiff categoryDiscussCount categoryDiscussCountDiff
            certificationLevel
          }
        }
      }
    """,
    "languageStats": """
      query languageStats($username: String!) {
        matchedUser(username: $username) {
          languageProblemCount {
            languageName
            problemsSolved
          }
        }
      }
    """,
    "skillStats": """
      query skillStats($username: String!) {
        matchedUser(username: $username) {
          tagProblemCounts {
            advanced { tagName tagSlug problemsSolved }
            intermediate { tagName tagSlug problemsSolved }
            fundamental { tagName tagSlug problemsSolved }
          }
        }
      }
    """,
    "contestInfo": """
      query userContestRankingInfo($username: String!) {
        userContestRanking(username: $username) {
          attendedContestsCount rating globalRanking
          totalParticipants topPercentage
          badge { name }
        }
        userContestRankingHistory(username: $username) {
          attended trendDirection problemsSolved totalProblems
          finishTimeInSeconds rating ranking
          contest { title startTime }
        }
      }
    """,
    "progress": """
      query userSessionProgress($username: String!) {
        allQuestionsCount { difficulty count }
        matchedUser(username: $username) {
          submitStats {
            acSubmissionNum { difficulty count submissions }
            totalSubmissionNum { difficulty count submissions }
          }
        }
      }
    """,
    "calendar": """
      query userProfileCalendar($username: String!, $year: Int) {
        matchedUser(username: $username) {
          userCalendar(year: $year) {
            activeYears streak totalActiveDays
            dccBadges { timestamp badge { name icon } }
            submissionCalendar
          }
        }
      }
    """
  }

  results = {}
  for name, query in queries.items():
    try:
      results[name] = client.execute(
        gql(query),
        variable_values={"username": username}
      )
    except Exception as e:
      print(f"Error fetching {name}: {str(e)}")
      results[name] = None

  return results

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
