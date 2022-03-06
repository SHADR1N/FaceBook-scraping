from time import time, sleep
import random
import os
import os.path


import pickle
import json
import asyncio
from pyppeteer import launch
from pyppeteer_stealth import stealth
from bs4 import BeautifulSoup
import sys
from datetime import datetime
from pytz import timezone
import traceback

import psycopg2
from psycopg2 import Error
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from time import time
import subprocess, sys


try:
    connection = psycopg2.connect(user="",
                                  password="",
                                  host="",
                                  port="5432",
                                  database="postgres")

    connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)


except (Exception, Error) as error:
    pass



async def br(proxy, login):
    if proxy != '':
        login = proxy.split('@')[0].split(':')[0]
        password = proxy.split('@')[0].split(':')[1]
        ip = proxy.split('@')[1].split(':')[0]
        port = proxy.split('@')[1].split(':')[1]

        browser = await launch({
            'defaultViewport': {'width': 1920, 'height': 1080},
            'args': [
            '--disable-setuid-sandbox',
            "--fast-start", 
            '--start-maximized',
            '--disable-infobars',
            f'--proxy-server={ip}:{port}', 
            ],
            'headless': False,
            'ignoreDefaultArgs': ["--enable-automation"],
            "ignoreHTTPSErrors": True
            })
        page = await browser.pages()
        page = page[0]

        await page.evaluateOnNewDocument('navigator.mediaDevices.getUserMedia = navigator.webkitGetUserMedia = navigator.mozGetUserMedia = navigator.getUserMedia = webkitRTCPeerConnection = RTCPeerConnection = MediaStreamTrack = undefined')
        await page.authenticate({'username': login, 'password': password})

        if os.path.exists(path = f'{login}/{login}.json'):
            with open(f'{login}/{login}.json') as f:
                cookies = json.load(f)
            
            for cookies in cookies:
                await page.setCookie(cookies)

        return page, browser
    else:
        browser = await launch({
            'defaultViewport': {'width': 1920, 'height': 1080},
            'args': [
            '--disable-setuid-sandbox',
            "--fast-start", 
            '--start-maximized',
            '--disable-infobars',
            ],
            'headless': False,
            'ignoreDefaultArgs': ["--enable-automation"],
            "ignoreHTTPSErrors": True
            })
        page = await browser.pages()
        page = page[0]

        await page.evaluateOnNewDocument('navigator.mediaDevices.getUserMedia = navigator.webkitGetUserMedia = navigator.mozGetUserMedia = navigator.getUserMedia = webkitRTCPeerConnection = RTCPeerConnection = MediaStreamTrack = undefined')
        
        if os.path.exists(path = f'{login}/{login}.json'):
            with open(f'{login}/{login}.json') as f:
                cookies = json.load(f)
            
            for cookies in cookies:
                await page.setCookie(cookies)

        return page, browser




