from nmrcerm.db.sqlite_db import get_visit_id, get_metadata_path
from datetime import datetime
from dotenv import load_dotenv
import json
from fGOaria import AriaClient, Bucket, Field

load_dotenv()

def send_metadata(project_name):
    """
    Function that sends FandanGO project info to ARIA

    Args:
        project_name (str): FandanGO project name

    Returns:
        success (bool): if everything went ok or not
        info (dict): bucket, record and field ARIA data
    """

    print(f'FandanGO will send metadata for {project_name} project to ARIA...')
    success = True
    info = None

    try:
        visit_id = get_visit_id(project_name)
        print(f"visit_id:{visit_id}")
        metadata_path = get_metadata_path(project_name)
        print(f"metadata_path:{metadata_path}")

        aria = AriaClient(True)
        aria.login()
        today = datetime.today()
        visit = aria.new_data_manager(int(visit_id), 'visit', True)
        embargo_date = datetime(today.year + 3, today.month, today.day).strftime('%Y-%m-%d')
        bucket = visit.create_bucket(embargo_date)

        # experiment metadata
        with open(metadata_path, 'r') as file:
            metadata = json.load(file)

        # for element in metadata:
        #     record = visit.create_record(bucket.id, 'TestSchema')
        #     field = Field(record.id, 'TestFieldType', element)
        #     visit.push(field)
        #     if not isinstance(field, Field):
        #         success = False


    except Exception as e:
        success = False
        info = e

    if success:
        print(f'Successfully sent metadata for project {project_name} to ARIA!')
        info = {'bucket': bucket.__dict__}

    return success, info


def perform_action(args):
    success, info = send_metadata(args['name'])
    results = {'success': success, 'info': info}
    return results
