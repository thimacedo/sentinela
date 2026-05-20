import httpx
import asyncio

async def test_connectivity():
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get('https://httpbin.org/get')
            print(f'SUCCESS: httpbin.org status: {r.status_code}')
            return True
    except Exception as e:
        print(f'ERROR: httpbin.org failed: {e}')
        return False

async def test_zyte_endpoint():
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get('https://api.zyte.com/v1/extract')
            print(f'SUCCESS: Zyte endpoint reachable, status: {r.status_code}')
            return True
    except Exception as e:
        print(f'ERROR: Zyte endpoint failed: {e}')
        return False

if __name__ == '__main__':
    print('Testing basic connectivity...')
    result1 = asyncio.run(test_connectivity())
    print('Testing Zyte endpoint...')
    result2 = asyncio.run(test_zyte_endpoint())
    
    if result1 and result2:
        print('\nAll connectivity tests PASSED')
    else:
        print('\nSome connectivity tests FAILED')
