import requests

from invite.config import TOKEN

s = requests.Session()

dHeaders = {
    "Authorization": f"Bot {TOKEN}",
    "User-Agent": "InviteTracker (requests, 2.9)",
}

s.headers.update(dHeaders)


def get_member(username: str, guild: int = 148831815984087041) -> dict:
    API = f"https://discord.com/api/v10/guilds/{guild}/members-search"
    members = s.post(
        API,
        json={
            "and_query": {"usernames": {"or_query": [username]}},
            "limit": 5,
        },
    ).json()["members"]
    assert members

    last_join = max(i["member"]["joined_at"] for i in members)
    for m in members:
        if m["member"]["joined_at"] == last_join:
            return m
    return None


def get_all(guild: int = 148831815984087041) -> dict:
    API = f"https://discord.com/api/v10/guilds/{guild}/members-search"
    resp = s.post(
        API,
        json={
            "limit": 350,
        },
    ).json()
    if resp.get("code") == 50001:
        raise PermissionError

    return resp


if __name__ == "__main__":
    pass
