import urllib.request
import json

def test_endpoint(url):
    try:
        print(f"Chamando {url}...")
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            status = response.getcode()
            body = response.read().decode('utf-8')
            print(f"Status: {status}")
            print(f"Body: {json.dumps(json.loads(body), indent=2)}")
    except Exception as e:
        print(f"Erro ao chamar {url}: {e}")

if __name__ == "__main__":
    test_endpoint("http://127.0.0.1:8000/api/v1/summary")
    test_endpoint("http://127.0.0.1:8000/api/v1/analytics/temporal-series")
