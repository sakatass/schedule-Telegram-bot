#!/usr/bin/env python
# coding: utf-8

# # CREATE TELEGRAM BOT

# In[1]:


import telebot
from telebot import types
import requests
import numpy as np
from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from datetime import datetime
from PIL import Image
from selenium.webdriver.common.keys import Keys
from io import BytesIO
import math
import time
import os
from bs4 import BeautifulSoup
import wget

BOT_TOKEN = '**************************************'
START_MESSAGE = 'Привет, это бот ПДАБА. \nЗдесь ты можешь получить расписание на неделю, информацию о преподавателе по фамилии, а также оставить отзыв о любом преподавателе. \nВведи /help для просмотра списка команд.'
HELP_MESSAGE = '''Список команд:
/help - список команд
/schedule название группы - расписание на неделю
Например: /schedule КН-21
'''
NAME_GROUP_ERROR_MESSAGE = 'Неверно введено название группы.'
UPDATE_SCHEDULE_MESSAGE = 'Началось обновление, подождите пару минут.'
UPDATE_TEACHERS_MESSAGE = 'Началось обновление, подождите пару минут.'
CHROMEDRIVER_EXECUTABLE_PATH = r'chromedriver.exe'
SCHEDULE_LINK = {'Будівельний':'https://www.pgasa.dp.ua/timetable/WSIGMA/CTP/K{YEAR}/ROZKLAD.HTML',
            'Архітектурний':'https://www.pgasa.dp.ua/timetable/WSIGMA/APX/K{YEAR}/ROZKLAD.HTML',
            'ЦІ_та_Е':'https://www.pgasa.dp.ua/timetable/WSIGMA/CT/K{YEAR}/ROZKLAD.HTML',
            'ІТ_та_МІ':'https://www.pgasa.dp.ua/timetable/WSIGMA/MEX/K{YEAR}/ROZKLAD.HTML',
            'Економічний':'https://www.pgasa.dp.ua/timetable/WSIGMA/EK/K{YEAR}/ROZKLAD.HTML'}
SCHEDULE_DIR = 'C:\\Users\\Zavod\\Desktop\\вуз\\telegram_bot\\schedule\\'
TEACHERS_LINK = 'https://pgasa.dp.ua/academy/struktura/department/'
TEACHERS_DIR_PHOTO = 'C:\\Users\\Zavod\\Desktop\\вуз\\telegram_bot\\teachers\\teachers photo\\'
TEACHERS_DIR_DATA = 'C:\\Users\\Zavod\\Desktop\\вуз\\telegram_bot\\teachers\\teachers_data.txt'
COMMENTS_ANON_DIR = 'C:\\Users\\Zavod\\Desktop\\вуз\\telegram_bot\\teachers\\anon_comm.txt'
COMMENTS_PUB_DIR = 'C:\\Users\\Zavod\\Desktop\\вуз\\telegram_bot\\teachers\\pub_comm.txt'
LAST_UPDATE_SCHEDULE = None

comment_teacher_name = None
comment_type = None


# ## functions

# In[2]:


def get_start_end_2(selenium_screenshot):
    full_image = Image.open(BytesIO(selenium_screenshot))
    full_image = full_image.convert('RGB')
    image_1_pixel = full_image.crop((21, 0, 22, full_image.size[1]))
    start_end_array = []
    blue_pixel = []
    for y in range(0, image_1_pixel.size[1]):
        if image_1_pixel.getpixel((0, y)) == (79, 129, 189):
            blue_pixel.append(y)
    for index, y in enumerate(blue_pixel[1:]):
        if blue_pixel[index] - blue_pixel[index-1] > 1:
            start_end_array.append((blue_pixel[index-1], blue_pixel[index]))
    return start_end_array

def get_shedule(SCHEDULE_LINK, SCHEDULE_DIR, CHROMEDRIVER_EXECUTABLE_PATH):
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1000,20000")
    options.add_argument("--start-maximized")
    options.add_argument("--headless")
    
    driver = webdriver.Chrome(
        executable_path=CHROMEDRIVER_EXECUTABLE_PATH,
        options=options
        )
    driver.implicitly_wait(2)
    for group in SCHEDULE_LINK:
        for YEAR in range(1, 7):
            driver.get(SCHEDULE_LINK[group].format(YEAR=YEAR))
            faculty_names = driver.find_elements(By.XPATH, '//font[@color="#000000"]')
            screenshot = driver.get_screenshot_as_png()
            start_end_array = get_start_end_2(screenshot)
            for nomer, faculty_name in enumerate(faculty_names):
                im = Image.open(BytesIO(screenshot))
                one_gr_image = im.crop((9, start_end_array[nomer][0], 972, start_end_array[nomer][1]+1))
                one_gr_image.save(f'{SCHEDULE_DIR}{faculty_name.text}.png', quality=95)   

