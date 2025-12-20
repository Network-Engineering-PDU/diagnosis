
import os
import json
from ttdiagnosis.ttdiagnosis import TTDiagnosis


def run_diagnosis(silent=False):
    """Reads credentials from config file, performs and sends a diagnostic"""
    config_file_path = os.path.expanduser("~/.tychetools/gw.config")
    if not os.path.isfile(config_file_path):
        print("Error reading config file")
        return
    try:
        with open(config_file_path, 'r', encoding='utf-8') as file:
            config_data = json.load(file)
        backend_config = config_data.get("backend", {})
        client = backend_config.get("company")
        user = backend_config.get("user")
        password = backend_config.get("password")
    except json.JSONDecodeError as e:
        print(f"Error decoding config file: {e}")
        return
    ttdiagnosis = TTDiagnosis(client, user, password)
    diagnostic = ttdiagnosis.run()
    if not silent:
        print(json.dumps(diagnostic, indent=4))

    rsp = ttdiagnosis.send()
    print(rsp.json())

if __name__ == "__main__":
    run_diagnosis()
