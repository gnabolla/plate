import requests

# Test dashboard template rendering
dashboards = [
    '/officer/dashboard',
    '/cashier/dashboard', 
    '/admin/dashboard'
]

for dashboard in dashboards:
    response = requests.get(f'http://localhost:8001{dashboard}')
    print(f"\n{dashboard}:")
    print(f"  Status: {response.status_code}")
    print(f"  Content-Type: {response.headers.get('content-type')}")
    if 'text/html' in response.headers.get('content-type', ''):
        print(f"  HTML Title: {response.text[response.text.find('<title>')+7:response.text.find('</title>')]}")
    else:
        print(f"  Response: {response.text[:100]}")