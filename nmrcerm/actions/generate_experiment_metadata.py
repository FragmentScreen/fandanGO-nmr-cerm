import configparser
import os
import json
import requests
import pprint as pp
from typing import List, Dict, Any
from dotenv import load_dotenv
from nmrcerm.db.sqlite_db import update_project

load_dotenv()

metadata_server = os.getenv("CERM_BASE_URL")
user = os.getenv('CERM_USERNAME')
password = os.getenv('CERM_PASSWORD')

config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config.yaml'))
metadata_output_path = config['METADATA'].get('OUTPUT_PATH')

def generate_experiment_metadata(project_name: str, vid: str) -> Dict[str, Any]:
    """
    Function that generates metadata for a FandanGO project based on external system

    Args:
        project_name (str): FandanGO project name
        vid (str): Visit ID for the project
        
    Returns:
        Dict: Dictionary containing success status and metadata info
    """
    try:
        print(f"user:{user}")
        print(f"password:{password}")
        token = login(user, password)
        
        api_response = call_protected(token, vid)
        
        token_info = decode(token)
        
        json_path = f"{metadata_output_path}/project_{project_name}_{vid}.json"
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        
        metadata = {
            "vid": vid,
            "api_response": api_response,
            "token_info": token_info
        }
        
        with open(json_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        success = True
        update_project(project_name, 'visit_id', vid)
        update_project(project_name, 'metadata_path', json_path)
        info = {"metadata_path": json_path}

    except Exception as e:
        success = False
        info = str(e)

    return success, info

def login(username: str, password: str) -> str:
    r = requests.post(f"{metadata_server}/auth/login", json={"username": username, "password": password}, verify=False)
    #r = requests.post(f"{BASE_URL}/auth/login",json={"username": username, "password": password}, verify="spring.crt")
    r.raise_for_status()
    token = r.json()["token"]
    print("Token JWT ottenuto:", token)
    return token

def call_protected(token: str, vid: str) -> Dict[str, Any]:
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{metadata_server}/fandango/export/json/{vid}", headers=headers, verify=False)
    #r = requests.get(f"{BASE_URL}/fandango/export/json", headers=headers, verify="spring.crt")
    r.raise_for_status()
    print("Risposta API:", r.text)
    pp.pprint(r.text)
    return r.json()  

def decode(token: str):
    decoded = jwt.decode(token, "mysupersecretkeythatshouldbestoredsafe",
    algorithms=["HS256"])
    print("Payload decodificato:", decoded)
    return decoded

def perform_action(args):
    success, info = generate_experiment_metadata(args['name'], args['vid'])
    results = {'success': success, 'info': info}
    return results