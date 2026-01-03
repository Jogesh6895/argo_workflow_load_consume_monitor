import os
import sys
import time
import redis
import datetime
from optparse import OptionParser


NOW_TIME_OBJ = datetime.datetime.now()

CURRENT_YEARWEEK = "%04d%02d" % (
    NOW_TIME_OBJ.year,
    NOW_TIME_OBJ.isocalendar()[1]
)
PREVIOUS_TIME_OBJECT = NOW_TIME_OBJ - datetime.timedelta(weeks=1)
PREVIOUS_YEARWEEK = "%04d%02d" % (
    PREVIOUS_TIME_OBJECT.year,
    PREVIOUS_TIME_OBJECT.isocalendar()[1],
)

REDIS_CONNECTION_DICT = {
    "host": os.getenv("REDIS_HOST", "localhost"),
    "port": int(os.getenv("REDIS_PORT", 6379)),
    "username": os.getenv("REDIS_USERNAME", ""),
    "password": os.getenv("REDIS_PASSWORD"),
    "db": int(os.getenv("REDIS_DB", 0)),
}


def monitor(pattern, check_option):
    try:
        redis_conn = redis.Redis(**REDIS_CONNECTION_DICT)
        weekly_key_pattern = ""
        if check_option == "current":
            weekly_key_pattern = pattern + CURRENT_YEARWEEK
        elif check_option == "previous":
            weekly_key_pattern = pattern + PREVIOUS_YEARWEEK
        else:
            print("Invalid check_option passed.")
        available = redis_conn.get(weekly_key_pattern)
        print("Finished Processing Pattern: ", weekly_key_pattern)
        if available and int(available):
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception as e:
        print("Exception: %s" % (e))


if __name__ == "__main__":
    if not REDIS_CONNECTION_DICT["password"]:
        raise ValueError("REDIS_PASSWORD environment variable is required")
    parser = OptionParser()

    parser.add_option(
        "-p",
        "--pattern",
        dest="pattern",
        action="store",
        help="base pattern to check"
    )
    parser.add_option(
        "-c",
        "--check",
        dest="check",
        action="store",
        help="[current/previous] week or time_value to check"
    )

    (options, args) = parser.parse_args()

    pattern = ""
    check_option = ""

    if options.pattern:
        pattern = options.pattern
    if options.check:
        check_option = options.check

    start_time = time.time()
    monitor(pattern, check_option)
    end_time = time.time()
    time_taken = end_time - start_time
    print("Total Time Taken: ", time_taken, "seconds")
