import traceback
import boto3
import urllib
from pathlib import Path
from PyPDF2 import PdfReader, PdfWriter

def lambda_handler(event, context):
  print(event)
  s3 = boto3.resource("s3")
  dynamodb = boto3.resource('dynamodb')

  table = dynamodb.Table('pdf')
  uploaded_s3_info = event["Records"][0]["s3"]
  bucket_name, key = uploaded_s3_info["bucket"]["name"], uploaded_s3_info["object"]["key"]
  key = urllib.parse.unquote(key)
  uploaded_file = s3.Object(bucket_name, key)
  file_name = Path(key).name
  file_id = Path(file_name).stem
  origin_file_name = Path(uploaded_file.metadata['name']).stem if 'name' in uploaded_file.metadata else file_id
  download_path = f"/tmp/{file_name}"
  output_file_name = f"{origin_file_name}_decrypted.pdf"
  output_path = f"/tmp/{output_file_name}"

  table.update_item(
    Key={
      'id': file_id
    },
    AttributeUpdates={
      'status': {
          'Value': 'InProcessing',
          'Action': 'PUT'
      }
    },
  )

  try:
    uploaded_file.download_file(download_path)
    reader = PdfReader(download_path, password="")
    writer = PdfWriter()
    for page in reader.pages:
      writer.add_page(page)
    writer.write(output_path)
    print(f"{reader.getNumPages()} pages processed")

    output_s3_info = s3.Object(bucket_name, f"g/{output_file_name}")
    output_s3_info.upload_file(output_path)

  except Exception:
    traceback.print_exc()
    table.update_item(
      Key={
        'id': file_id
      },
      AttributeUpdates={
        'status': {
            'Value': 'Error',
            'Action': 'PUT'
        },
      },
    )
    return

  table.update_item(
    Key={
      'id': file_id
    },
    AttributeUpdates={
      'status': {
          'Value': 'Done',
          'Action': 'PUT'
      },
      's3': {
          'Value': f"s3://{bucket_name}/g/{output_file_name}",
          'Action': 'PUT'
      }
    },
  )

lambda_handler({
  "Records": [
    {
      "eventVersion": "2.1",
      "eventSource": "aws:s3",
      "awsRegion": "us-west-2",
      "eventTime": "2022-09-27T01:10:45.975Z",
      "eventName": "ObjectCreated:Put",
      "userIdentity": {
        "principalId": "A1C1NFAPH1ED"
      },
      "requestParameters": {
        "sourceIPAddress": "73.97.44.33"
      },
      "responseElements": {
        "x-amz-request-id": "PF3TDTTHQRKQ3F7S",
        "x-amz-id-2": "LeAMuRpb2MltYRb7OcCzmRyatffdpJX4sDuCSsxi4QYEtsyV/k8XmkF+l7glSF3aw+IHpnbF8p6WWcKjCY9OpHUMl9WDmD5y"
      },
      "s3": {
        "s3SchemaVersion": "1.0",
        "configurationId": "pdf uploaded",
        "bucket": {
          "name": "my-smart-pdf",
          "ownerIdentity": {
            "principalId": "A1C1NFAPH1ED"
          },
          "arn": "arn:aws:s3:::my-smart-pdf"
        },
        "object": {
          "key": "upload/LCRgoTXhr6VXpidhfJ9L5A==.pdf",
          "size": 1260716,
          "eTag": "2c2460a135e1afa557a627617c9f4be4",
          "sequencer": "0063324D95D39D262E"
        }
      }
    }
  ]
}, None)