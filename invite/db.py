import json

import mariadb

with open("discorddb.json") as f:
    connect_params = json.load(f)


def get_conn() -> mariadb.Connection:
    return mariadb.connect(**connect_params)


def insert_row(invitee: int, inviter: int, server: int) -> bool:
    query = """
        INSERT IGNORE INTO invites (invitee, inviter, server)
        VALUES (?, ?, ?)
    """
    try:
        with get_conn() as conn:
            cursor = conn.cursor(prepared=True)
            cursor.execute(query, (invitee, inviter, server))
            conn.commit()
            # If a row was inserted, cursor.rowcount will be 1, else 0 on duplicate ignored
            print("Added", invitee, inviter, server)
            return cursor.rowcount == 1
    except mariadb.Error:
        return False


def get_all_invitees(server: int) -> set[int]:
    query = """
        SELECT distinct invitee
        FROM invites
        WHERE server = ?
    """
    try:
        with get_conn() as conn:
            cursor = conn.cursor(prepared=True)
            cursor.execute(query, (server,))
            return {i[0] for i in cursor.fetchall()}
    except mariadb.Error:
        raise


def get_inviter_invitees(server: int) -> dict[int, list[str]]:
    query = """
        SELECT
            inviter,
            GROUP_CONCAT(invitee ORDER BY time SEPARATOR ',') AS invitees
        FROM invites
        WHERE server = ?
        GROUP BY inviter
    """
    result: dict[int, list[str]] = {}
    try:
        with get_conn() as conn:
            cursor = conn.cursor(prepared=True)
            cursor.execute(query, (server,))
            for inviter, invitees_str in cursor:
                # invitees_str is a comma separated string like "123,456,789"
                invitees_list = invitees_str.split(",") if invitees_str else []
                result[int(inviter)] = invitees_list

            del result[150651680168345600]  # Legacy invite
    except mariadb.Error:
        raise
    return result