async def main(ID, proxy, login, password):
    page, browser = await br(proxy, login)
    await page.goto('https://www.facebook.com/')
    await asyncio.sleep(10)

    try:
        await page.click('button[class="_42ft _4jy0 _9o-t _4jy3 _4jy1 selected _51sy"]')
    except:
        pass

    html_code = await page.evaluate('() => document.documentElement.outerHTML')      
    soup = BeautifulSoup(html_code, 'html.parser')
    try:
        for i in [1,2]:
            if 0 == len(soup.select('span[class="a8c37x1j ni8dbmo4 stjgntxs l9j0dhe7 ltmttdrg g0qnabr5"]')):
                try:
                    await page.type('#email', login)
                    await page.type('#pass', password)
                    await page.waitFor(500)
                    
                    await page.click('button[class="_42ft _4jy0 _6lth _4jy6 _4jy1 selected _51sy"]')
                    await page.waitFor(5000)

                    html_code = await page.evaluate('() => document.documentElement.outerHTML')      
                    soup = BeautifulSoup(html_code, 'html.parser')
                    if soup.select('input[name="email"]'):
                        await browser.close()
                        cursor = connection.cursor()
                        cursor.execute('''UPDATE users SET status = 'WrongAuthrization' WHERE id = %s''', [ID])
                        cursor.close()
                        return print('Wrong authrization.')
                except:
                    pass

                if await page.JJ('input[id="approvals_code"]'):
                    print('2fa')
                    cursor = connection.cursor()
                    cursor.execute('''UPDATE users SET status = '2fa' WHERE id = %s''', [ID])
                    cursor.close()

                    _start = time()
                    while True:
                        if time() - _start > 180:
                            print('time')
                            cursor = connection.cursor()
                            cursor.execute('''UPDATE users SET status = 'WrongLogin' WHERE id = %s''', [ID])
                            cursor.close()
                            await browser.close()
                            return print('Wrong login...')

                        cursor = connection.cursor()
                        view = '''select complete from users where id = %s'''
                        cursor.execute(view, ([ID]))
                        code = cursor.fetchone()
                        code = code[0]

                        if code:
                            if await page.JJ('a[class="autofocus _9l2h  layerCancel _4jy0 _4jy3 _4jy1 _51sy selected _42ft"]'):
                                await page.click('a[class="autofocus _9l2h  layerCancel _4jy0 _4jy3 _4jy1 _51sy selected _42ft"]')
                                await page.waitFor(1500)

                            await page.type('input[id="approvals_code"]', code)
                            await page.waitFor(2000)
                            x = 1
                            while x == 1:
                                if await page.JJ('button[id="checkpointSubmitButton"]'):
                                    await page.click('button[id="checkpointSubmitButton"]')
                                    await page.waitFor(5000)

                                else:
                                    x += 1

                            cursor = connection.cursor()
                            cursor.execute('''UPDATE users SET complete = %s WHERE id = %s''', [None, ID])
                            cursor.close()
                            await page.goto('https://www.facebook.com/')
                            await page.waitFor(2000)
                            break
                        await asyncio.sleep(5)

                elif await page.JJ('span[class="a8c37x1j ni8dbmo4 stjgntxs l9j0dhe7 ltmttdrg g0qnabr5"]'):
                    await page.waitFor(3000)
                    await page.click('#checkpointSubmitButton')
                    await page.waitFor(3000)

                    await page.click('div[class="uiInputLabel clearfix"]')
                    await page.waitFor(1000)

                    await page.click('#checkpointSubmitButton')
                    await page.waitFor(120000)

                    await page.click('#checkpointSubmitButton')
                    await page.waitFor(3000)

            await page.goto('https://www.facebook.com/')
            await page.waitFor(2000)

            html_code = await page.evaluate('() => document.documentElement.outerHTML')      
            soup = BeautifulSoup(html_code, 'html.parser')
            if 0 == len(soup.select('span[class="a8c37x1j ni8dbmo4 stjgntxs l9j0dhe7 ltmttdrg g0qnabr5"]')):
                pass

            else:
                break
        else:   
            cursor = connection.cursor()
            cursor.execute('''UPDATE users SET status = 'WrongLogin' WHERE id = %s''', [ID])
            cursor.close()
            await browser.close()
            return print('Wrong login...')
    except Exception as err:
        print(err)
        cursor = connection.cursor()
        cursor.execute('''UPDATE users SET status = 'WrongLogin' WHERE id = %s''', [ID])
        cursor.close()
        await browser.close()
        return print('Wrong login...')

    if not os.path.exists(path = f'{login}'):
        os.mkdir(path = f'{login}')
        os.mkdir(path = f'{login}/friends')


    cookies = await page.cookies()
    with open(f'{login}/{login}.json', 'w') as f:
        f.write(json.dumps(cookies, sort_keys=True, indent=4))
        f.truncate()



    # Name and photo
    await page.click('a[class="oajrlxb2 g5ia77u1 qu0x051f esr5mh6w e9989ue4 r7d6kgcz rq0escxv nhd2j8a9 j83agx80 p7hjln8o kvgmc6g5 cxmmr5t8 oygrvhab hcukyx3x jb3vyjys d1544ag0 qt6c0cv9 tw6a2znq i1ao9s8h esuyzwwr f1sip0of lzcic4wl l9j0dhe7 abiwlrkh p8dawk7l bp9cbjyn e72ty7fz qlfml3jp inkptoze qmr60zad btwxx1t3 tv7at329 taijpn5t k4urcfbm"]')
    await page.waitFor(7000)
    html_code = await page.evaluate('() => document.documentElement.outerHTML')      
    soup = BeautifulSoup(html_code, 'html.parser')

    img = soup.select('image[preserveAspectRatio="xMidYMid slice"]')[0]['xlink:href']
    name_acc = soup.select('div[class="bi6gxh9e aov4n071"]')[0].text.strip()

    await page.goto('https://www.facebook.com/friends/list')
    await page.waitFor(3000)

    html_code = await page.evaluate('() => document.documentElement.outerHTML')      
    soup = BeautifulSoup(html_code, 'html.parser')
    if len(soup.select('span[class="a8c37x1j ni8dbmo4 stjgntxs l9j0dhe7 ojkyduve"]')) == 0:
        await browser.close()
        return print('Total friends zero.')

    try:
        total_friends = soup.select('span[class="a8c37x1j ni8dbmo4 stjgntxs l9j0dhe7 ojkyduve"]')[-1].text.split(':')[1].replace(' ', '').strip()
        total_friends = int(int(total_friends)*0.95)
    except:
        # Update data
        cursor = connection.cursor()
        cursor.execute('''UPDATE users SET status = 'complete', firstName = %s, lastName = %s, avatartUrl = %s, friendsCount = %s, updateAt = %s WHERE id = %s''', [name_acc.split()[0], name_acc.split()[1], img, 0, time(), ID])
        cursor.close()
        await browser.close()
        return print('Total friends zero.')

    # Update data
    cursor = connection.cursor()
    cursor.execute('''UPDATE users SET status = 'friendsParsing', firstName = %s, lastName = %s, avatartUrl = %s, friendsCount = %s WHERE id = %s''', [name_acc.split()[0], name_acc.split()[1], img, total_friends, ID])
    cursor.close()


    friends_urls = []
    start = time()
    enum = 0
    while True:
        datalist = await page.JJ('div[data-visualcompletion="ignore-dynamic"]')     

        if enum == 0:
            pag = 0
        else:
            pag = enum - 10

        for friend in datalist[pag:]:
            enum += 1
            try:
                u = await friend.querySelector('a')
                url = await page.evaluate('(a) => a.getAttribute("href")', u)
                await page.evaluate('(friend) => friend.scrollIntoView()', friend)  
            except:
                continue

            if url in friends_urls:
                continue

            await page.waitFor(1000)
            friend = BeautifulSoup(await page.evaluate('(friend) => friend.outerHTML', friend), 'html.parser')           
            try:
                if friend.select('div[class="oajrlxb2 g5ia77u1 qu0x051f esr5mh6w e9989ue4 r7d6kgcz rq0escxv nhd2j8a9 nc684nl6 p7hjln8o kvgmc6g5 cxmmr5t8 oygrvhab hcukyx3x jb3vyjys rz4wbd8a qt6c0cv9 a8nywdso i1ao9s8h esuyzwwr f1sip0of lzcic4wl l9j0dhe7 abiwlrkh p8dawk7l ni8dbmo4 stjgntxs ltmttdrg"]'):
                    role = friend.select('div[class="oajrlxb2 g5ia77u1 qu0x051f esr5mh6w e9989ue4 r7d6kgcz rq0escxv nhd2j8a9 nc684nl6 p7hjln8o kvgmc6g5 cxmmr5t8 oygrvhab hcukyx3x jb3vyjys rz4wbd8a qt6c0cv9 a8nywdso i1ao9s8h esuyzwwr f1sip0of lzcic4wl l9j0dhe7 abiwlrkh p8dawk7l ni8dbmo4 stjgntxs ltmttdrg"]')[0]
                    mutual_frineds = role.select('span[class="d2edcug0 hpfvmrgz qv66sw1b c1et5uql lr9zc1uh e9vueds3 j5wam9gi knj5qynh m9osqain"]')
                    if mutual_frineds:
                        mutual_frineds = mutual_frineds[0].text
                        mutual_frineds = mutual_frineds.split('общ')[0].strip()
                    else:
                        mutual_frineds = 0
                else:
                    mutual_frineds = 0

                fio = friend.select('span[class="d2edcug0 hpfvmrgz qv66sw1b c1et5uql lr9zc1uh jq4qci2q a3bd9o3v lrazzd5p oo9gr5id"]')[0].text
                if [url, fio, mutual_frineds] not in friends_urls and 'facebook.com' in url:
                    friends_urls.append([url, fio, mutual_frineds])
                    
                    cursor = connection.cursor()
                    cursor.execute('''UPDATE users SET complete = %s WHERE id = %s''', [len(friends_urls), ID])
                    cursor.close()

                    cursor = connection.cursor()
                    create_row = '''INSERT INTO FriendsList(parentId, facebookUrl, mutualFriends, createdAt, name) VALUES (%s, %s, %s, %s, %s)'''
                    cursor.execute(create_row, [  ID, url, int(mutual_frineds), int(time()), fio  ])
                    cursor.close()

            except Exception as err:
                pass



        if len(datalist) * 1.05 >= int(total_friends):
            break

    await about_save(page, browser, ID, friends_urls)
    return

