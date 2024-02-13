import requests
import json
from ..utils.addon_logger import addon_logger

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
        addon_logger.info(f'Response status code:{str(statusCode)}')
        if statusCode == 200:
            print("Successfully found the LICENSE KEY in the database.")
            addon_logger.info("Successfully found the LICENSE KEY in the database.")
            data = json.loads(response.text)['body']
            
            return True, data, None
        elif statusCode == 409:
            print("user exist! returning UUID from database")
            addon_logger.info("user exist! returning UUID from database")
            data = json.loads(response.text)['body']
            return True, data, None
        elif statusCode == 401:
            addon_logger.error("Licence key was not valid")
            print(f"Licence key was not valid")
            return False, None, json.loads(response.text)['body']
        elif statusCode == 500:
            addon_logger.error("Internal server error. Please try again or contact support")
            print(f"Internal server error. Please try again or contact support")
            return False, None, json.loads(response.text)['body']

    except Exception as e:
        error =f"error validating license: {e}"
        print(error)
        addon_logger.error(error)
        return {False, None,str(e)}