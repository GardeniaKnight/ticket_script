from selenium import webdriver

driver = webdriver.Chrome()
url = 'https://www.damai.cn/'
driver.get(url)
driver.maximize_window()
