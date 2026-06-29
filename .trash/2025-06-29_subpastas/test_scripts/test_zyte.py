import os
import httpx
import base64
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_zyte_call():
    api_key = os.getenv("ZYTE_API_KEY")
    if not api_key:
        print("ERROR: ZYTE_API_KEY not found")
        return False
    
    print(f"ZYTE_API_KEY found: {api_key[:10]}...")
    
    # Test URL
    url = "https://www.instagram.com/gleisihoffmann/"
    print(f"Testing URL: {url}")
    
    payload = {
        "url": url,
        "browserHtml": True,
        "screenshot": False,
    }
    
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "https://api.zyte.com/v1/extract",
                auth=(api_key, ""),
                json=payload,
            )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code >= 400:
            print(f"ERROR: Zyte HTTP {response.status_code}: {response.text[:200]}")
            return False
            
        data = response.json()
        html = data.get("browserHtml")
        
        if html:
            print(f"SUCCESS: Received HTML of length {len(html)}")
            # Save a sample for inspection
            os.makedirs("logs/zyte_samples", exist_ok=True)
            sample_path = f"logs/zyte_samples/gleisihoffmann_profile.html"
            with open(sample_path, "w", encoding="utf-8", errors="ignore") as f:
                f.write(html[:500000])  # Limit size
            print(f"Saved sample to {sample_path}")
            return True
        else:
            print("WARNING: No browserHtml in response")
            print(f"Response keys: {list(data.keys())}")
            if data.get("httpResponseBody"):
                print("Found httpResponseBody instead")
                # Try to decode it
                try:
                    decoded = base64.b64decode(data["httpResponseBody"]).decode("utf-8", errors="ignore")
                    print(f"Decoded body length: {len(decoded)}")
                    return True
                except Exception as e:
                    print(f"Failed to decode httpResponseBody: {e}")
            return False
            
    except Exception as e:
        print(f"ERROR: Exception during Zyte call: {str(e)}")
        return False

if __name__ == "__main__":
    import asyncio
    result = asyncio.run(test_zyte_call())
    if result:
        print("\nSUCCESS: Zyte integration test PASSED")
    else:
        print("\nFAILED: Zyte integration test FAILED")
