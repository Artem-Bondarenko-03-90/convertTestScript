import json
import os
import re
import random
import time
import datetime

from pathlib import Path

import pytz

from originalOscFile import originalOscFile
from pytz import timezone


if __name__ == '__main__':
    with open('settings.json', 'r', encoding='utf-8') as f:
        settings_file = json.load(f)

    addressSSNTI = settings_file['address_SSNTI']
    addressClientSSNTI = settings_file['addressClientSSNTI']
    token = settings_file['token']
    current_dir = settings_file['current_dir']
    clients_list = settings_file['clients']
    tz = timezone('Europe/Moscow')
    utc_tz = pytz.utc

    dir_path = current_dir
    originalOscDict = {}
    for dirs in list(os.walk(dir_path)):
        for file in dirs[2]:
            suf = str(Path(file).suffix).lower()
            fileName = str(Path(file)).replace(Path(file).suffix, '')
            if suf in ['.aura', '.bb', '.os1', '.os2', '.os3'] or re.fullmatch(
                    '.[td][0o][\S]', suf) or re.fullmatch('.[td][0o]', suf):
                st = (dirs[0] + '\\' + file).replace('\\', '/')
                if str(Path(file)).replace(Path(file).suffix, '') not in originalOscDict.keys():
                    originalOscDict[str(Path(file)).replace(Path(file).suffix, '')] = [[], suf]
                originalOscDict[str(Path(file)).replace(Path(file).suffix, '')][0].append(str(st))

    timestamp_start_test = datetime.datetime.now(tz)
    # сформируем объекты для исходых файлов осциллограмм
    originOscList = []
    for osc in originalOscDict.keys():
        originOsc = originalOscFile(osc, originalOscDict[osc][0], originalOscDict[osc][1])
        # разложим исходные файлы осциллограмм случайным образом по папкам клиентов
        client1 = random.choice(clients_list)
        originOsc.copyOriginalOscInClient(client1['directory'])
        originOsc.clientId = client1['id']
        originOscList.append(originOsc)

    # проверяем в цикле появление исходных файлов и их конвертированных копий в ССНТИ
    i=0
    while i < 70:
        # пауза 5 сек
        print('Цикл проверки: '+str(i+1))
        time.sleep(5)
        try:
            for osc in originOscList:
                filesList = osc.requestFilesFromClient(addressSSNTI, token)
                pathDict = {}
                for f in filesList:

                    lmd = datetime.datetime.strptime(str(f['lastModifiedDate'])[:-7], '%Y-%m-%dT%H:%M:%S.%f')
                    if utc_tz.localize(lmd) >= osc.createdTimestamp:
                        pathDict[f['path']] = f['convertFileResultId']
                for p in osc.parts_in_client:
                    if p in pathDict.keys() and osc.inSSNTItimestamp == None:
                        osc.inSSNTItimestamp = datetime.datetime.now(tz)
                    if p in pathDict.keys():
                        if pathDict[p] != None and osc.convertedTimestamp == None:
                            osc.convertedTimestamp = datetime.datetime.now(tz)
        except  Exception as ex:
            print(ex)
        i+=1

    timestamp_end_test = datetime.datetime.now(tz)

    # Вывод результатов теста
    j1=0
    j2=0
    sum1=0
    sum2=0
    for osc in originOscList:
        print('Name: '+str(osc.name)+ str(osc.suf))
        if osc.inSSNTItimestamp != None:
            print('Задержка времени появления в ССНТИ: ' + str((osc.inSSNTItimestamp - osc.createdTimestamp).seconds)+' с.')
            sum1 += (osc.inSSNTItimestamp - osc.createdTimestamp).seconds
            j1+=1
        else:
            print('! Осциллограмма не передана в ССНТИ')
        if osc.convertedTimestamp != None:
            print('Задержка времени конвертации: ' + str((osc.convertedTimestamp - osc.createdTimestamp).seconds) + ' с.')
            sum2 += (osc.convertedTimestamp - osc.createdTimestamp).seconds
            j2 += 1
        elif osc.inSSNTItimestamp != None:
            print('! Осциллограмма не сконвертирована')
        print('-----------------------------------------------------')
    if j1 > 0:
        print('Среднее время передачи осциллограмм в ССНТИ: '+str(sum1//j1)+' с.')
    if j2 > 0:
        print('Среднее время конвертации осциллограмм: '+str(sum2//j2)+' с.')
    print('Время тестирования: ' + str(timestamp_end_test - timestamp_start_test))

    # Очистим файлы исходных осциллограмм из папок клиентов
    for osc in originOscList:
        for p in osc.parts_in_client:
            os.remove(p)

    msg = str(input('Для завершения нажмите пробел'))