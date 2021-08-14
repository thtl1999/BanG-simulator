
import os
import requests
import sys
import fileinput
import re
import json
#import urllib.request

#musicnamecode = '106'
#pyinstaller --onefile  getmusicscore.py

def custom_score(mcode):
    songinfo = requests.get('https://bestdori.com/api/post/details?id=' + mcode).json()



    if not os.path.isfile('data/music/bgm'+mcode+'.mp3'):
        f5 = open('data/music/bgm'+mcode+'.mp3','wb')
        mp3down = requests.get(songinfo['post']['song']['audio'])
        f5.write(mp3down.content)
        f5.close()

    notedata = songinfo['post']['notes']
    #print(notedata)

    fw = open("data/score/" + mcode + "ex.txt", 'w')

    fw.write('46\n'+str('111'))
    fw.write('\n0/0/0')

    for note in notedata:

        print(note)
        b = str(note['beat'])
        if note['type'] == 'System' and note['cmd'] == 'BPM':
            fw.write('\n'+ b + '/20/' + str(note['bpm']))
            continue
        if note['type'] != 'Note':
            continue

        if 'flick' in note:
            if note['note'] == 'Single': t = '/2/'
            if note['note'] == 'Slide':
                if note['pos'] == 'A':
                    t = '/12/'
                else:
                    t = '/13/'
        else:
            if note['note'] == 'Single': t = '/1/'
            if note['note'] == 'Slide':
                if 'end' in note:
                    if note['pos'] == 'A':
                        t = '/5/'
                    else:   #B
                        t = '/8/'
                else:
                    if note['pos'] == 'A':
                        t = '/4/'
                    else:   #B
                        t = '/7/'

        fw.write('\n' + b + t + str(note['lane']))
    fw.close()
    return


musicnamecode2 = input("write code: ")

if 'bestdori' in musicnamecode2:
    custom_score(musicnamecode2.replace('bestdori ',''))
    quit(0)

musicnamecode = musicnamecode2[0:3]

print(musicnamecode2)

if musicnamecode2.find('music') != -1:
    if not os.path.isfile('data/music/bgm'+musicnamecode+'.mp3'):
        f5 = open('data/music/bgm'+musicnamecode+'.mp3','wb')
        #urllib.request.urlretrieve('https://res.bangdream.ga/assets/sound/bgm'+musicname+'.mp3', 'music/'+musicname+'.mp3')
        #responsemp3 = urllib.request.urlretrieve('http://res.bangdream.ga/assets/sound/bgm'+musicname+'.mp3','music/'+musicname+'.mp3')
        #mp3data = responsemp3.read()
        #f5.close()
        mp3down = requests.get('http://res.bandori.ga/assets/sound/bgm'+musicnamecode+'_rip/bgm' + musicnamecode + '.mp3')
        f5.write(mp3down.content)
        f5.close()
else:
    musicnamecode = musicnamecode2

#check if special
if musicnamecode.find('+') != -1:
    isspecialchart = 1
    musicnamecode = musicnamecode[0:3]
else:
    isspecialchart = 0

if isspecialchart == 1: #check if request special
    # get bms file from bangdream database
    isspecialchart = 1
    if not os.path.isfile('scorebms/' + musicnamecode + 'sp.txt'):
        print('download bms from bangdream database')
        req = requests.get('https://api.bandori.ga/v1/jp/music/' + musicnamecode)
        data = req.json()
        musicnamestring = data["chartAssetBundleName"]
        req = requests.get(
            'https://res.bandori.ga/assets/musicscore/' + musicnamecode + '_rip/' + musicnamestring + '_special.txt')
        html = req.text
        f1 = open('scorebms/' + musicnamecode + 'sp.txt', 'w')
        f1.write(html)
        f1.close()
    else:
        print("alreay have music score")
else:
    #get bms file from bangdream database
    if not os.path.isfile('scorebms/'+musicnamecode+'ex.txt'):
        print('download bms from bangdream database')
        req = requests.get('https://api.bandori.ga/v1/jp/music/'+musicnamecode)
        data = req.json()
        musicnamestring = data["chartAssetBundleName"]
        req = requests.get('https://res.bandori.ga/assets/musicscore/'+musicnamecode+'_rip/'+musicnamestring+'_expert.txt')
        html = req.text
        f1 = open('scorebms/'+musicnamecode+'ex.txt','w')
        f1.write(html)
        f1.close()
    else:
        print("alreay have music score")


