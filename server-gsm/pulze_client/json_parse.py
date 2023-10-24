import json

def parse_json(data: dict) -> dict:
    try:
        json_str = json.dumps(data)
        parsed_data = json.loads(json_str)
        return parsed_data
    except json.JSONDecodeError:
        return {"error": "Invalid JSON data"}