def save_row(kye, main_block, additionalSelector, href, block, _ID):

    if kye == 'about':
        cursor = connection.cursor()
        create_row = '''INSERT INTO generalInformation(parentId, mainSelector, additionalSelector, linkSelector, blockName) VALUES (%s, %s, %s, %s, %s)'''
        cursor.execute(create_row, [  int(_ID), main_block, additionalSelector, href, block ])
        cursor.close()

    elif kye == 'about_work_and_education':
        cursor = connection.cursor()
        create_row = '''INSERT INTO workedInformation(parentId, mainSelector, additionalSelector, linkSelector, blockName) VALUES (%s, %s, %s, %s, %s)'''
        cursor.execute(create_row, [  int(_ID), main_block, additionalSelector, href, block ])
        cursor.close()

    elif kye == 'about_places':
        cursor = connection.cursor()
        create_row = '''INSERT INTO livingRaw(parentId, mainSelector, additionalSelector, linkSelector, blockName) VALUES (%s, %s, %s, %s, %s)'''
        cursor.execute(create_row, [  int(_ID), main_block, additionalSelector, href, block ])
        cursor.close()

    elif kye == 'about_contact_and_basic_info':
        cursor = connection.cursor()
        create_row = '''INSERT INTO contactsRaw(parentId, mainSelector, additionalSelector, linkSelector, blockName) VALUES (%s, %s, %s, %s, %s)'''
        cursor.execute(create_row, [  int(_ID), main_block, additionalSelector, href, block ])
        cursor.close()

    elif kye == 'about_family_and_relationships':
        cursor = connection.cursor()
        create_row = '''INSERT INTO familyRaw(parentId, mainSelector, additionalSelector, linkSelector, blockName) VALUES (%s, %s, %s, %s, %s)'''
        cursor.execute(create_row, [  int(_ID), main_block, additionalSelector, href, block ])
        cursor.close()

    elif kye == 'about_details':
        cursor = connection.cursor()
        create_row = '''INSERT INTO infoAbout(parentId, mainSelector, additionalSelector, linkSelector, blockName) VALUES (%s, %s, %s, %s, %s)'''
        cursor.execute(create_row, [  int(_ID), main_block, additionalSelector, href, block ])
        cursor.close()

    elif kye == 'about_life_events':
        cursor = connection.cursor()
        create_row = '''INSERT INTO eventsRaw(parentId, mainSelector, additionalSelector, linkSelector, blockName) VALUES (%s, %s, %s, %s, %s)'''
        cursor.execute(create_row, [  int(_ID), main_block, additionalSelector, href, block ])
        cursor.close()
    return

