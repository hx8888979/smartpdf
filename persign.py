import json
import boto3
import urllib.parse

def lambda_handler(event, context):
    file_md5 = event["queryStringParameters"]["md5"]
    file_name = urllib.parse.quote(file_md5, safe='')
    sts_client = boto3.client("sts")
    credential = sts_client.assume_role(
        RoleArn='arn:aws:iam::415377008207:role/pdf_uploader',
        RoleSessionName='uploader'
    )["Credentials"]
    session = boto3.Session(credential["AccessKeyId"], credential["SecretAccessKey"], credential["SessionToken"], "us-west-2")
    s3 = session.client("s3")
    signature = s3.generate_presigned_post(Bucket="my-smart-pdf-upload", Key=f"upload/{file_name}.pdf", Conditions=[["content-length-range", 1, 10485760], {"Content-MD5": file_md5}, ["starts-with", "$x-amz-meta-name", ""]], ExpiresIn=600)

    return {
        'statusCode': 200,
        'body': json.dumps(signature),
        'headers': {
            "Access-Control-Allow-Origin": "*"
        },
    }