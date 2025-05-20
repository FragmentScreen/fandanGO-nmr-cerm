import configparser
import os
import json
import requests
import jwt
import pprint as pp
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

metadata_server = os.getenv("BASE_URL")
user = os.getenv('USERNAME')
password = os.getenv('PASSWORD')

config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config.yaml'))
metadata_output_path = config['METADATA'].get('OUTPUT_PATH')

def generate_experiment_metadata(vid: str) -> Dict[str, Any]:
    """
    Function that generates metadata for a FandanGO project based on external system

    Args:
        vid (str): Visit ID for the project
        
    Returns:
        Dict: Dictionary containing success status and metadata info
    """
    try:
        token = login(user, password)
        
        api_response = call_protected(token, vid)
        
        token_info = decode(token)
        
        json_path = f"{metadata_output_path}/project_{vid}.json"
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        
        metadata = {
            "vid": vid,
            "api_response": api_response,
            "token_info": token_info
        }
        
        with open(json_path, 'w') as f:
            json.dump(metadata, f, indent=2)
            
        return {
            "success": True, 
            "info": {
                "metadata_path": json_path
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "info": {
                "error": str(e)
            }
        }

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
    success, info = generate_experiment_metadata(args['vid'])
    results = {'success': success, 'info': info}
    return results