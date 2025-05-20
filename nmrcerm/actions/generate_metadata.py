import configparser
import os
import json
import requests
import jwt
import pprint as pp
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL")


def generate_experiment_metadata(username: str, password: str, vid: str) -> Dict[str, Any]:
    """
    Function that generates metadata for a FandanGO project based on external system

    Args:
        username (str): Username for authentication
        password (str): Password for authentication
        vid (str): Visit ID for the project
        
    Returns:
        Dict: Dictionary containing success status and metadata info
    """
    try:
        token = login(username, password)
        
        api_response = call_protected(token)
        
        token_info = decode(token)
        
        metadata_path = f"metadata/project_{vid}.json"
        os.makedirs(os.path.dirname(metadata_path), exist_ok=True)
        
        metadata = {
            "vid": vid,
            "api_response": api_response,
            "token_info": token_info
        }
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
            
        return {
            "success": True, 
            "info": {
                "metadata_path": metadata_path
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
    r = requests.post(f"{BASE_URL}/auth/login", json={"username": username, "password": password}, verify=False)
    #r = requests.post(f"{BASE_URL}/auth/login",json={"username": username, "password": password}, verify="spring.crt")
    r.raise_for_status()
    token = r.json()["token"]
    print("Token JWT ottenuto:", token)
    return token

def call_protected(token: str):
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{BASE_URL}/fandango/export/json/PID33131", headers=headers, verify=False)
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
    success, info = generate_experiment_metadata(args['username'], args['password'], args['vid'])
    results = {'success': success, 'info': info}
    return results

if __name__ == "__main__":
    generate_experiment_metadata()