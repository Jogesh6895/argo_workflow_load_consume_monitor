import os
import time
import redis
import datetime


REDIS_CONNECTION_DICT = {
    "host": os.getenv("REDIS_HOST", "localhost"),
    "port": int(os.getenv("REDIS_PORT", 6379)),
    "username": os.getenv("REDIS_USERNAME", ""),
    "password": os.getenv("REDIS_PASSWORD"),
    "db": int(os.getenv("REDIS_DB", 0)),
}

NOW_TIME_OBJ = datetime.datetime.now()
CURRENT_YEARWEEK = "%04d%02d" % (NOW_TIME_OBJ.year, NOW_TIME_OBJ.isocalendar()[1])
REDIS_COMPLETION_STATUS_KEY = "ARGO_STATUS:JOB_LOADER:" + CURRENT_YEARWEEK
STATUS_KEY_TTL = 14400  # 4 Hours
REDIS_JOB_QUEUE_KEY = "queue:argo_job_queue"


def load_jobs():
    try:
        redis_connection = redis.Redis(**REDIS_CONNECTION_DICT)
        for i in range(10):
            job_val = "####>>>> Script - 1 <<<<####" + str(i)
            redis_connection.lpush(REDIS_JOB_QUEUE_KEY, job_val)
            print("Pushed job to redis queue 'queue:argo_job_queue' -> ", job_val)
            time.sleep(1)
    except Exception as e:
        print("Exception Occured: %s" % (e))


def set_complete_status():
    try:
        redis_connection = redis.Redis(**REDIS_CONNECTION_DICT)
        redis_connection.setex(REDIS_COMPLETION_STATUS_KEY, STATUS_KEY_TTL, 1)
        print("Status Key successfully Set: ", REDIS_COMPLETION_STATUS_KEY)
    except Exception as e:
        print("Exception Occured while seting compltion status: %s" % (e))


if __name__ == "__main__":
    if not REDIS_CONNECTION_DICT["password"]:
        raise ValueError("REDIS_PASSWORD environment variable is required")
    start_time = time.time()
    load_jobs()
    set_complete_status()
    end_time = time.time()
    time_taken = end_time - start_time
    print("Total Time Taken: ", time_taken, "seconds")
