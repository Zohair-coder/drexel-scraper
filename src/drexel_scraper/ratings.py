# Allows you to get the ratings of a professor from RateMyProfessors.com
# Makes a request to the RateMyProfessors GraphQL API
# I found out that the GraphQL API is used by inspecting the network tab in the browser

from typing import Any, cast

import requests

from drexel_scraper.helpers import send_request

DREXEL_RMP_ID = "U2Nob29sLTE1MjE="

# I found this header by inspecting the network tab in the browser
# It does not change: it is the same for every request (even if you're not logged in)
# So I don't think it's a security risk to hardcode it
AUTHORIZATION_HEADER = "Basic dGVzdDp0ZXN0"


def search_professors(professor_name: str) -> list[dict[str, dict[str, str]]]:
    query = """query searchProf($query: TeacherSearchQuery!){
        newSearch {
            teachers(query: $query) {
                edges {
                    node {
                        id
                        firstName
                        lastName
                        department
                    }
                }
            }
        }
    }"""

    variables = {"query": {"text": professor_name, "schoolID": DREXEL_RMP_ID}}

    response = send_request(
        requests.Session(),
        "https://www.ratemyprofessors.com/graphql",
        "POST",
        json={"query": query, "variables": variables},
        headers={"Authorization": AUTHORIZATION_HEADER},
    )

    return cast(
        list[dict[str, dict[str, str]]],
        response.json()["data"]["newSearch"]["teachers"]["edges"],
    )


def get_ratings(id: str) -> dict[str, Any]:
    query = """query TeacherRatingsPageQuery($id: ID!){
        node(id: $id) {
            __typename
            ... on Teacher {
                avgRating
                avgDifficulty
                numRatings
                legacyId
            }
        }
    }"""

    variables = {"id": id}

    response = send_request(
        requests.Session(),
        "https://www.ratemyprofessors.com/graphql",
        "POST",
        json={"query": query, "variables": variables},
        headers={"Authorization": AUTHORIZATION_HEADER},
    )

    return cast(dict[str, Any], response.json()["data"]["node"])


def rating(professor_name: str) -> dict[str, int] | None:
    professor = search_professors(professor_name)

    if len(professor) == 0:
        return None

    professor_id = professor[0]["node"]["id"]

    ratings = get_ratings(professor_id)

    if ratings is None:
        return None

    del ratings["__typename"]  # Not needed

    if ratings["numRatings"] == 0:
        return None

    return ratings


if __name__ == "__main__":
    print(rating("Galen Long"))
