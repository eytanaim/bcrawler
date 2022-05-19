#!/bin/python3.8
from asyncio import exceptions
from contextlib import suppress
from itertools import cycle
import string
import random
import boto3
import botocore.exceptions
from concurrent.futures.thread import ThreadPoolExecutor
import concurrent.futures
import logging
import requests
import sys
import urllib3
from datetime import datetime

log_format="[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] [%(threadName)s (%(name)s)]: %(message)s "
logging.basicConfig(level=logging.INFO,
    filename="log.txt",
    format=log_format,
    # filemode='w',
    datefmt='%H:%M:%S')
logger = logging.getLogger()
console_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(console_handler)
logger.setLevel(logging.INFO)

threads_count = 10

class Empty:
    pass

def scan_bucket(b: str):
    result = Empty()
    result.bucket = b
    result.exists = False
    result.public = False
    result.details = ""
    try:
        url = f"http://{b}.s3.amazonaws.com"
        r = requests.head(url)
        logger.debug(f"{url}: {r.status_code}")
        result.details = r.status_code
        if r.status_code == 403:
            result.exists = True
        elif r.status_code // 100 != 4:
            result.exists = True
            result.public = True
    # except urllib3.exceptions.NewConnectionError as e:
    #     logger.error("Rate limit...")
    except requests.exceptions.ConnectionError as e:
        logger.error("Rate limit...")
    except Exception:
        logger.exception("Something went wrong")
    # try:
    #     s3 = boto3.resource('s3')
    #     my_bucket = s3.Bucket(b)
    #     for my_bucket_object in my_bucket.objects.all():
    #         result.exists = True
    # except botocore.exceptions.ClientError as e:
    #     expected_errors = ["AccessDenied", "NoSuchBucket"]
    #     if not any([i not in str(e) for i in expected_errors]):
    #         print(f"Unexpected exception. {str(e)}")
    return result

    

letters = string.ascii_lowercase
digits = string.digits
# dots_and_hyphens  = ".-"
dots_and_hyphens  = ""

def bucket_name_validator(name: str):
    if len(name) < 3 or len(name) > 63:
        return False
    if name[0] == "-" or name[-1:] == "-":
        return False
    return True
    
def name_generator(characters: int, offset = 1369):
    dictionary = digits + letters + "-" #+ "."
    base = len(dictionary)
    logger.info(f"There are {pow(base, characters) - offset} optional bucket names")
    for i in range(offset, pow(base, characters)):
        current = i
        name = ""
        while current != 0:
            remainder=current%base
            name = name + dictionary[remainder]
            current = current//base
        yield name

# str = ''.join(random.choice(letters) for i in range(3))
strs = [ ''.join(random.choice(letters + digits + dots_and_hyphens) for i in range(3)) for j in range(22*22*22*22) ]
# result_str = [  for j in range(100)) ]
buckets = strs
# buckets = ["sdf", "aaa", "aab", "pivot-development", "imperva-snapshot-cloudformation", "Sdf"]
buckets = ["pivot-development"]

names = name_generator(4,1369)
names = filter(bucket_name_validator, names)
buckets = [next(names) for _ in range(100)]
# print(len(list(names)))
# exit
# for b in buckets:
#     print(f"Checking bucket {b}")
#     if scan_bucket(b):
if __name__ == '__main__':
    logger.info(f"Creating thread pool #{threads_count}")
    tries = 0
    exists = 0
    public = 0
    start_time = datetime.now()
    public_buckets = []
    try:
        with ThreadPoolExecutor(max_workers=threads_count) as executor:
            try:
                futures = [ executor.submit(scan_bucket, b) for b in buckets]
                for future in concurrent.futures.as_completed(futures):
                    tries = tries + 1
                    a = future.result()
                    # print(f"Bucket {a.bucket}..")
                    if a.exists:
                        exists = exists + 1
                    if a.public:
                        elasped_time = datetime.now() - start_time
                        elasped_time.total_seconds()
                        public = public + 1
                        public_buckets.append(a.bucket)
                        print(f"scan rate: 1 per {round(elasped_time.total_seconds() / public, 0)} seconds. public-per-open: {public}/{exists} - {round(100 * public/exists, 2)}% - public-per-guess: {public}/{tries} - {round(100 * public/tries, 2)}% - exists-per-guess: {exists}/{tries} - {round(100 * exists/tries, 2)}% - Bucket {a.bucket} is open to the world! details: {a.details}")
            except Exception as e:
                logger.exception("Something went wrong with future")
    except Exception as e:
        logger.exception("Something went wrong with pool creation")
    
    with open(r'public_buckets.list', 'a') as fp:
        for b in public_buckets:
            # write each item on a new line
            fp.write("%s\n" % b)
    
