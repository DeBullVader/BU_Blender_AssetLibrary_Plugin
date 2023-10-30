import requests
import json

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
            print('response,',response)
            return True, data, None
        elif statusCode == 409:
            print("user exist! returning UUID from database")
            data = json.loads(response.text)['body']
            print('response,',response)
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