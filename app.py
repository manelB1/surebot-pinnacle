from datetime import datetime
import pytz
from dateutil import parser
import json
from flask import Flask, request, Response
from playwright.sync_api import sync_playwright

import requests

app = Flask(__name__)


ROUTER_PATH = '/api/v1/bot'

AVAILABLES_TO_MARKET_TYPES = ['TOTAL', 'HANDICAP']

MARKETS = {
    "TOTAL": "Total –",
    "MONEY": "Money Line –",
    "HANDICAP": "Handicap –",
    "TOTALS": "Total – Game"
}

MARKET_TYPE_NAMES = {
    "UNDER": 'Menos',
    "OVER": 'Acima',
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
    
    with sync_playwright() as p:
        try:
            home = tip.get('homeTeam')
            away = tip.get('awayTeam')
            stake = tip.get('stake')
            market = tip.get('market')
            market_type = tip.get('marketType')
            market_point = tip.get('marketPoint')
            point = tip.get('point')

            market = MARKETS[market]

            if market_type:
                market_type = MARKET_TYPE_NAMES[market_type]

            game_url: str = tip.get('gameUrl')
            
            browser = p.chromium.launch(headless=True)
            
            page = browser.new_page()
            
            page.goto(game_url, timeout=15000)
            
            title = page.title()
            

            page.wait_for_timeout(3000)
            
            print(title)
            
            # Localiza o botão para expandir todos mercados
            page.locator('div[class*="style_showAll__"]').click()
            for button in page.locator('button[class*="style_toggleMarkets__"]').all():
                button.click()

            if market in AVAILABLES_TO_MARKET_TYPES:
                #Clica em todos os buttons
                if market_point and market_type:
                    buttons = page.locator(f"button").filter(has_text=str(point)).filter(has_text=market_point).filter(has_text=market_type)
                elif market_point:
                    buttons = page.locator(f"button").filter(has_text=str(point)).filter(has_text=market_point)
                elif market_type:
                    buttons = page.locator(f"button").filter(has_text=str(point)).filter(has_text=market_type)
                else:
                    buttons = page.locator(f"button").filter(has_text=str(point))
            else:
                buttons = page.locator(f"button").filter(has_text=str(point))

            page.wait_for_timeout(1000)
            for button in buttons.all():
                button.click()

            page.wait_for_timeout(1000)

            cards_container = page.locator('#betslip-singles')

            cards = cards_container.locator('div>.betslip-card').filter(has_text=market)
            
            if not cards.count():
                return {
                    "error": True,
                    "detail": "Não foi encontrada nenhuma ODD"
                }
            elif cards.count() > 1:
                print("@@@@@@@@@@ cards:", cards.count())
                for card in cards.all():
                    print(card.text_content())


                return {
                    "error": True,
                    "detail": "O jogo retornou mais de uma ODD"
                }


            card = cards.first
            print("@@@@@@@@@@@@@ 1")

            print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ", card.locator('span[class^="style_priceLabelAlt__"]').text_content())

            inputs = card.locator(".betslipCardStakeWinInput")
            
            print("@@@@@@@@@@@@@ 2")
            input_stake = inputs.locator('input').first

            print("@@@@@@@@@@@@@ 3")
            input_win = inputs.locator('input').nth(1)

            print("@@@@@@@@@@@@@ 4")
            page.wait_for_timeout(1000)

            input_stake.fill(str(stake))

            print("@@@@@@@@@@@@@ 5")
            
            page.wait_for_timeout(1000)


            print("@@@@@@@@@@@@@ 6")
            payout_value = input_win.get_attribute('value')
            

            print("@@@@@@@@@@@@@ 7")
            browser.close()

            return {
                "error": False,
                "detail": "",
                "data": {
                    "payout_value": payout_value,
                }
            }, 200

        except Exception as e:
            return {
                "error": True,
                "detail": repr(e)
            }, 400
    
    return {
        "error": True,
        "detail": "Nada foi feito" 
    }, 400

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




