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
  file_id = urllib.parse.unquote(Path(file_name).stem)
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
      },
      'name': {
          'Value': uploaded_file.metadata['name'] if 'name' in uploaded_file.metadata else "",
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
    print(f"{len(reader.pages)} pages processed")

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
  