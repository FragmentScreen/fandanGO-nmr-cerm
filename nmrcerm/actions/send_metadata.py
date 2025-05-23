from nmrcerm.db.sqlite_db import get_visit_id, get_metadata_path
from datetime import datetime
from dotenv import load_dotenv
import json
from fGOaria import AriaClient, Bucket, Field, Record
import uuid
import time
from functools import wraps

load_dotenv()

def retry_on_error(max_retries=3, delay=1, backoff=1.5):
    """
    Decorator to retry operations on failure with exponential backoff
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries (seconds)
        backoff: Multiplier for delay on each retry
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            for attempt in range(max_retries):
                try:
                    result = func(*args, **kwargs)
                    if attempt > 0:
                        print(f"✓ Success on attempt {attempt + 1}")
                    return result
                except Exception as e:
                    if attempt == max_retries - 1:
                        print(f"✗ Final attempt {attempt + 1} failed: {e}")
                        raise e
                    print(f"✗ Attempt {attempt + 1} failed: {e}")
                    print(f"  Retrying in {current_delay:.1f}s...")
                    time.sleep(current_delay)
                    current_delay *= backoff
            return None
        return wrapper
    return decorator

@retry_on_error(max_retries=3, delay=1, backoff=2)
def push_record_safe(visit, record):
    """Safely push a record with retry logic"""
    return visit.push(record)

@retry_on_error(max_retries=5, delay=2, backoff=1.5)
def push_field_safe(visit, field):
    """Safely push a field with retry logic and longer delays"""
    return visit.push(field)

def send_metadata(project_name):
    """
    Function that sends FandanGO project info to ARIA with robust error handling

    Args:
        project_name (str): FandanGO project name

    Returns:
        success (bool): if everything went ok or not
        info (dict): bucket, record and field ARIA data
    """

    success = True
    info = None
    failed_operations = []

    try:
        visit_id = get_visit_id(project_name)
        print(f"visit_id:{visit_id}")
        metadata_path = get_metadata_path(project_name)
        print(f"metadata_path:{metadata_path}")

        aria = AriaClient(True)
        aria.login()

        today = datetime.today()
        visit = aria.new_data_manager(int(visit_id), 'visit', False)
        embargo_date = datetime(today.year + 3, today.month, today.day).strftime('%Y-%m-%d')
        bucket = visit.create_bucket(embargo_date)
        print(f"Bucket ID: {bucket.id}")

        # experiment metadata
        with open(metadata_path, 'r') as file:
            samples_data = json.load(file)

        created_records = []
        created_fields = []
        
        print(f"Processing {len(samples_data)} samples...")

        for sample_idx, sample in enumerate(samples_data):
            sample_name = sample['name']
            sample_uuid = str(uuid.uuid4())
            
            print(f"\n[{sample_idx + 1}/{len(samples_data)}] Processing sample: {sample_name}")
            
            try:
                # Create sample record
                sample_record = Record(bucket.id, 'TestSchema', f"{sample_name}: {sample_uuid}")
                push_record_safe(visit, sample_record)
                print(f"✓ Sample record created: {sample_record.id}")
                
                sample_data = {k: v for k, v in sample.items() if k != 'experimentDTO'}
                
                # Create field for sample data
                sample_field = Field(sample_record.id, 'TestFieldType', sample_data)
                print('  Pushing sample field...')
                
                push_field_safe(visit, sample_field)
                print(f"✓ Sample field created: {getattr(sample_field, 'id', 'unknown')}")
                
                # Rate limiting
                time.sleep(0.5)
                
                if not isinstance(sample_field, Field):
                    failed_operations.append(f"Sample field creation failed for {sample_name}")
                    continue
                    
                created_records.append({
                    'type': 'sample',
                    'name': sample_name,
                    'uuid': sample_uuid,
                    'record_id': sample_record.id
                })
                
                created_fields.append({
                    'record_id': sample_record.id,
                    'field_id': getattr(sample_field, 'id', 'unknown'),
                    'field_type': 'TestFieldType',
                    'description': f'Sample data for {sample_name}',
                    'data': sample_data,
                    'field_metadata': sample_field.__dict__ if hasattr(sample_field, '__dict__') else {},
                    'field_object': sample_field
                })

                if 'experimentDTO' in sample and sample['experimentDTO']:
                    print(f"  Processing {len(sample['experimentDTO'])} datasets...")
                    
                    for dataset_idx, experiment_dto in enumerate(sample['experimentDTO']):
                        dataset_id = experiment_dto['id']
                        print(f"    [{dataset_idx + 1}] Processing dataset: {dataset_id}")
                        
                        try:
                            dataset_record = Record(bucket.id, 'TestSchema', f"dataset_{dataset_id}_experiment_{sample_uuid}")
                            push_record_safe(visit, dataset_record)
                            print(f"    ✓ Dataset record created: {dataset_record.id}")
                            
                            dataset_field = Field(dataset_record.id, 'TestFieldType', experiment_dto, description=f"{sample_name}_Dataset_{dataset_id}")
                            print(f"      Pushing dataset field...")
                            
                            push_field_safe(visit, dataset_field)
                            print(f"    ✓ Dataset field created: {getattr(dataset_field, 'id', 'unknown')}")
                            
                            time.sleep(0.5)

                            if not isinstance(dataset_field, Field):
                                failed_operations.append(f"Dataset field creation failed for {dataset_id}")
                                continue
                                
                            created_records.append({
                                'type': 'dataset',
                                'dataset_id': dataset_id,
                                'parent_uuid': sample_uuid,
                                'record_id': dataset_record.id
                            })
                            
                            created_fields.append({
                                'record_id': dataset_record.id,
                                'field_id': getattr(dataset_field, 'id', 'unknown'),
                                'field_type': 'TestFieldType',
                                'description': f"{sample_name}_Dataset_{dataset_id}",
                                'data': experiment_dto,
                                'field_metadata': dataset_field.__dict__ if hasattr(dataset_field, '__dict__') else {},
                                'field_object': dataset_field
                            })

                            if 'experimentList' in experiment_dto and experiment_dto['experimentList']:
                                print(f"      Processing {len(experiment_dto['experimentList'])} experiments...")
                                
                                for exp_idx, experiment in enumerate(experiment_dto['experimentList']):
                                    expno = experiment['expno']
                                    print(f"        [{exp_idx + 1}] Processing experiment: {expno}")
                                    
                                    try:
                                        experiment_record = Record(bucket.id, 'TestSchema', f"experiment_{expno}_dataset_{dataset_id}")
                                        push_record_safe(visit, experiment_record)
                                        print(f"        ✓ Experiment record created: {experiment_record.id}")
                                        
                                        experiment_field = Field(experiment_record.id, 'TestFieldType', experiment)
                                        print(f"          Pushing experiment field...")
                                        
                                        push_field_safe(visit, experiment_field)
                                        print(f"        ✓ Experiment field created: {getattr(experiment_field, 'id', 'unknown')}")
                                        
                                        time.sleep(0.3)
                                        
                                        if not isinstance(experiment_field, Field):
                                            failed_operations.append(f"Experiment field creation failed for {expno} in dataset {dataset_id}")
                                            continue
                                            
                                        created_records.append({
                                            'type': 'experiment',
                                            'expno': expno,
                                            'dataset_id': dataset_id,
                                            'record_id': experiment_record.id
                                        })
                                        
                                        created_fields.append({
                                            'record_id': experiment_record.id,
                                            'field_id': getattr(experiment_field, 'id', 'unknown'),
                                            'field_type': 'TestFieldType',
                                            'description': f'Experiment {expno} data',
                                            'data': experiment,
                                            'field_metadata': experiment_field.__dict__ if hasattr(experiment_field, '__dict__') else {},
                                            'field_object': experiment_field
                                        })
                                        
                                    except Exception as e:
                                        failed_operations.append(f"Experiment {expno} in dataset {dataset_id}: {str(e)}")
                                        print(f"        ✗ Failed to process experiment {expno}: {e}")
                                        
                        except Exception as e:
                            failed_operations.append(f"Dataset {dataset_id}: {str(e)}")
                            print(f"    ✗ Failed to process dataset {dataset_id}: {e}")
                            
            except Exception as e:
                failed_operations.append(f"Sample {sample_name}: {str(e)}")
                print(f"✗ Failed to process sample {sample_name}: {e}")

        # Summary
        print(f"\n{'='*60}")
        print("UPLOAD SUMMARY")
        print(f"{'='*60}")
        print(f"✓ Records created: {len(created_records)}")
        print(f"✓ Fields created: {len(created_fields)}")
        
        if failed_operations:
            print(f"✗ Failed operations: {len(failed_operations)}")
            for failure in failed_operations:
                print(f"  - {failure}")
        else:
            print("✓ All operations completed successfully!")
            
        info = {
            'bucket': bucket.__dict__,
            'records_created': len(created_records),
            'fields_created': len(created_fields),
            'records_detail': created_records,
            'fields_detail': created_fields,
            'failed_operations': failed_operations
        }
        
    except Exception as e:
        success = False
        info = str(e)
        print(f"Critical Error: {e}")

    return success, info

def perform_action(args):
    success, info = send_metadata(args['name'])
    results = {'success': success, 'info': info}
    return results
