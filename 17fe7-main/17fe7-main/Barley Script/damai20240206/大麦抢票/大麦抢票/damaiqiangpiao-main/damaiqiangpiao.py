import os  # 创建文件夹, 文件是否存在
import time  # time 计时
import pickle  # 保存和读取cookie实现免登陆的一个工具
from time import sleep
from selenium import webdriver  # 操作浏览器的工具
from selenium.webdriver.common.by import By

"""
一. 实现免登陆
二. 抢票并且下单
"""
# 大麦网主页
damai_url = 'https://www.damai.cn/'
# 登录
login_url = 'https://passport.damai.cn/login?ru=https%3A%2F%2Fwww.damai.cn%2F'
# 抢票目标页
target_url = 'https://detail.damai.cn/item.htm?spm=a2oeg.home.card_0.ditem_0.6ee823e1Gm7IzB&id=766022937790'

# class Concert:
class Concert:
    # 初始化加载
    def __init__(self):
        self.status = 0  # 状态, 表示当前操作执行到了哪个步骤
        self.login_method = 1  # {0:模拟登录, 1:cookie登录}自行选择登录的方式
        self.driver = webdriver.Chrome(executable_path='chromedriver.exe')  # 当前浏览器驱动对象

    # cookies: 登录网站时出现的 记录用户信息用的
    def set_cookies(self):
        """cookies: 登录网站时出现的 记录用户信息用的"""
        self.driver.get(damai_url)
        print('###请点击登录###')
        # 我没有点击登录,就会一直延时在首页, 不会进行跳转
        while self.driver.title.find('大麦网-全球演出赛事官方购票平台') != -1:
            sleep(1)
        print('###请扫码登录###')
        # 没有登录成功
        while self.driver.title != '大麦网-全球演出赛事官方购票平台-100%正品、先付先抢、在线选座！':
            sleep(1)
        print('###扫码成功###')
        # get_cookies: driver里面的方法
        pickle.dump(self.driver.get_cookies(), open('cookies.pkl', 'wb'))
        print('###cookie保存成功###')
        self.driver.get(target_url)

    # 假如说我现在本地有 cookies.pkl 那么 直接获取
    def get_cookie(self):
        """假如说我现在本地有 cookies.pkl 那么 直接获取"""
        cookies = pickle.load(open('cookies.pkl', 'rb'))
        for cookie in cookies:
            cookie_dict = {
                'domain': '.damai.cn',  # 必须要有的, 否则就是假登录
                'name': cookie.get('name'),
                'value': cookie.get('value')
            }
            self.driver.add_cookie(cookie_dict)
        print('###载入cookie###')

    def login(self):
        """登录"""
        if self.login_method == 0:
            self.driver.get(login_url)
            print('###开始登录###')
        elif self.login_method == 1:
            # 创建文件夹, 文件是否存在
            if not os.path.exists('cookies.pkl'):
                self.set_cookies()  # 没有文件的情况下, 登录一下
            else:
                self.driver.get(target_url)  # 跳转到抢票页
                self.get_cookie()  # 并且登录

    def enter_concert(self):
        """打开浏览器"""
        print('###打开浏览器,进入大麦网###')
        # 调用登录
        self.login()  # 先登录再说
        self.driver.refresh()  # 刷新页面
        self.status = 2  # 登录成功标识
        print('###登录成功###')
        # 处理弹窗
        if self.isElementExist('/html/body/div[2]/div[2]/div/div/div[3]/div[2]'):
            self.driver.find_element(By.XPATH, '/html/body/div[2]/div[2]/div/div/div[3]/div[2]').click()

    # 二. 抢票并且下单
    def choose_ticket(self):
        """选票操作"""
        if self.status == 2:
            print('=' * 30)
            print('###开始进行日期及票价选择###')
            while self.driver.title.find("确认订单") == -1:
                try:
                    # buybutton = self.driver.find_element(By.CLASS_NAME, 'buybtn').text
                    buybutton = self.driver.find_element(By.CLASS_NAME, 'buy-link').text

                    if buybutton == '提交缺货登记':
                        self.status = 2  # 没有进行更改操作
                        self.driver.get(target_url)  # 刷新页面 继续执行操作
                    elif buybutton == '立即预定':
                        # 点击立即预定
                        self.driver.find_element('buybtn').click()
                        self.status = 3
                    elif buybutton == '不，立即预订':
                        # 点击立即预定
                        self.driver.find_element('buybtn').click()
                        self.status = 3
                    elif buybutton == '立即购买':
                        self.driver.find_element(By.CLASS_NAME, 'buybtn').click()
                        self.status = 4
                    elif buybutton == '选座购买':
                        self.driver.find_element(By.CLASS_NAME, 'buybtn').click()
                        self.status = 5
                except:
                    print('###没有跳转到订单结算界面###')
                    print(buybutton)
                    self.driver.quit()

                title = self.driver.title
                if title == '选座购买':
                    # 选座购买的逻辑
                    self.choice_seats()
                elif title == '确认订单':
                    # 实现下单的逻辑
                    while True:
                        # 如果标题为确认订单
                        print('正在加载.......')
                        # 如果当前购票人信息存在 就点击
                        if self.isElementExist('//*[@id="container"]/div/div[9]/button'):
                            # 下单操作
                            self.check_order()
                            break

    def choice_seats(self):
        """选择座位"""
        while self.driver.title == '选座购买':
            while self.isElementExist('//*[@id="app"]/div[2]/div[2]/div[1]/div[2]/img'):
                print('请快速选择你想要的座位!!!')
            while self.isElementExist('//*[@id="app"]/div[2]/div[2]/div[2]/div'):
                self.driver.find_element(By.XPATH, '//*[@id="app"]/div[2]/div[2]/div[2]/button').click()

    def check_order(self):
        """下单操作"""
        if self.status in [3, 4, 5]:
            print('###开始确认订单###')
            time.sleep(1)
            try:
                # 默认选第一个购票人信息
                self.driver.find_element(By.XPATH, '//*[@id="container"]/div/div[2]/div[2]/div[1]/div/label').click()
            except Exception as e:
                print('###购票人信息选中失败, 自行查看元素位置###')
                print(e)
            # 最后一步提交订单
            time.sleep(0.5)  # 太快了不好, 影响加载 导致按钮点击无效
            self.driver.find_element(By.XPATH, '//*[@id="container"]/div/div[9]/button').click()
            time.sleep(20)

    def isElementExist(self, element):
        """判断元素是否存在"""
        flag = True
        browser = self.driver
        try:
            browser.find_element(By.XPATH, element)
            return flag
        except:
            flag = False
            return flag

    def finish(self):
        """抢票完成, 退出"""
        self.driver.quit()


if __name__ == '__main__':
    con = Concert()
    try:
        con.enter_concert()  # 打开浏览器
        con.choose_ticket()  # 选择座位
    except Exception as e:
        print(e)
        con.finish()