async def __save_row(kye, main, _ID):

    if kye == 'about':
        cursor = connection.cursor()
        create_row = '''INSERT INTO rawData_about(parentId, Text, createdAt) VALUES (%s, %s, %s)'''
        cursor.execute(create_row, [  int(_ID), main, time() ])
        cursor.close()

    elif kye == 'about_work_and_education':
        cursor = connection.cursor()
        create_row = '''INSERT INTO rawData_work(parentId, Text, createdAt) VALUES (%s, %s, %s)'''
        cursor.execute(create_row, [  int(_ID), main, time() ])
        cursor.close()

    elif kye == 'about_places':
        cursor = connection.cursor()
        create_row = '''INSERT INTO rawData_places(parentId, Text, createdAt) VALUES (%s, %s, %s)'''
        cursor.execute(create_row, [  int(_ID), main, time() ])
        cursor.close()

    elif kye == 'about_contact_and_basic_info':
        cursor = connection.cursor()
        create_row = '''INSERT INTO rawData_contacts(parentId, Text, createdAt) VALUES (%s, %s, %s)'''
        cursor.execute(create_row, [  int(_ID), main, time() ])
        cursor.close()

    elif kye == 'about_family_and_relationships':
        cursor = connection.cursor()
        create_row = '''INSERT INTO rawData_family(parentId, Text, createdAt) VALUES (%s, %s, %s)'''
        cursor.execute(create_row, [  int(_ID), main, time() ])
        cursor.close()

    elif kye == 'about_details':
        cursor = connection.cursor()
        create_row = '''INSERT INTO rawData_info(parentId, Text, createdAt) VALUES (%s, %s, %s)'''
        cursor.execute(create_row, [  int(_ID), main, time() ])
        cursor.close()

    elif kye == 'about_life_events':
        cursor = connection.cursor()
        create_row = '''INSERT INTO rawData_events(parentId, Text, createdAt) VALUES (%s, %s, %s)'''
        cursor.execute(create_row, [  int(_ID), main, time() ])
        cursor.close()
    return