#parse bms data
if isspecialchart == 0:
    fr = open("scorebms/"+musicnamecode+'ex.txt','r')
    fw = open("data/score/" + musicnamecode + "ex.txt", 'w')
else:
    fr = open("scorebms/"+musicnamecode+'sp.txt','r')
    fw = open("data/score/" + musicnamecode + "sp.txt", 'w')

se = {}

print(fr.encoding)

if fr.encoding == 'cp949':
    fr.close()
    if isspecialchart == 0:
        fr = open("scorebms/"+musicnamecode+'ex.txt','r', encoding='UTF8')
    else:
        fr = open("scorebms/"+musicnamecode+'sp.txt','r', encoding='UTF8')

#header read
#it should be modified to handle bpm over 256
while True:
    line = fr.readline()
    #print(line)
    if line.find('MAIN') != -1:
        break
    if line.find('WAV') != -1:
        se[line[4:6]] = line[7:-1]
        #print(se[line[4:6]])
    elif line.find('BPM') != -1:
        bpm = float(line[5:-1])
    else:
        continue


print(se)
print('start bpm:' + str(bpm))


#main read
longstarted = []            #to indicate there was longnotestart before a line
for i in range(0,8):
    longstarted.append(False)

note = []   #all the notes will be put here. note has notese, notetype, notebeat, notelane, noteproperty, notetiming
#notese: put se code, noetype: decide (later) normal, longstart, longend, longflick, slide, slidefinish notebeat: decide beat
#notelane: lane of this note noteproperty: decide skill, fever, extra notetiming: calculate time with bpm and notebeat

