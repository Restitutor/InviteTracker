r"""Bulk data importer. By default it will only add the delta.
1. Shell: python3 bulkimport.py > data.csv
2. SQL: load data infile 'data.csv' into table invites FIELDS TERMINATED BY ',' LINES TERMINATED BY '\n' (invitee, inviter, server, time);
"""

from datetime import datetime, timedelta, timezone

from db import get_all_invitees
from rawapi import get_all


def convert_utc_iso_to_local_mysql_datetime(
    iso_str: str,
    local_tz_offset_hours: int = -5,
) -> str:
    # Parse ISO 8601 string (which includes timezone info)
    # Example input: '2024-11-25T07:18:30.998000+00:00'
    assert iso_str.endswith("000+00:00")
    dt_utc = datetime.fromisoformat(iso_str)

    # Define the local timezone as a fixed offset
    local_tz = timezone(timedelta(hours=local_tz_offset_hours))

    # Convert from UTC to local timezone
    dt_local = dt_utc.astimezone(local_tz)

    # Format as 'YYYY-MM-DD HH:MM:SS' — truncate fractional seconds
    return dt_local.strftime("%Y-%m-%d %H:%M:%S")


InviteeMapping = list[tuple[str, str, str]]


def get_inviters():
    # Invitee to inviter
    mapping: InviteeMapping = []
    all_members = get_all()
    for m in all_members["members"]:
        if m["inviter_id"] is None:
            continue

        mapping.append(
            (m["member"]["user"]["id"], m["inviter_id"], m["member"]["joined_at"]),
        )

    # print("Found", len(mapping), "associations.")
    return mapping


if __name__ == "__main__":
    TRACKED_GUILD = 148831815984087041
    try:
        invitees = get_all_invitees(TRACKED_GUILD)
    except:
        invitees = set()

    for line in get_inviters():
        invitee, inviter, date = line
        dbdate = convert_utc_iso_to_local_mysql_datetime(date)