async def about_save(page, browser, ID, friends_urls):
    about = {}
    for i, url_fb in enumerate(friends_urls):


        cursor = connection.cursor()
        cursor.execute('''UPDATE users SET complete = %s, status = 'infoParsing' WHERE id = %s''', [i+1, ID])

        view = '''SELECT id FROM friendsList WHERE facebookUrl = %s AND parentId = %s'''
        cursor.execute(view, [str(url_fb[0]), int(ID)])
        get = cursor.fetchone()
        _ID = get[0]
        _ID = int(_ID)

        if 'profile.php' in url_fb[0]:
            url = f'{url_fb[0]}&sk=about' 
        else:
            url = f'{url_fb[0]}/about'

        await page.goto(url)
        await page.waitFor(5000)

        html_code = await page.evaluate('() => document.documentElement.outerHTML')
        soup = BeautifulSoup(html_code, 'html.parser')     
        await get_information(soup, url_fb, url, 'about', page, html_code, _ID)

        for index, kye in enumerate(['about_work_and_education', 'about_places', 'about_contact_and_basic_info', 'about_family_and_relationships', 'about_details', 'about_life_events']):
            index += 1
            if 'profile.php' in url_fb[0]:
                url = f'{url_fb[0]}&sk={kye}' 
            else:
                url = f'{url_fb[0]}/{kye}'

            await page.goto(url)
            await page.waitFor(6500)

            html_code = await page.evaluate('() => document.documentElement.outerHTML')
            soup = BeautifulSoup(html_code, 'html.parser')     
            await get_information(soup, url_fb, url, kye, page, html_code, _ID)
    cursor = connection.cursor()
    cursor.execute('''UPDATE users SET status = 'completed', updateAt = %s WHERE id = %s''', [time(), ID])
    cursor.close()
    return await browser.close()