noteindex = 0   #to indicate note number
errorinbms = 0
while True:
    line = fr.readline()
    if not line: break

    if line.find('#') == -1: #only read for #
        continue

    nowbeat = float(line[1:4])  #first 3 digit indicate beat
    lanestring = line[4:6]      #last 2 digit indicate lane number and type


    #select lane number
    if lanestring[1] == '6': lane = 1
    if lanestring[1] == '1': lane = 2
    if lanestring[1] == '2': lane = 3
    if lanestring[1] == '3': lane = 4
    if lanestring[1] == '4': lane = 5
    if lanestring[1] == '5': lane = 6
    if lanestring[1] == '8': lane = 7
    #select long note line
    #if lanestring[0] == '1':
    isitlongline = False
    if lanestring[0] == '5':
        isitlongline = True
    # special lane number
    if lanestring == '01': lane = 0

    #BGA, layer, poor exception
    if lanestring == '04': continue
    if lanestring == '06': continue
    if lanestring == '07': continue


    #read a line
    beatnumber = 0  # to count how much digit are there. to calculate beat
    i = 7           # start string number of line
    thislinenoteindex = noteindex   # save current note index to check
    while (i+2) < len(line):        # read until nothing to read
        if line[i:i+2] != '00':     #if 00, don't create note and read next
            note.append({})
            #note[noteindex] = {'notese': line[i:i+2]}
            note[noteindex]['notese'] = line[i:i+2]       # notetype is selected by se
            note[noteindex]['notebeat'] = beatnumber      # notebeat should be corrected after read all digit in this line
            note[noteindex]['notelane'] = lane              #notelane
            note[noteindex]['notetype'] = 'none'            #not yet decieded

            if lanestring == '03':                          #bpm control
                note[noteindex]['notese'] = int(line[i:i+2],16)
                note[noteindex]['notelane'] = 0
                note[noteindex]['notetype'] = 'special'

            if lanestring == '01':                          #bgm, fever control
                note[noteindex]['notetype'] = 'special'

            if isitlongline == True:                        #long note indicate
                note[noteindex]['notetype'] = 'long'

            if lanestring[0] == '3':
                note[noteindex]['notetype'] = 'hidden'

            noteindex += 1                              # if note exist, index++


        beatnumber += 1                                 # count beat
        i = i+2                                         # every note is 2 digit number(string)

    #calculate notebeat and select note type
    for i in range(thislinenoteindex , noteindex):
        tempbeat = nowbeat + 1/beatnumber*note[i]['notebeat'] #calculate notebeat
        note[i]['notebeat'] = tempbeat
        print(note[i])

        # error correction
        if not note[i]['notese'] in se:
            if not note[i]['notelane'] == 0: #if this is not special note
                print('error')
                errorinbms = 1
                #note[i]['noteproperty'] = 'none'
                for secode, sename in se.items():
                    if sename == 'bd.wav':
                        note[i]['notese'] = secode
                print(note[i]['notese'])


        if note[i]['notelane'] == 0:                #handle special type of note
            if lanestring == '03':
                note[i]['noteproperty'] = 'bpmchange'
                continue
            if note[i]['notese'] == '01':
                note[i]['noteproperty'] = 'bgm'
            if se[note[i]['notese']] == se['01']: #very special case like music 085
                note[i]['noteproperty'] = 'bgm'
            if se[note[i]['notese']] == 'cmd_fever_ready.wav':
                note[i]['noteproperty'] = 'feverready'
            if se[note[i]['notese']] == 'cmd_fever_start.wav':
                note[i]['noteproperty'] = 'feverstart'
            if se[note[i]['notese']] == 'cmd_fever_end.wav':
                note[i]['noteproperty'] = 'feverend'
            if se[note[i]['notese']] == 'cmd_fever_checkpoint.wav':
                note[i]['noteproperty'] = 'fevercheck'



        elif note[i]['notetype'] == 'long':     #long
            if longstarted[lane] == False:          #if this is long note start
                note[i]['notetype'] = 'longstart'
                longstarted[lane] = True
                if se[note[i]['notese']] == 'bd.wav':
                    note[i]['noteproperty'] = 'none'
                if se[note[i]['notese']] == 'skill.wav':
                    note[i]['noteproperty'] = 'skill'
                if se[note[i]['notese']] == 'fever_note.wav':
                    note[i]['noteproperty'] = 'fever'
            else:                                   #if this is long note last
                longstarted[lane] = False
                if se[note[i]['notese']] == 'bd.wav':
                    note[i]['noteproperty'] = 'none'
                    note[i]['notetype'] = 'longend'
                if se[note[i]['notese']] == 'flick.wav':
                    note[i]['noteproperty'] = 'none'
                    note[i]['notetype'] = 'longflick'
                if se[note[i]['notese']] == 'skill.wav':
                    note[i]['noteproperty'] = 'skill'
                    note[i]['notetype'] = 'longend'
                if se[note[i]['notese']] == 'fever_note.wav':
                    note[i]['noteproperty'] = 'fever'
                    note[i]['notetype'] = 'longend'
                if se[note[i]['notese']] == 'fever_note_flick.wav':
                    note[i]['noteproperty'] = 'fever'
                    note[i]['notetype'] = 'longflick'

        elif note[i]['notetype'] == 'hidden':     #hidden
                if se[note[i]['notese']] == 'slide_a.wav':
                    note[i]['noteproperty'] = 'none'
                    note[i]['notetype'] = 'slideahidden'
                if se[note[i]['notese']] == 'slide_b.wav':
                    note[i]['noteproperty'] = 'none'
                    note[i]['notetype'] = 'slidebhidden'
                if se[note[i]['notese']].startswith('slide_a_LS'):
                    note[i]['notelane'] -= float(se[note[i]['notese']][10:12])/100.0
                    note[i]['noteproperty'] = 'none'
                    note[i]['notetype'] = 'slideahidden'
                if se[note[i]['notese']].startswith('slide_a_RS'):
                    note[i]['notelane'] += float(se[note[i]['notese']][10:12])/100.0
                    note[i]['noteproperty'] = 'none'
                    note[i]['notetype'] = 'slideahidden'
                if se[note[i]['notese']].startswith('slide_b_LS'):
                    note[i]['notelane'] -= float(se[note[i]['notese']][10:12])/100.0
                    note[i]['noteproperty'] = 'none'
                    note[i]['notetype'] = 'slidebhidden'
                if se[note[i]['notese']].startswith('slide_b_RS'):
                    note[i]['notelane'] += float(se[note[i]['notese']][10:12])/100.0
                    note[i]['noteproperty'] = 'none'
                    note[i]['notetype'] = 'slidebhidden'

        else:                                   #normal, flick, slide
            if se[note[i]['notese']] == 'bd.wav':
                note[i]['noteproperty'] = 'none'
                note[i]['notetype'] = 'normal'
            if se[note[i]['notese']] == 'flick.wav':
                note[i]['noteproperty'] = 'none'
                note[i]['notetype'] = 'flick'
            if se[note[i]['notese']] == 'skill.wav':
                note[i]['noteproperty'] = 'skill'
                note[i]['notetype'] = 'normal'
            if se[note[i]['notese']] == 'slide_a.wav':
                note[i]['noteproperty'] = 'none'
                note[i]['notetype'] = 'slidea'
            if se[note[i]['notese']] == 'slide_end_a.wav':
                note[i]['noteproperty'] = 'none'
                note[i]['notetype'] = 'slideaend'
            if se[note[i]['notese']] == 'slide_end_flick_a.wav':
                note[i]['noteproperty'] = 'none'
                note[i]['notetype'] = 'slideaendflick'
            if se[note[i]['notese']] == 'slide_b.wav':
                note[i]['noteproperty'] = 'none'
                note[i]['notetype'] = 'slideb'
            if se[note[i]['notese']] == 'slide_end_b.wav':
                note[i]['noteproperty'] = 'none'
                note[i]['notetype'] = 'slidebend'
            if se[note[i]['notese']] == 'slide_end_flick_b.wav':
                note[i]['noteproperty'] = 'none'
                note[i]['notetype'] = 'slidebendflick'
            if se[note[i]['notese']] == 'fever_note.wav':
                note[i]['noteproperty'] = 'fever'
                note[i]['notetype'] = 'normal'
            if se[note[i]['notese']] == 'fever_note_flick.wav':
                note[i]['noteproperty'] = 'fever'
                note[i]['notetype'] = 'flick'
            if se[note[i]['notese']] == 'fever_slide_a.wav': #special case like music 113
                note[i]['noteproperty'] = 'fever'
                note[i]['notetype'] = 'slidea'
            if se[note[i]['notese']] == 'fever_slide_b.wav':
                note[i]['noteproperty'] = 'fever'
                note[i]['notetype'] = 'slideb'
            if se[note[i]['notese']] == 'fever_slide_end_a.wav': #special case like music 015
                note[i]['noteproperty'] = 'fever'
                note[i]['notetype'] = 'slideaend'
            if se[note[i]['notese']] == 'fever_slide_end_b.wav':
                note[i]['noteproperty'] = 'fever'
                note[i]['notetype'] = 'slidebend'
            if se[note[i]['notese']] == 'fever_note_slide_a.wav': #special case like music 024
                note[i]['noteproperty'] = 'fever'
                note[i]['notetype'] = 'slidea'
            if se[note[i]['notese']] == 'fever_note_slide_end_a.wav':
                note[i]['noteproperty'] = 'fever'
                note[i]['notetype'] = 'slideaend'
            if se[note[i]['notese']] == 'fever_note_slide_b.wav': #special case like music 054
                note[i]['noteproperty'] = 'fever'
                note[i]['notetype'] = 'slideb'
            if se[note[i]['notese']] == 'directional_fl_l.wav':
                note[i]['noteproperty'] = 'none'
                note[i]['notetype'] = 'directional_fl_l'
            if se[note[i]['notese']] == 'directional_fl_r.wav':
                note[i]['noteproperty'] = 'none'
                note[i]['notetype'] = 'directional_fl_r'

        print(note[i])

