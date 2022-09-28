import json
import boto3

def lambda_handler(event, context):
    file_md5 = event["queryStringParameters"]["md5"]
    dynamodb = boto3.resource('dynamodb')
    s3 = boto3.client('s3')

    table = dynamodb.Table('pdf')
    result = table.get_item(Key={"id": file_md5})

    if 'Item' in result:
        ret = {}
        item = result['Item']
        ret['status'] = item['status']
        if item['status'] == "Done" and 's3' in item:
            url = item['s3'].split('/')
            output = s3.generate_presigned_url(
                ClientMethod="get_object",
                Params={
                    "Bucket": url[2],
                    "Key": '/'.join(url[3:])
                },
                ExpiresIn=1800
            )
            ret['s3'] = output

        return {
            'statusCode': 200,
            'body': json.dumps(ret),
            'headers': {
                "Access-Control-Allow-Origin": "*"
            }
        }

    return {
        'statusCode': 404,
        'body': "Job NOT FOUND",
        'headers': {
            "Access-Control-Allow-Origin": "*"
        }
    }