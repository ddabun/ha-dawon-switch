#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
 수정사항 :
 - 여러개 플러그가 작동되도록 수정
 - 매번 로그인에서 세션파일을 두어  세션이끊기지 전까지 작동되록 변경 
"""


import requests
import urllib
import sys
import json

TIMEOUT=5
API_URL='https://dwapi.dawonai.com:18443'
DIR_PATH='/config/python_script/'


SSO_TOKEN='unuseddata'
FCM_TOKEN='unuseddata'
TERMINAL_ID='unuseddata'
EMAIL='unuseddata'
NAME='unuseddata'


if sys.platform == 'win32':
    CONFIGFILE='./dawon_config.json'
    SESSIONFILE='./dawon_session.json'
else:
    CONFIGFILE= DIR_PATH + 'dawon_config.json'
    SESSIONFILE= DIR_PATH + 'dawon_session.json'


def _realTime_power(DEVICE_ID):
    from websocket import create_connection
    ws = create_connection("wss://dwws.dawonai.com:18444/mqreceiver/v1/devices/webSocket")
    ws.send("deviceInfo;" + DEVICE_ID)
    result =  ws.recv()
    print(result)
    ws.close()


def _json_save(data,savename):
    try:
        js_w = open(savename, 'w')
        js_w.write(data)
        js_w.close()
        print('file write:{}'.format(savename))
        return True
    except:
        return False
    
def _json_read(filename):
    try:
        with open(filename, 'r') as f:
            config = f.read()
            f.close()
            #print('파일:{} 읽음'.format(filename))
            return config
        return True
    except:
        print('{} File not found or failed to read file.'.format(filename))
        return 'no file'
        


class DAWON_API():
    def __init__(self):
        self.user_id=self._load_config()
        self._baseHeader={'X-Requested-With': 'XMLHttpRequest',\
                          'Content-Type':'application/x-www-form-urlencoded',\
                          'Cookie':'JSESSIONID=' + _json_read(SESSIONFILE)}

    def _request_api(self,url, header, payload):
        body=urllib.parse.urlencode(payload)
        r = requests.post(url, headers=header, data=body, timeout=TIMEOUT)
        return r
    
    
    def _load_config(self):
        try:
            with open(CONFIGFILE, 'r') as f:
                config = json.load(f)
                f.close()
                return config['user_id']
        except:
            print ('{} :: File not found or failed to read.'.format('dawon_config.json'))
    
    
    def _dawon_control(self):
        count=len(sys.argv)
        if count == 3:
            if sys.argv[2] == 'on' or  sys.argv[2] == 'off':
                self._call_api(sys.argv[1],sys.argv[2])
            elif sys.argv[2] == 'status':
                self._get_status(sys.argv[1])
            elif sys.argv[2] == 'realtime':
                _realTime_power(sys.argv[1])
            else:
                print ('Invalid command.')
        else:
            print ('Invalid argument.')    

    
    def _act_ret_print(self,r,action):
        if 'execute success' in r.text and action == 'on':
            print ('on success')
        if 'execute success' in r.text and action == 'off':
            print ('off success')
                
    
    def _call_api(self,DEVICE_ID,action):
        url=API_URL + '/iot/product/device_' + action + '.opi'
        payload={'devicesId':DEVICE_ID}
        r=self._request_api(url, self._baseHeader, payload)
        if r.status_code == 500:
            print ('[dawon_api.py]responese code[{}] \nCheck the value of device_id or user_id please.\nexit'.format(r.status_code))
            exit(0)
        if self._is_logIn(r):
            self._act_ret_print(r,action)
        else:
            self._refreshBaseHeader={'X-Requested-With': 'XMLHttpRequest',\
                          'Content-Type':'application/x-www-form-urlencoded',\
                          'Cookie':'JSESSIONID=' + self.cookie}
            r=self._request_api(url, self._refreshBaseHeader, payload)
            self._act_ret_print(r,action)
            
        
    def _get_cookie(self):
        url = API_URL + '/iot/'
        header={'Upgrade-Insecure-Requests':'1'}
        session = requests.Session()
        r = session.get(url, headers=header, timeout=TIMEOUT)
        return r.cookies.get_dict()
    
    def _logIn_Action(self):
        session=self._get_cookie()
        url=API_URL + '/iot/member/loginAction.opi'
        header={'X-Requested-With': 'XMLHttpRequest',\
                'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8',
                'Cookie': 'JSESSIONID=' + str(session['JSESSIONID'])}
        payload={'user_id':self.user_id + '/google','sso_token':SSO_TOKEN,'fcm_token':FCM_TOKEN,'terminal_id':TERMINAL_ID,\
                 'os_type':'Android','email':EMAIL,'name':NAME,'register':'google','terminal_name':'SAMSUNG'}
        r=self._request_api(url, header, payload)
        if r.text == 'Y':
            saveData=str(session['JSESSIONID'])
            _json_save(saveData,SESSIONFILE)
            print ('Your session has been refreshed.')
            return str(session['JSESSIONID'])
        else:
            print ('Login Fail')
            
    def _is_logIn(self,r):
        if 'intro.opi' in r.text:
            print ('Session has expired.')
            self.cookie=self._logIn_Action()  
            return False
        else:
            return True
       
            
    def _get_status(self,DEVICE_ID):
        url = API_URL + '/iot/product/device_profile_get.opi'
        payload={'devicesId': DEVICE_ID}
        r=self._request_api(url, self._baseHeader, payload)
        if r.status_code == 500:
            self._logIn_Action()
            print ('[dawon_api.py]responese code[{}] \nCheck the value of device_id or user_id pleas.\nexit'.format(r.status_code))
            exit(0)
        else:
            if self._is_logIn(r):
                ret=r.json()
                if 'devices' in ret and ret['devices'] == []:
                    print ('[dawon_api.py]Failed to get device info\nCheck the value of device_id or user_id please.')
                    exit(0)
                else:
                    print ('on' if ret['devices'][0]['device_profile']['power'] == 'true' else 'off')
        
        
if __name__ == "__main__":
    api=DAWON_API()
    api._dawon_control()