#print(note)
#sort notes by beat to calculate timing (bpm change need sort)
sortednote = sorted(note,key=lambda k: k['notebeat'])
#special sort for like bgm153. slide end should be first if in same beat
specialsort = ['slideaend','slidebend','slideaendflick','slidebendflick']
for i in range(len(sortednote) - 1):
    if sortednote[i]['notebeat'] == sortednote[i+1]['notebeat']:
        if sortednote[i+1]['notetype'] in specialsort:
            if not sortednote[i]['notetype'] in specialsort:
                sortednote[i], sortednote[i+1] = sortednote[i+1], sortednote[i]
                print('!!!! special sort')

#print(sortednote)

#calculate timing
bitsec = 60/bpm
savedtiming = 0
savedbeat = 0
dfllt=-1
dflrt=-1
dfll=[0,0,0,0,0,0,0,0]
dflr=[0,0,0,0,0,0,0,0]
for i in range(len(sortednote)):
    sortednote[i]['notebeat'] *= 4
    print(sortednote[i])
    if sortednote[i]['noteproperty'] == 'bpmchange':
        savedtiming = savedtiming + (sortednote[i]['notebeat']-savedbeat)*bitsec
        savedbeat = sortednote[i]['notebeat']
        bitsec = 60/(sortednote[i]['notese'])

    sortednote[i]['timing'] = savedtiming + (sortednote[i]['notebeat']-savedbeat)*bitsec
    print(sortednote[i])

