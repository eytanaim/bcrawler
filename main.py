#!/bin/python3.8
from asyncio import exceptions
from contextlib import suppress
from itertools import cycle
import string
import random
#port boto3
#mport botocore.exceptions
from concurrent.futures.thread import ThreadPoolExecutor
import concurrent.futures
import logging
import re
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
logger.setLevel(logging.DEBUG)
logger.setLevel(logging.INFO)

urllib3.disable_warnings()

threads_count = 5

class Empty:
    pass

def urls():
    # return ["https://myaccount.blob.core.windows.net/{bucket_name}"]
    # return ["http://{bucket_name}.storage.googleapis.com"]
    regions = [
        "af-south-1",
        "ap-east-1",
        "ap-northeast-1",
        "ap-northeast-2",
        "ap-northeast-3",
        "ap-south-1",
        "ap-southeast-1",
        "ap-southeast-2",
        "ca-central-1",
        "eu-central-1",
        "eu-north-1",
        "eu-south-1",
        "eu-west-1",
        "eu-west-2",
        "eu-west-3",
        "me-south-1",
        "sa-east-1",
        "us-east-1",
        "us-east-2",
        "us-west-1",
        "us-west-2"
        ]
    protocols = [ "http", "https" ]
    urls = [ f"{proto}://{{bucket_name}}.s3.{r}.amazonaws.com"  for r in regions for proto in protocols ]
    return urls

def scan_bucket(b: str):
    result = Empty()
    result.bucket = b
    result.exists = False
    result.public = False
    result.details = ""
    requests_methods = [ requests.get, requests.head ]
    try:
        url = random.choice(urls()).format(bucket_name=b)
        
        method = random.choice(requests_methods)
        r = method(url, verify=False)
        logger.debug(f"{url}: {r.status_code}")
        if r.status_code == 301:
            r = method(f"https://{b}.s3.amazonaws.com")
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
        logger.exception("Rate limit...")
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
    if name[0] == "." or name[-1:] == ".":
        return False
    if name[0] == "-" or name[-1:] == "-":
        return False
    if name.find("..") != -1:
        return False
    if re.search(r"[^a-z0-9-.]", name):
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

def file_list(file: str):
    loaded_companies = [ line.rstrip() for line in open(file, 'r') ]
    companies = map(lambda a: a.lower(), loaded_companies)
    out_companies = []
    for company in companies:
        if " " not in company:
            out_companies.append(company)
        else:
            out_companies.extend(company.split(" "))
            out_companies.append(company.replace(" ", "-"))
            out_companies.append(company.replace(" ", "."))
    return sorted(set(out_companies))

def words_and_companies():
    l1 = file_list(file="companies.list")
    l2 = file_list(file="words.list")
    l = l1 + l2
    for i in l:
        for j in l:
            yield j + i
            yield j + "-" + i
            yield j + "." + i

# c = company_list()
# logger.info(len(list(c)))
# buckets = ["sdf", "aaa", "aab", "pivot-development", "imperva-snapshot-cloudformation", "Sdf"]
buckets = ["pivot-development"]

names = name_generator(3)
# names = file_list(file="companies.list")
names = file_list(file="words.list")
names = filter(bucket_name_validator, names)
buckets = names
buckets = list(names)

logger.info(f"Scanning  {len(buckets)}")
#[next(names) for _ in range(1000)]
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
                        with open('aws_exist_buckets.list', 'a') as fp:
                            fp.write("%s\n" % a.bucket)
                    else:
                        with open('aws_none_exist_buckets.list', 'a') as fp:
                                fp.write("%s\n" % a.bucket)
                    if a.public:
                        elasped_time = datetime.now() - start_time
                        elasped_time.total_seconds()
                        public = public + 1
                        public_buckets.append(a.bucket)
                        print(f"scan rate: 1 per {round(elasped_time.total_seconds() / public, 0)} seconds. public-per-open: {public}/{exists} - {round(100 * public/exists, 2)}% - public-per-guess: {public}/{tries} - {round(100 * public/tries, 2)}% - exists-per-guess: {exists}/{tries} - {round(100 * exists/tries, 2)}% - Bucket {a.bucket} is open to the world! details: {a.details}")
                        with open('aws_public_buckets.list', 'a') as fp:
                            fp.write("%s\n" % a.bucket)
            except Exception as e:
                logger.exception("Something went wrong with future")
    except Exception as e:
        logger.exception("Something went wrong with pool creation")
    
