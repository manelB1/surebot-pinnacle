from datetime import datetime
import pytz
from dateutil import parser
import json
from flask import Flask, request, Response
from playwright.sync_api import sync_playwright

import requests

app = Flask(__name__)


ROUTER_PATH = '/api/v1/bot'

MARKETS = {
    "HANDCAP ASIATICO": "Handicap – Game",
    "TOTALS": "Total – Game"
}

def authenticate(authorization):
    
    authorization = json.loads(request.data).get("authorization")

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
    
    if not authorization.get('validate') or parser.isoparse(authorization.get('validate')) < datetime.now(pytz.utc):
        
        response = requests.post('https://guest.api.arcadia.pinnacle.com/0.1/sessions', headers=headers, json=json_data)
        

        if response.status_code <= 300:
            responseData = response.json()

            token = responseData.get('token')
            expiresAt = responseData.get('expiresAt')

            authorization['validate'] = expiresAt
            authorization['token'] = token
    
    return authorization


@app.route(f"{ROUTER_PATH}/check_game/")
def check_game():
    
    tip = json.loads(request.data)
    success = False

    with sync_playwright() as p:
        data = {
            "payout": None,
        }
        
        home = tip.get('homeTeam')
        away = tip.get('awayTeam')
        stake = tip.get('stake')
        market = tip.get('market')
        market_type = tip.get('marketType')
        point = tip.get('point')
        
        game_url: str = tip.get('gameUrl')
        
        browser = p.chromium.launch(headless=False)
        
        page = browser.new_page()
        
        page.goto(game_url)
        
        title = page.title()
        
        # page.get_by_title(home).click()
        
        page.wait_for_timeout(1000)
        
        # Localiza o botão para expandir todos mercados
        page.locator('div[class*="style_showAll__"]').click()
        for button in page.locator('button[class*="style_toggleMarkets__"]').all():
            button.click()
        
        if point > 0:
            point = f'+{point}'
        else:
            point = f'-{point}'
            
        page.locator(f'button[title="{point}"]').click()
        page.wait_for_timeout(2000)
                
        # Localiza os inputs para digitar o valor da aposta
        input_value = page.locator(".betslipCardStakeWinInput > div > div:nth-child(1) > input[type=text]")
        input_win = page.locator(".betslipCardStakeWinInput > div > div:nth-child(2) > input[type=text]")
        
        # Preenche o valor da aposta com o campo 'Stake'
        input_value.fill(str(stake))
        
        # Esse é o valor do campo que calcula o valor ganho na aposta
        data["payout"] = input_win.get_attribute('value')
        
        page.wait_for_timeout(3000)
        
        if home in title and away in title:
            success = True
        
        browser.close()
    
    return Response(data["payout"],status=200 if success else 400)

@app.route(f"{ROUTER_PATH}/balance/", methods=["POST"])
def get_balance():

    authorization = json.loads(request.data).get('authorization')        
    authorization = authenticate(authorization)
    

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
    
    if not authorization.get('validate') or parser.isoparse(authorization.get('validate')) < datetime.now(pytz.utc):
    
        responseBalance = requests.get('https://guest.api.arcadia.pinnacle.com/0.1/wallet/balance', headers=headers)

        balance = responseBalance.json()
        
        getBalance = balance.get('amount')
        getCurrency = balance.get('currency')

        return Response({
            'totalAmount': getBalance,
            'currency': getCurrency
        })

@app.route(f"{ROUTER_PATH}/login/", methods=["POST"])
def login():
    authorization = json.loads(request.data).get("authorization")
    authorization = authenticate(authorization)

    return{
        "sucess": "usuario logado"
    }

@app.route(f"{ROUTER_PATH}/check_authentication/", methods=["POST"])
def check_authentication():
    authorization = json.loads(request.data).get("authorization")
    authorization = authenticate(authorization)
    
    return Response({
        "token": authorization.get("token"),
        "validate": authorization.get("validate")
    })




