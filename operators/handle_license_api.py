import requests
import json

#CONSTANTS
PRODUCT_ID = "ScjwmP11MCOfPZG4SwtcPQ=="

def validate_license_api(userId, uuid, licenseType):
    try:
        url = 'https://bdzu1thiy3.execute-api.us-east-1.amazonaws.com/dev/BBPS_Premium_Licensing'
        headers = {'Content-Type': 'application/json'}
        payload = json.dumps({
            'userId': userId,
            'uuid': uuid,
            'licenseType': licenseType
        })

        response = requests.post(url, headers=headers, data=payload)
        response_json = json.loads(response.text)
        statusCode = response_json.get('statusCode', None)
        print('Response status code:', statusCode)
        if statusCode == 200:
            print("Successfully found the LICENSE KEY in the database.")
            data = json.loads(response.text)['body']
            return True, data, None
        elif statusCode == 409:
            print("user exist! returning UUID from database")
            data = json.loads(response.text)['body']
            return True, data, None
        elif statusCode == 401:
            print(f"Licence key was not valid")
            return False, None, json.loads(response.text)['body']
        elif statusCode == 500:
            print(f"Internal server error. Please try again or contact support")
            return False, None, json.loads(response.text)['body']

    except Exception as e:
        print(f"An error occurred: {e}")
        return {False, None,str(e)}
    



def verify_gumroad_license(license_key):
    url = "https://api.gumroad.com/v2/licenses/verify"
    payload = {
        "product_id": PRODUCT_ID,
        "license_key": license_key
    }
    
    try:
        response = requests.post(url, data=payload)
        
        if response.status_code == 200:
            print("Successfully verified the license.")
            return True,response.json(),None
        else:
            print(f"Failed to verify the license. Status code: {response.status_code}")
            return False, None, response.text

    except Exception as e:
        print(f"An error occurred: {e}")
        return False, None, str(e)

# Example usage
license_key = "2BF55F25-4A114A22-A73C745A-7BF010A1"
result = verify_gumroad_license(license_key)
print(result)




