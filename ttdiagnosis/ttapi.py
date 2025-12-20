import requests

class TTApi:
    """TycheTools backend API helper"""
    def __init__(self, client):
        self.client = client
        self.base_url = f"https://{self.client}-api.tychetools.com"
        self.headers = {
            "content-type": "application/json"
        }

    def auth(self, user, password):
        """Auth."""
        url = f"{self.base_url}/auth/token/"
        json_data = {"email": user, "password": password}
        req = self.req_post(url, json_data)
        access_token = req.json()["access"]
        self.headers["Authorization"] = f"Bearer {access_token}"
        print(f"auth response: {req.status_code}")

    def req_get(self, url, params=None):
        """API GET interface"""
        if params:
            return requests.get(url, headers=self.headers, params=params,
                timeout=60)
        return requests.get(url, headers=self.headers, timeout=60)

    def req_post(self, url, json_data):
        """API POST interface"""
        return requests.post(url, headers=self.headers, json=json_data,
            timeout=30)

    def req_put(self, url, json_data):
        """API PUT interface"""
        return requests.put(url, headers=self.headers, json=json_data,
            timeout=30)
