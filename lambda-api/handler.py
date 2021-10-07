import sys

sys.path.insert(0, "package/")
import boto3
from boto3.dynamodb.conditions import Attr, Contains, Key
from pprint import pprint
import json

from route import Route
from writer import Writer

from decimal import Decimal

# 型を変換するやつ
def decimal_default_proc(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError


placehold_dir_path = "./json/placehold/"
convenience_json_path = placehold_dir_path + "convenience.json"
file_not_found_error_json = {"statusCode": 404, "body": "File Not Found"}
item_not_found_error_json = {"statusCode": 404, "body": "Item Not Found"}

dynamodb = boto3.resource("dynamodb", region_name="ap-northeast-1")
table = dynamodb.Table("Meal")


def convenience() -> dict:
    try:
        with open(convenience_json_path, "r") as f:
            data = json.load(f)
            return data
    except FileNotFoundError:
        return file_not_found_error_json

def sandwich() -> list:
    response = table.query(
        IndexName="MealClassifyIndex",
        KeyConditionExpression=Key("Classification").eq("sandwich"),
    )
    return response["Items"]


def onigiri() -> list:
    response = table.query(
        IndexName="MealClassifyIndex",
        KeyConditionExpression=Key("Classification").eq("onigiri"),
    )
    return response["Items"]


def bento() -> list:
    response = table.query(
        IndexName="MealClassifyIndex",
        KeyConditionExpression=Key("Classification").eq("bento"),
    )
    return response["Items"]


def bread() -> list:
    response = table.query(
        IndexName="MealClassifyIndex",
        KeyConditionExpression=Key("Classification").eq("bread"),
    )
    return response["Items"]


def shortage(params: list) -> list:
    nutrition = params["Nutrition"]
    index = "Status" + nutrition + "GSI"
    response = table.query(
        IndexName=index,
        KeyConditionExpression=Key("Status").eq("exist"),
        ScanIndexForward=False,
    )
    return json.dumps(response["Items"], default=decimal_default_proc)


def search(params: list) -> list:
    # とりま単語のみの場合
    # TODO: 複数検索に対応させる
    keyword = params["Keyword"]
    response = table.scan(
        FilterExpression=Attr("Name").contains(keyword),
        ProjectionExpression="#name, Id, Classification",
        ExpressionAttributeNames={"#name": "Name"},
    )
    return response["Items"]


def item(params: list) -> list:
    id = params["Id"]
    classification = params["Classification"]
    response = table.get_item(Key={"Id": id, "Classification": classification})
    return json.dumps(response["Item"], default=decimal_default_proc)


writer = Writer()
route = Route(writer=writer)
# 仮でおいてあるやつ
route.add(path="convenience", func=convenience)
# 実際に取得したやつ
route.add(path="sandwich", func=sandwich)
route.add(path="onigiri", func=onigiri)
route.add(path="bento", func=bento)
route.add(path="bread", func=bread)
route.add(path="search", func=search)
route.add(path="shortage", func=shortage)
# 詳細取得するやつ
route.add(path="item", func=item)

# 起点
def lambda_handler(event, context):
    if "queryStringParameters" in event:
        route.run(
            path=event["pathParameters"]["proxy"],
            params=event["queryStringParameters"],
        )
    else:
        route.run(path=event["pathParameters"]["proxy"])
    resp = route.get_result()
    return resp