def download_photo_data(list_links, TEACHERS_DIR_PHOTO, TEACHERS_DIR_DATA):
    for url in list_links:
        r = requests.get(url)
        soup = BeautifulSoup(r.text, 'html.parser')
        full_name = str(soup.find_all('div', class_='item-name')[0].findChildren('p')[1]).replace('<p>', '').replace('</p>', '').replace('<br/>', ' ').replace('\r', '').replace('\n', '')
        contacts = soup.find_all('div', class_='contact-info')[0].findChildren('p')
        location = contacts[1].text.replace('\r', '').replace('\n', '')
        phone = contacts[3].text.replace('\r', '').replace('\n', '')
        email = contacts[5].text.replace('\r', '').replace('\n', '').replace('.ua', '.ua ').replace('.com', '.com ').replace(' @', '@')
        if location == '': location = 'Інформація відсутня.'
        if phone == '': phone = 'Інформація відсутня.'
        if email == '': email = 'Інформація відсутня.'
        if f'{TEACHERS_DIR_PHOTO}{full_name}.png' not in os.listdir(TEACHERS_DIR_PHOTO):
            wget.download(soup.find_all('img', alt='foto_teacher')[0]['src'], out=f'{TEACHERS_DIR_PHOTO}{full_name}.png')
            with open(TEACHERS_DIR_DATA, 'a+') as file:                    
                file.write(f"{full_name}_{location}_{phone}_{email}".rstrip('\n')+'\n')  
                
def update_teachers_data(TEACHERS_DIR_PHOTO, TEACHERS_DIR_DATA, TEACHERS_LINK):
    [f.unlink() for f in Path(TEACHERS_DIR_PHOTO).glob("*") if f.is_file()]
    with open(TEACHERS_DIR_DATA, 'w') as file:
        pass
    r = requests.get(TEACHERS_LINK)
    soup = BeautifulSoup(r.text, 'html.parser')
    main_links = [link['href'].replace(' ', '') if 'https' in link['href'] else 'https://pgasa.dp.ua'+link['href'].replace(' ', '') for link in soup.find_all('a', class_='faculty-item')]
    second_links = [link['href'].replace(' ', '') if 'https' in link['href'] else 'https://pgasa.dp.ua'+link['href'].replace(' ', '') for link in soup.find_all('a', class_='testtest')]
    teacher_links = []
    for link in main_links:
        r = requests.get(link)
        soup = BeautifulSoup(r.text, 'html.parser')
        teachers = soup.find_all('div', class_='dep-office-item')
        for teacher in teachers:
            teacher_links.append('https://pgasa.dp.ua'+teacher.findChildren('a')[0]['href'])
    for link in second_links[0:-1]:
        r = requests.get(link, timeout=(3.05, 3))
        soup = BeautifulSoup(r.text, 'html.parser')
        teachers = soup.find_all('div', class_='department-row-item')
        for teacher in teachers:
            teacher_links.append(teacher.findChildren('a')[0]['href'])
    download_photo_data(teacher_links, TEACHERS_DIR_PHOTO, TEACHERS_DIR_DATA)


# In[3]:


bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(content_types=['text'])
def get_message(message):
    global LAST_UPDATE_SCHEDULE
    global comment_teacher_name
    global comment_type
    if message.text == '/start':
        bot.send_message(message.chat.id, START_MESSAGE)
    elif message.text == '/help':
        bot.send_message(message.chat.id, HELP_MESSAGE)
    elif '/schedule' in message.text:
        if datetime.now().timetuple().tm_yday != LAST_UPDATE_SCHEDULE:
            bot.send_message(message.chat.id, UPDATE_SCHEDULE_MESSAGE)
            get_shedule(SCHEDULE_LINK, SCHEDULE_DIR, CHROMEDRIVER_EXECUTABLE_PATH)
            LAST_UPDATE_SCHEDULE = datetime.now().timetuple().tm_yday
            if datetime.now().timetuple().tm_yday in np.arange(243, 273):
                bot.send_message(message.chat.id, UPDATE_TEACHERS_MESSAGE)
                update_teachers_data(TEACHERS_DIR_PHOTO, TEACHERS_DIR_DATA, TEACHERS_LINK)
        if message.text.split(' ')[-1].upper()+'.png' in os.listdir(SCHEDULE_DIR):
            bot.send_document(message.chat.id, open('{SCHEDULE_DIR}{GROUP_NAME}.png'.format(SCHEDULE_DIR=SCHEDULE_DIR, GROUP_NAME=message.text.split(' ')[-1]), 'rb'))
        else:
            bot.send_message(message.chat.id, NAME_GROUP_ERROR_MESSAGE)
    if '/teachers' in message.text:
        #keyboard = types.InlineKeyboardMarkup()
        borders = [(50*bord, 50*(bord+1)) for bord in range(math.ceil(len(os.listdir(TEACHERS_DIR_PHOTO))/50))]
        keyboards = [types.InlineKeyboardMarkup() for bord in borders]
        short_teachers = {f'{teacher.split(" ")[0]} {teacher.split(" ")[1][0]}. {teacher.split(" ")[2][0]}.': teacher for teacher in os.listdir(TEACHERS_DIR_PHOTO)}
        for count, bord in enumerate(borders):  
            for teacher in list(short_teachers.keys())[bord[0]:bord[1]]:
                keyboards[count].add(types.InlineKeyboardButton(text=teacher.replace('.png', ''), callback_data=teacher))
            bot.send_message(message.chat.id, text=f'{count+1} страница:', reply_markup=keyboards[count])
    if '/comment' in message.text:
        if comment_teacher_name is not None and comment_type is not None and message.text not in ['/comment', '/comment ']:
            comment_text = ' '.join(message.text.replace('\n', ' ').replace('\r', ' ').split(' ')[1::])
            if comment_type == 'anon':
                with open(COMMENTS_ANON_DIR, 'a+') as file:
                    file.write('{t_name}__{comm}\n'.format(t_name=comment_teacher_name, comm=comment_text))
                bot.send_message(message.chat.id, text='Комментарий сохранен.')
                comment_teacher_name, comment_type = None, None
            elif comment_type == 'pub':
                with open(COMMENTS_PUB_DIR, 'a+') as file:
                    file.write('{t_name}__{chat_id}__{comm}\n'.format(t_name=comment_teacher_name, chat_id=message.chat.id, comm=comment_text))
                bot.send_message(message.chat.id, text='Комментарий сохранен.')
                comment_teacher_name, comment_type = None, None
        else:
            bot.send_message(message.chat.id, text='Не выбран или преподаватель или тип коментария или комментарий отсутствует.')

@bot.callback_query_handler(func = lambda call: True)
def answer(call):
    global comment_teacher_name
    global comment_type
    if '2yes' in call.data:
        comment_type = 'anon'
        bot.send_message(call.message.chat.id, text='Отправить комментарий: /comment <комментарий>')
    elif '2no' in call.data:
        comment_type = 'pub'
        bot.send_message(call.message.chat.id, text='Отправить комментарий: /comment <комментарий>')
    elif '1yes' in call.data:
        comment_teacher_name = ' '.join(call.data.split(' ')[1::])
        keyboard = types.InlineKeyboardMarkup()
        btn_yes = types.InlineKeyboardButton(text='Да', callback_data='2yes')
        btn_no = types.InlineKeyboardButton(text='Нет', callback_data='2no')
        keyboard.row(btn_yes, btn_no)
        bot.send_message(call.message.chat.id, text='Анонимно?', reply_markup=keyboard)
    elif '1no' in call.data: bot.send_message(call.message.chat.id, text='Вы всегда можете вернуться к этому выбору.')
    else:
        short_teachers = {f'{teacher.split(" ")[0]} {teacher.split(" ")[1][0]}. {teacher.split(" ")[2][0]}.': teacher for teacher in os.listdir(TEACHERS_DIR_PHOTO)}
        with open(TEACHERS_DIR_DATA, 'r') as file:
            for teacher_info in file:
                if teacher_info.split('_')[0] == short_teachers[call.data].replace('.png', ''):
                    break
        msg = f"""ПІБ: {teacher_info.split('_')[0]}
Кабінет: {teacher_info.split('_')[1]}
Телефонні номера: {teacher_info.split('_')[2]}
Пошта: {teacher_info.split('_')[3]}

Хотите оставить комментарий о преподавателе?"""
        bot.send_document(call.message.chat.id, open('{directory}{full_name}.png'.format(directory=TEACHERS_DIR_PHOTO, full_name=teacher_info.split('_')[0]), 'rb'))
        keyboard = types.InlineKeyboardMarkup()
        btn_yes = types.InlineKeyboardButton(text='Да', callback_data='1yes, {name}'.format(name=teacher_info.split('_')[0]))
        btn_no = types.InlineKeyboardButton(text='Нет', callback_data='1no, {name}'.format(name=teacher_info.split('_')[0]))
        keyboard.row(btn_yes, btn_no)
        bot.send_message(call.message.chat.id, text=msg, reply_markup=keyboard)

bot.polling(none_stop=True, interval=0)



