from datetime import datetime
import pytz
from dateutil import parser
import json
from flask import Flask, request
import requests

app = Flask(__name__)


def authenticate(authorization):
    headers = {
        'authority': 'guest.api.arcadia.pinnacle.com',
        'accept': 'application/json',
        'accept-language': 'pt-BR,pt;q=0.7',
        'content-type': 'application/json',
        'origin': 'https://www.pinnacle.com',
        'referer': 'https://www.pinnacle.com/',
        'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Brave";v="114"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'sec-gpc': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
        'x-api-key': 'CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R',
        'x-device-uuid': 'cf6477ed-f5e13873-9631ac49-0725adfb',
    }

    json_data = {
        'username': authorization.get('username'),
        'password': authorization.get('password'),
        'captchaToken': '',
        'trustCode': '6278097a32b0149c100b11dede550896c3dc8fe702dc8742b98207c9c0c687b4',
        'geolocation': '',
    }
    
    print(datetime.now())
    if not authorization.get('validate') or parser.isoparse(authorization.get('validate')) < datetime.now(pytz.utc):
        
        response = requests.post('https://guest.api.arcadia.pinnacle.com/0.1/sessions', headers=headers, json=json_data)

        if response.status_code <= 300:
            response_data = response.json()
            print(response_data)
            token = response_data.get('token')
            expiresAt = response_data.get('expiresAt')
            lastUseAt = response_data.get('lastUsedAt')
            createdAt = response_data.get('createdAt')
            userName = response_data.get('username')

            headers_with_session = headers.copy()
            headers_with_session['x-session'] = token
        
            authorization['validate'] = expiresAt
            authorization['token'] = token
            authorization['lastUseAt'] = lastUseAt
            authorization['createdAt'] = createdAt
            authorization['username'] = userName

        else:
            print(response.status_code)
            
       

   
    return authorization



@app.route("/api/v1/bot/balance/", methods=["POST"])
def get_balance():

    authorization = json.loads(request.data).get('authorization')        
    authorization = authenticate(authorization)

    if not authorization.get('token'):
        return {
            'error': 'Usuário não autenticado. Faça a autenticação primeiro.'
        }


    headers = {
        'authority': 'guest.api.arcadia.pinnacle.com',
        'accept': 'application/json',
        'accept-language': 'pt-BR,pt;q=0.5',
        'content-type': 'application/json',
        'origin': 'https://www.pinnacle.com',
        'referer': 'https://www.pinnacle.com/',
        'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Brave";v="114"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'sec-gpc': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
        'x-api-key': 'CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R',
        'x-device-uuid': 'cf6477ed-f5e13873-9631ac49-0725adfb',
        'x-session': authorization.get('token'),
    }

    response_balance = requests.get('https://guest.api.arcadia.pinnacle.com/0.1/wallet/balance', headers=headers)
    balance = response_balance.json()
    getBalance = balance.get('amount')
    getCurrency = balance.get('currency')

    return {
        'totalAmount': getBalance,
        'currency': getCurrency
    }

@app.route("/api/v1/bot/check_authentication/", methods=["POST"])
def check_authentication( ):
    authorization = json.loads(request.data).get("authorization")
    authorization = authenticate(authorization)
    
    if not authorization.get("validate") or parser.isoparse(authorization.get("validate")) < datetime.now(pytz.utc):

        return {
            "Usuario não autentificado!!"
        }
    else:
        return {

            "token": authorization.get("token"),
            "validate": authorization.get("validate"),
            "lastUseAt": authorization.get("lastUseAt"),
            "createdAt": authorization.get("createdAt"),
            "username": authorization.get("username")
        }




