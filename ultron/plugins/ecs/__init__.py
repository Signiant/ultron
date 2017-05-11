import boto3
import json

def log (message):
    print id() + ": " + message

def id():
    return "ecs"

def check_versions():
    log("hello world")