async def get_information(soup, url_fb, url, kye, page, html_code, _ID):
    if not os.path.exists(path = f'{login}/friends/{url_fb[1].strip()}'):
        os.mkdir(path = f'{login}/friends/{url_fb[1].strip()}')

    with open(f'{login}/friends/{url_fb[1].strip()}/{kye}.html', 'w', encoding='utf-8') as f:
        f.write(html_code)


    data = []
    start = soup.select('div[class="dati1w0a tu1s4ah4 f7vcsfb0 discj3wi"]')
    if not start:
        while True:
            await asyncio.sleep(20)
            await page.goto(url)
            await page.waitFor(30000)
            html_code = await page.evaluate('() => document.documentElement.outerHTML')
            soup = BeautifulSoup(html_code, 'html.parser')   
            start = soup.select('div[class="dati1w0a tu1s4ah4 f7vcsfb0 discj3wi"]')
            if start:
                start = start[0]
                with open(f'{login}/friends/{url_fb[1].strip()}/{kye}.html', 'w', encoding='utf-8') as f:
                    f.write(html_code)
                break

    else:
        start = start[0]
    text = start.find_all(text = True)
    for i in text:
        await __save_row(kye, i, _ID)


    for selector in start.select('div[class="tu1s4ah4"]') + start.select('div[class="c9zspvje"]') + start.select('div[class="oygrvhab"]'):
        block = selector.select('span[class="d2edcug0 hpfvmrgz qv66sw1b c1et5uql lr9zc1uh a8c37x1j keod5gw0 nxhoafnm aigsh9s9 d3f4x2em fe6kdd0r mau55g9w c8b282yb mdeji52x a5q79mjw g1cxx5fr lrazzd5p oo9gr5id"]')
        if block:
            block = block[0].text.strip()
        elif selector.select('span[class="d2edcug0 hpfvmrgz qv66sw1b c1et5uql lr9zc1uh a8c37x1j keod5gw0 nxhoafnm aigsh9s9 d3f4x2em fe6kdd0r mau55g9w c8b282yb iv3no6db jq4qci2q a3bd9o3v ekzkrbhg oo9gr5id"]'):
            block = selector.select('span[class="d2edcug0 hpfvmrgz qv66sw1b c1et5uql lr9zc1uh a8c37x1j keod5gw0 nxhoafnm aigsh9s9 d3f4x2em fe6kdd0r mau55g9w c8b282yb iv3no6db jq4qci2q a3bd9o3v ekzkrbhg oo9gr5id"]')[0].text.strip()
        else:
            block = ''
        if kye == 'about_places':
            block = 'Места проживания'

        if selector.select('div[class="j83agx80 cbu4d94t ew0dbk1b irj2b8pg"]'):
            for selector in selector.select('div[class="j83agx80 cbu4d94t ew0dbk1b irj2b8pg"]'):
                main = selector.select('div[class="ii04i59q a3bd9o3v jq4qci2q oo9gr5id tvmbv18p"]')
                if main:
                    main = main[0].text.strip()
                elif selector.select('div[class="ii04i59q a3bd9o3v jq4qci2q oo9gr5id"]'):
                    main = selector.select('div[class="ii04i59q a3bd9o3v jq4qci2q oo9gr5id"]')[0].text.strip()
                elif selector.select('span[class="d2edcug0 hpfvmrgz qv66sw1b c1et5uql lr9zc1uh a8c37x1j keod5gw0 nxhoafnm aigsh9s9 d3f4x2em fe6kdd0r mau55g9w c8b282yb iv3no6db jq4qci2q a3bd9o3v b1v8xokw oo9gr5id hzawbc8m"]'):
                    main = selector.select('span[class="d2edcug0 hpfvmrgz qv66sw1b c1et5uql lr9zc1uh a8c37x1j keod5gw0 nxhoafnm aigsh9s9 d3f4x2em fe6kdd0r mau55g9w c8b282yb iv3no6db jq4qci2q a3bd9o3v b1v8xokw oo9gr5id hzawbc8m"]')[0].text.strip()
                else:
                    continue

                second = selector.select('span[class="j5wam9gi e9vueds3 m9osqain"]')
                if second:
                    second = second[0].text.strip()
                elif selector.select('span[class="d2edcug0 hpfvmrgz qv66sw1b c1et5uql lr9zc1uh sq6gx45u a3bd9o3v b1v8xokw m9osqain hzawbc8m"]'):
                    second = selector.select('span[class="d2edcug0 hpfvmrgz qv66sw1b c1et5uql lr9zc1uh sq6gx45u a3bd9o3v b1v8xokw m9osqain hzawbc8m"]')[0].text.strip()
                else:
                    second = ''

                if selector.select('a[class="oajrlxb2 g5ia77u1 qu0x051f esr5mh6w e9989ue4 r7d6kgcz rq0escxv nhd2j8a9 nc684nl6 p7hjln8o kvgmc6g5 cxmmr5t8 oygrvhab hcukyx3x jb3vyjys rz4wbd8a qt6c0cv9 a8nywdso i1ao9s8h esuyzwwr f1sip0of lzcic4wl gmql0nx0 gpro0wi8"]'):
                    href = selector.select('a[class="oajrlxb2 g5ia77u1 qu0x051f esr5mh6w e9989ue4 r7d6kgcz rq0escxv nhd2j8a9 nc684nl6 p7hjln8o kvgmc6g5 cxmmr5t8 oygrvhab hcukyx3x jb3vyjys rz4wbd8a qt6c0cv9 a8nywdso i1ao9s8h esuyzwwr f1sip0of lzcic4wl gmql0nx0 gpro0wi8"]')[0]['href']
                else:
                    href = ''

                if [main, second] not in data:
                    data.append([main, second])
                    save_row(kye, main, second, href, block, _ID)

        if selector.select('div[class="rq0escxv l9j0dhe7 du4w35lb j83agx80 pfnyh3mw jifvfom9 gs1a9yip owycx6da btwxx1t3 jb3vyjys b5q2rw42 lq239pai mysgfdmx hddg9phg"]'):
            for selector in selector.select('div[class="rq0escxv l9j0dhe7 du4w35lb j83agx80 pfnyh3mw jifvfom9 gs1a9yip owycx6da btwxx1t3 jb3vyjys b5q2rw42 lq239pai mysgfdmx hddg9phg"]'):
                main = selector.select('div[class="ii04i59q a3bd9o3v jq4qci2q oo9gr5id tvmbv18p"]')
                if main:
                    main = main[0].text.strip()
                elif selector.select('div[class="ii04i59q a3bd9o3v jq4qci2q oo9gr5id"]'):
                    main = selector.select('div[class="ii04i59q a3bd9o3v jq4qci2q oo9gr5id"]')[0].text.strip()
                elif selector.select('span[class="d2edcug0 hpfvmrgz qv66sw1b c1et5uql lr9zc1uh a8c37x1j keod5gw0 nxhoafnm aigsh9s9 d3f4x2em fe6kdd0r mau55g9w c8b282yb iv3no6db jq4qci2q a3bd9o3v b1v8xokw oo9gr5id hzawbc8m"]'):
                    main = selector.select('span[class="d2edcug0 hpfvmrgz qv66sw1b c1et5uql lr9zc1uh a8c37x1j keod5gw0 nxhoafnm aigsh9s9 d3f4x2em fe6kdd0r mau55g9w c8b282yb iv3no6db jq4qci2q a3bd9o3v b1v8xokw oo9gr5id hzawbc8m"]')[0].text.strip()
                else:
                    continue

                second = selector.select('span[class="j5wam9gi e9vueds3 m9osqain"]')
                if second:
                    second = second[0].text.strip()
                elif selector.select('span[class="d2edcug0 hpfvmrgz qv66sw1b c1et5uql lr9zc1uh sq6gx45u a3bd9o3v b1v8xokw m9osqain hzawbc8m"]'):
                    second = selector.select('span[class="d2edcug0 hpfvmrgz qv66sw1b c1et5uql lr9zc1uh sq6gx45u a3bd9o3v b1v8xokw m9osqain hzawbc8m"]')[0].text.strip()
                else:
                    second = ''
                
                if selector.select('a[class="oajrlxb2 g5ia77u1 qu0x051f esr5mh6w e9989ue4 r7d6kgcz rq0escxv nhd2j8a9 nc684nl6 p7hjln8o kvgmc6g5 cxmmr5t8 oygrvhab hcukyx3x jb3vyjys rz4wbd8a qt6c0cv9 a8nywdso i1ao9s8h esuyzwwr f1sip0of lzcic4wl gmql0nx0 gpro0wi8"]'):
                    href = selector.select('a[class="oajrlxb2 g5ia77u1 qu0x051f esr5mh6w e9989ue4 r7d6kgcz rq0escxv nhd2j8a9 nc684nl6 p7hjln8o kvgmc6g5 cxmmr5t8 oygrvhab hcukyx3x jb3vyjys rz4wbd8a qt6c0cv9 a8nywdso i1ao9s8h esuyzwwr f1sip0of lzcic4wl gmql0nx0 gpro0wi8"]')[0]['href']
                else:
                    href = ''

                if [main, second] not in data:
                    data.append([main, second])
                    save_row(kye, main, second, href, block, _ID)

        main = selector.select('div[class="ii04i59q a3bd9o3v jq4qci2q oo9gr5id tvmbv18p"]')
        if main:
            main = main[0].text.strip()
        elif selector.select('div[class="ii04i59q a3bd9o3v jq4qci2q oo9gr5id"]'):
            main = selector.select('div[class="ii04i59q a3bd9o3v jq4qci2q oo9gr5id"]')[0].text.strip()
        elif selector.select('span[class="d2edcug0 hpfvmrgz qv66sw1b c1et5uql lr9zc1uh a8c37x1j keod5gw0 nxhoafnm aigsh9s9 d3f4x2em fe6kdd0r mau55g9w c8b282yb iv3no6db jq4qci2q a3bd9o3v b1v8xokw oo9gr5id hzawbc8m"]'):
            main = selector.select('span[class="d2edcug0 hpfvmrgz qv66sw1b c1et5uql lr9zc1uh a8c37x1j keod5gw0 nxhoafnm aigsh9s9 d3f4x2em fe6kdd0r mau55g9w c8b282yb iv3no6db jq4qci2q a3bd9o3v b1v8xokw oo9gr5id hzawbc8m"]')[0].text.strip()
        else:
            continue

        second = selector.select('span[class="j5wam9gi e9vueds3 m9osqain"]')
        if second:
            second = second[0].text.strip()
        elif selector.select('span[class="d2edcug0 hpfvmrgz qv66sw1b c1et5uql lr9zc1uh sq6gx45u a3bd9o3v b1v8xokw m9osqain hzawbc8m"]'):
            second = selector.select('span[class="d2edcug0 hpfvmrgz qv66sw1b c1et5uql lr9zc1uh sq6gx45u a3bd9o3v b1v8xokw m9osqain hzawbc8m"]')[0].text.strip()
        else:
            second = ''
        if selector.select('a[class="oajrlxb2 g5ia77u1 qu0x051f esr5mh6w e9989ue4 r7d6kgcz rq0escxv nhd2j8a9 nc684nl6 p7hjln8o kvgmc6g5 cxmmr5t8 oygrvhab hcukyx3x jb3vyjys rz4wbd8a qt6c0cv9 a8nywdso i1ao9s8h esuyzwwr f1sip0of lzcic4wl gmql0nx0 gpro0wi8"]'):
            href = selector.select('a[class="oajrlxb2 g5ia77u1 qu0x051f esr5mh6w e9989ue4 r7d6kgcz rq0escxv nhd2j8a9 nc684nl6 p7hjln8o kvgmc6g5 cxmmr5t8 oygrvhab hcukyx3x jb3vyjys rz4wbd8a qt6c0cv9 a8nywdso i1ao9s8h esuyzwwr f1sip0of lzcic4wl gmql0nx0 gpro0wi8"]')[0]['href']
        else:
            href = ''

        if [main, second] not in data:
            data.append([main, second])
            save_row(kye, main, second, href, block, _ID)

    return

proxy = ''#

ID = sys.argv[1]
ID = int(ID)

cursor = connection.cursor()
view = '''select login, password from users where id = %s'''
cursor.execute(view, ([int(ID)]))
get = cursor.fetchone()

get = True
if get:
    login = get[0] 
    password = get[1] 

    try:
        asyncio.run(main(ID, proxy, login, password))   
    except Exception as err:
        print(err)
        cursor = connection.cursor()
        cursor.execute('''UPDATE users SET status = %s WHERE id = %s''', [err, ID])
        cursor.close()
        print(err)

else:
    print('Wrong taskID')

