import requests
import json

def validate_license_api(userId, uuid):
    try:
        url = 'https://bdzu1thiy3.execute-api.us-east-1.amazonaws.com/dev/BBPS_Premium_Licensing'
        headers = {'Content-Type': 'application/json'}
        payload = json.dumps({
            'userId': userId,
            'uuid': uuid
        })

        response = requests.post(url, headers=headers, data=payload)
        statusCode = json.loads(response.text)['statusCode']
        print('this is response = ' + str(statusCode))
        print()
        if statusCode == 200:
            print("Successfully found the LICENSE KEY in the database.")
            data = json.loads(response.text)['body']
            return True, data, None
        else:
           
            print(f"Licence key not found in database. Status code: {str(statusCode)}")
            return False, None, json.loads(response.text)['body']

    except Exception as e:
        print(f"An error occurred: {e}")
        return {False, None,str(e)}