if True:    #convert to my simulator
    fw.write('46\n'+str(bpm))
    
    for i in range(len(sortednote)):
        if dfllt != -1 and dfllt < sortednote[i]['notebeat']:
            print('dfll:', dfll);
            dfllts = str(dfllt)
            width = 0
            for k in range(1,8):
                if dfll[k]:
                    width = width + 1
                elif width:
                    fw.write('\n'+ dfllts + '/' + str(50+width) + '/' + str(k-1))
                    width = 0
                dfll[k]=0
            if width:
                fw.write('\n'+ dfllts + '/' + str(50+width) + '/7')
                width = 0
            dfllt = -1
        if dflrt != -1 and dflrt < sortednote[i]['notebeat']:
            print('dflr:', dflr);
            dflrts = str(dflrt)
            width = 0
            for k in range(1,8):
                if dflr[k]:
                    width = width + 1
                elif width:
                    fw.write('\n'+ dflrts + '/' + str(60+width) + '/' + str(k-width))
                    width = 0
                dflr[k]=0
            if width:
                fw.write('\n'+ dflrts + '/' + str(60+width) + '/' + str(8-width))
                width = 0
            dflrt = -1
        b = str(sortednote[i]['notebeat'])
        if sortednote[i]['noteproperty'] == 'bgm':
            fw.write('\n0/0/0')
            continue
        if sortednote[i]['noteproperty'] == 'bpmchange':
            fw.write('\n'+ b + '/20/' + str(sortednote[i]['notese']))
            continue
        if sortednote[i]['notelane'] == 0:
            continue

        if sortednote[i]['notetype'] == 'normal':
            t = '/1/'
            if sortednote[i]['noteproperty'] == 'skill':
             t = '/11/'
        if sortednote[i]['notetype'] == 'flick':
            t = '/2/'
        if sortednote[i]['notetype'] == 'longstart':
            t = '/21/'
            if sortednote[i]['noteproperty'] == 'skill':
             t = '/31/'
        if sortednote[i]['notetype'] == 'longend':
            t = '/25/'
            if sortednote[i]['noteproperty'] == 'skill':
             t = '/32/'
        if sortednote[i]['notetype'] == 'longflick':
            t = '/26/'
        if sortednote[i]['notetype'] == 'slidea':
            t = '/4/'
        if sortednote[i]['notetype'] == 'slideaend':
            t = '/5/'
        if sortednote[i]['notetype'] == 'slideaendflick':
            t = '/12/'
        if sortednote[i]['notetype'] == 'slideahidden':
            t = '/41/'
        if sortednote[i]['notetype'] == 'slideb':
            t = '/7/'
        if sortednote[i]['notetype'] == 'slidebend':
            t = '/8/'
        if sortednote[i]['notetype'] == 'slidebendflick':
            t = '/13/'
        if sortednote[i]['notetype'] == 'slidebhidden':
            t = '/42/'
        if sortednote[i]['notetype'] == 'directional_fl_l':
            dfllt = sortednote[i]['notebeat']
            dfll[sortednote[i]['notelane']] = 1
            print('dfll:', dfll);
            continue
        if sortednote[i]['notetype'] == 'directional_fl_r':
            dflrt = sortednote[i]['notebeat']
            dflr[sortednote[i]['notelane']] = 1
            print('dflr:', dflr);
            continue
        fw.write('\n' + b + t + str(sortednote[i]['notelane']))
    if dfllt != -1:
        print('dfll:', dfll);
        dfllts = str(dfllt)
        width = 0
        for k in range(1,8):
            if dfll[k]:
                width = width + 1
            elif width:
                fw.write('\n'+ dfllts + '/' + str(50+width) + '/' + str(k-1))
                width = 0
            dfll[k]=0
        if width:
            fw.write('\n'+ dfllts + '/' + str(50+width) + '/7')
            width = 0
        dfllt = -1
    if dflrt != -1:
        print('dflr:', dflr);
        dflrts = str(dflrt)
        width = 0
        for k in range(1,8):
            if dflr[k]:
                width = width + 1
            elif width:
                fw.write('\n'+ dflrts + '/' + str(60+width) + '/' + str(k-width))
                width = 0
            dflr[k]=0
        if width:
            fw.write('\n'+ dflrts + '/' + str(60+width) + '/' + str(8-width))
            width = 0
        dflrt = -1


fr.close()
fw.close()

if errorinbms == 1:
    print("error in bms")