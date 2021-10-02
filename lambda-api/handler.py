import sys

sys.path.insert(0, "package/")
import boto3
from boto3.dynamodb.conditions import Key
from pprint import pprint
import json

from route import Route
from writer import Writer

from decimal import Decimal
def decimal_default_proc(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError


placehold_dir_path = "./json/placehold/"
convenience_json_path = placehold_dir_path + "convenience.json"
file_not_found_error_json = {"statusCode": 404, "body": "File Not Found"}
item_not_found_error_json = {"statusCode": 404, "body": "Item Not Found"}

dynamodb = boto3.resource("dynamodb", region_name="ap-northeast-1")


def convenience() -> dict:
    try:
        with open(convenience_json_path, "r") as f:
            data = json.load(f)
            return data
    except FileNotFoundError:
        return file_not_found_error_json


def onigiri() -> list:
    table = dynamodb.Table("Meal")

    response = table.query(
        IndexName="MealClassifyIndex",
        KeyConditionExpression=Key("Classification").eq("onigiri"),
    )
    return response["Items"]


def item(id: str) -> list:
    table = dynamodb.Table("Meal")

    response = table.get_item(Key={"Id": id, "Classification": "onigiri"})
    return json.dumps(response["Item"], default=decimal_default_proc)


writer = Writer()
route = Route(writer=writer)
route.add(path="convenience", func=convenience)
route.add(path="onigiri", func=onigiri)
route.add(path="item", func=item, key="id")


def lambda_handler(event, context):
    if "queryStringParameters" in event:
        route.run(
            path=event["pathParameters"]["proxy"],
            param=event["queryStringParameters"],
        )
    else:
        route.run(path=event["pathParameters"]["proxy"])
    resp = route.get_result()
    return resp
