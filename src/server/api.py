import requests
import typer
from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport

from ..server.session_manager import SessionManager


def create_leetcode_client(csrf_token: str, session_id: str):
    headers = {
        "Content-Type": "application/json",
        "x-csrftoken": csrf_token,
        "cookie": f"csrftoken={csrf_token}; LEETCODE_SESSION={session_id}",
        "referer": "https://leetcode.com",
    }

    transport = RequestsHTTPTransport(
        url="https://leetcode.com/graphql",
        headers=headers,
    )

    return Client(transport=transport, fetch_schema_from_transport=False)


def fetch_user_profile():
    session = SessionManager().load_session()
    username = session.get("user_name") if session else None

    if not username:
        typer.echo(
            typer.style(
                "❌ Please login first using the login command", fg=typer.colors.RED
            )
        )
        raise typer.Exit(1)

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
    """,
        "recentAcSubmissions": """
      query recentAcSubmissions($username: String!, $limit: Int!) {
        recentAcSubmissionList(username: $username, limit: $limit) {
          id
          title
          titleSlug
          timestamp
        }
      }
    """,
    }

    results = {}
    for name, query in queries.items():
        try:
            results[name] = client.execute(
                gql(query), variable_values={"username": username, "limit": 10}
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
    filters: dict = {},
):
    if filters and "difficulty" in filters and filters["difficulty"]:
        filters["difficulty"] = filters["difficulty"].upper()

    client = create_leetcode_client(csrf_token, session_id)
    variables = {
        "categorySlug": categorySlug,
        "limit": limit,
        "skip": skip,
        "filters": filters,
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


def get_daily_question():
    url = "https://leetcode.com/graphql"
    query = """
  query questionOfToday {
    activeDailyCodingChallengeQuestion {
      date
      userStatus
      link
      question {
        titleSlug
        title
        translatedTitle
        acRate
        difficulty
        freqBar
        frontendQuestionId: questionFrontendId
        isFavor
        paidOnly: isPaidOnly
        status
        hasVideoSolution
        hasSolution
        topicTags {
          name
          id
          slug
        }
      }
    }
  }
  """
    response = requests.post(url, json={"query": query})
    return response.json()
