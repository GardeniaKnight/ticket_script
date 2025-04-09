  # coding: utf-8
from json import loads
from os.path import exists
from pickle import dump, load
from time import sleep, time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import os
import argparse
import json
import platform
import requests
from requests import session


class Concert(object):
    def __init__(self, real_name, nick_name, ticket_num, show_id, sku_id):
        self.login_cookies = {}
        self.real_name = real_name
        self.nick_name = nick_name
        self.show_id = show_id
        self.sku_id = sku_id
        self.ticket_num = ticket_num
        self.total_wait_time = 3  # 页面元素加载总等待时间
        self.refresh_wait_time = 0.3  # 页面元素等待刷新时间
        self.intersect_wait_time = 0.6  # 间隔等待时间，防止速度过快导致问题
        self.mobile_url = "https://m.damai.cn"
        self.target_url = "https://m.damai.cn/app/dmfe/h5-ultron-buy/index.html?buyParam={0}_{1}_{2}&buyNow=true&exParams=%257B%2522channel%2522%253A%2522damai_app%2522%252C%2522damai%2522%253A%25221%2522%252C%2522umpChannel%2522%253A%2522100031004%2522%252C%2522subChannel%2522%253A%2522damai%2540damaih5_h5%2522%252C%2522atomSplit%2522%253A1%257D&spm=a2o71.project.sku.dbuy&sqm=dianying.h5.unknown.value".format(
            self.show_id, self.ticket_num, self.sku_id)

    def get_cookie(self):
        self.driver.get(self.mobile_url)
        # 扫码或点击登录
        Log_state = False
        while Log_state == False:
            try:
                name = self.driver.find_element(
                    By.XPATH, "/html/body/div[1]/div[1]/div[2]/div[1]").text
                if name == self.nick_name:
                    Log_state = True
                    break
            except:
                sleep(1)

        dump(self.driver.get_cookies(), open("cookies.pkl", "wb"))
        print("###Cookie保存成功###")

    def set_cookie(self):
        try:
            cookies = load(open("cookies.pkl", "rb"))  # 载入cookie
            for cookie in cookies:
                cookie_dict = {
                    'domain': '.damai.cn',  # 必须有，不然就是假登录
                    'name': cookie.get('name'),
                    'value': cookie.get('value'),
                    "expires": "",
                    'path': '/',
                    'httpOnly': False,
                    'HostOnly': False,
                    'Secure': False
                }
                self.driver.add_cookie(cookie_dict)
            #print('###载入Cookie###')
        except Exception as e:
            print(e)

    def set_driver(self):
        options = webdriver.ChromeOptions()
        prefs = {"profile.managed_default_content_settings.images": 2}
        options.add_experimental_option("prefs", prefs)
        options.add_experimental_option(
            'mobileEmulation', {'deviceName': 'Samsung Galaxy S20 Ultra'})
        options.add_experimental_option(
            'mobileEmulation', {
                'deviceMetrics': {
                    'width':
                    412,
                    'height':
                    915,
                    'piexelRatio':
                    3.0,
                    'userAgent':
                    'Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.162 Mobile Safari/537.36'
                }
            })
        options.add_experimental_option("excludeSwitches",
                                        ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument", {
                "source":
                """
            Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
            })
        """
            })

    def login(self):
        if not exists('cookies.pkl'):  # 如果不存在cookie, 获取一下
            # Chrome Driver配置，伪装成Samsung Galaxy S20 Ultra
            self.set_driver()
            self.get_cookie()
            self.driver.quit()
        # 需要重新set, 不然积极拒绝连接
        self.set_driver()
        self.driver.get(self.mobile_url)
        self.set_cookie()
        self.driver.refresh()

    def buy(self):
        flag = 0
        while flag != 1:
            self.driver.get(self.target_url)
            findflag = 0
            while findflag == 0:
                try:
                    txt = self.driver.find_element(
                        By.XPATH, "//*[@id=\"app\"]/div/div[1]").text
                    if txt == "您选购的商品信息已过期，请重新查询":
                        findflag = 0
                        self.driver.refresh()
                    else:
                        break
                except Exception as e:
                    findflag = 1
            if flag == 1:
                break
            button_xpath = "//*[@id=\"dmViewerBlock_DmViewerBlock\"]/div[2]/div/div[%d]/div[3]/i"
            for i in range(len(self.real_name)):  # 选择第i个实名者
                WebDriverWait(self.driver, self.total_wait_time, 0.5).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, button_xpath % (i + 1)))).click()
            buybutton = "//*[@id=\"dmOrderSubmitBlock_DmOrderSubmitBlock\"]/div[2]/div/div[2]/div[3]/div[2]/span"
            WebDriverWait(self.driver, self.total_wait_time, 0.1).until(
                EC.presence_of_element_located(
                    (By.XPATH, buybutton))).click()  # 同意以上协议并提交订单
            try:
                sleep(2)
                WebDriverWait(self.driver, 3,
                              3).until(EC.title_contains('支付宝'))
                self.status = 6
                flag = 1
            except Exception as e:
                flag = 0


if __name__ == '__main__':
    try:
        with open('./config.json', 'r', encoding='utf-8') as f:
            config = loads(f.read())
            con = Concert(config['real_name'], config['nick_name'],
                          config['ticket_num'], config['show_id'],
                          config['sku_id'])
    except Exception as e:
        print(e)
        raise Exception("错误：请设置config.json文件")
    con.login()  # 加载Cookie
    while True:  # 循环抢票
        try:
            con.buy()
        except Exception as e:
            con.driver.refresh()
