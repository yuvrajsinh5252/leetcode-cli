from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

transport = RequestsHTTPTransport(
	url='https://leetcode.com/graphql',
	headers={'Content-Type': 'application/json'},
)

client = Client(
  transport=transport,
  fetch_schema_from_transport=False
)

def fetch_problem_list(username: str = "yuvrajsinh5252"):
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