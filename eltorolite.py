#!/usr/bin/sudo python
# El Toro LITE
# 
# Coded by Jesse
# twitch.tv/oh_bother
#
# Lisences are for nerds. Er, I mean, do whatever with this. MIT or something.
# this "lite" version removes a lot of animations and similar cool stuff. :(
# also the client modified this code heavily. YMMV
#
# ElToro main code, this is going to work with V1 PCB.
# Assets are to be built into the eltoro/ass/ directory
#
# RPi Pinout:
#
#              3.3v 01|02 5v
#            GPIO02 03|04 5v
#            GPIO03 05|06 Gnd
#   RGB_OE - GPIO04 07|08 GPIO14 - BTN_Breakbeam
#               Gnd 09|10 GPIO15 - BTN_Coin
#  RGB_CLK - GPIO17 11|12 GPIO18 - BTN_Start
#    RGB_C - GPIO27 13|14 Gnd
#    RGB_A - GPIO22 15|16 GPIO23 - RGB_B2
#              3.3v 17|18 GPIO24 - BTN_P1Up
#   LED_DI - GPIO10 19|20 Gnd
#          - GPIO09 21|22 GPIO25 - BTN_P2Dn
#   LED_CI - GPIO11 23|24 GPIO08 - BTN_P2Up
#               Gnd 25|26 GPIO07 - BTN_P1Dn
#             ID_SD 27|28 ID_SC
#   RGB_R1 - GPIO05 29|30 Gnd
#   RGB_B1 - GPIO06 31|32 GPIO12 - RGB_R2
#   RGB_G1 - GPIO13 33|34 Gnd
#          - GPIO19 35|36 GPIO16 - RGB_G2
#    RGB_B - GPIO26 37|38 GPIO20 - RGB_D
#               GND 39|40 GPIO21 - RGB_LAT
#
# RGB display pixels are zero indexed. 
# png image row 64 is buttons and show lights
# 0, 1, 2, 3, 4, 5, 6...
# start, p1up, p2up, p2dn, p1dn, 3w pixels...
#
# Adafruit RGB Hat compatible, 32x64 pixels
# Adafruit Coin Slot
# Ws2803 LED Drivers
# Adafruit RGB LED Buttons with ws2801 LED strip
# Adafruit Breakbeam
# ALC4040 USB sound adapter
#
# James Congdon 11/22/2017 
# twitch.tv/oh_bother
#===================================================
#CREDITS SET TO 2 INITIAL STATE IS GAME FOR TESTING
#WIN SCORE IS SET TO 2
#===================================================

import os
import time
import random
import sys

from gpiozero import Button
from rgbmatrix import RGBMatrix, RGBMatrixOptions
from PIL import Image
from PIL import ImageFont, ImageDraw

import pygame
from threading import Thread

import Adafruit_WS2801
import Adafruit_GPIO.SPI as SPI


#Pins
pin_coin = 15 
pin_breakbeam = 14
pin_start = 18
pin_p1up = 24
pin_p1dn = 7
pin_p2up = 8
pin_p2dn = 25

pin_dout = 10
pin_cout = 11

#settings
frame_rate = 0.1
fade_rate = 0.03
down_limit = 4
win_score = 21
round_cost = 2
coin_each = 1 
button_inc = 1
min_score = 0
winWait = 2

idle_time = 40
guilt_time = 50

p1_upCol = (000, 000, 055)
p1_dnCol = (000, 000, 055)
p2_upCol = (000, 055, 000)
p2_dnCol = (000, 055, 000)

pixel_count = 32

#variables (globals)
credits = 0

p1_score = 0
p2_score = 0

idleInc = 0
#guiltInc = 0
startInc = 0
coinInc = 0
win1Inc = 0
win2Inc = 0
tieInc = 0

idleMax = 0
#guiltMax = 0
startMax = 0
coinMax = 0
win1Max = 0
win2Max = 0
tieMax = 0

baddnSfx = 0
badupSfx = 0
badhighSfx = 0
badlowSfx = 0
gooddnSfx = 0
goodupSfx = 0

idleFx = Image.new('RGB', (0, 0))
coinFx = Image.new('RGB', (0, 0))
win1Fx = Image.new('RGB', (0, 0))
win2Fx = Image.new('RGB', (0, 0))
tieFx = Image.new('RGB', (0, 0))
base = Image.new('RGBA', (64, 32))
 
#enable flags
startRun = 0
idleRun = 0
coinRun = 0
guiltRun = 0
gameWatch = 0
startWatch = 0
beamWatch = 0
beamBroke = 0
win1Run = 0
win2Run = 0
tieRun = 0

startWatch = 0
startPress = 0

p1hitWin = 0
p2hitWin = 0

tick = 0
tock = 0

#inputs
btn_coin = Button(pin_coin, hold_repeat=False)
btn_breakbeam = Button(pin_breakbeam, hold_repeat=False)
btn_start = Button(pin_start, hold_repeat=False, pull_up=False)
btn_p1up = Button(pin_p1up, hold_repeat=False, pull_up=False)
btn_p1dn = Button(pin_p1dn, hold_repeat=False, pull_up=False)
btn_p2up = Button(pin_p2up, hold_repeat=False, pull_up=False)
btn_p2dn = Button(pin_p2dn, hold_repeat=False, pull_up=False)

#initialize WS2801 Strip
pixels = Adafruit_WS2801.WS2801Pixels(pixel_count, clk=pin_cout, do=pin_dout)
pixels.clear()
pixels.show()

# Initialize mixer
pygame.mixer.pre_init(44100, -16, 2, 2048) # setup mixer to avoid sound lag
pygame.init()

# Configuration for the matrix
# THIS HAS TO BE AFTER THE BUTT AND AUDIO STUFF
options = RGBMatrixOptions()
options.rows = 32
options.chain_length = 2
options.parallel = 1
options.hardware_mapping = 'adafruit-hat'  # If you have an Adafruit HAT: 'adafruit-hat'

matrix = RGBMatrix(options = options)
    
#==============STARTUP STATES==============
def state_boot():
    #global constants
    global idleMax, startMax, coinMax, win1Max, win2Max, tieMax
    #global guiltMax
    
    #global sound fx
    global guiltSfx, coinSfx, baddnSfx, badupSfx, badhighSfx, badlowSfx, gooddnSfx, goodupSfx
    global win1Sfx, win2Sfx, tieSfx
    
    #global LED arrays
    global idleFx, coinFx, win1Fx, win2Fx, tieFx
    
    #global timers
    global t, t2
    
    print "boot message"
    
    #boot screen
    for thing in os.listdir("ass/boot"):
        if ".wav" in thing:
            #sound file name/location loaded up
            soundLoc = "ass/boot/" + thing
            effect = pygame.mixer.Sound(soundLoc)
            effect.play()
        
    file = "ass/boot/" + str(random.randint(1,2)) + ".png"
    
    if os.path.isfile(file):
        rgbimg = Image.open(file).convert('RGB')
        matrix.SetImage(rgbimg)
        
        for i in range(32):
            r, g, b = rgbimg.getpixel((64, i))
            for i in range(pixel_count):
                pixels.set_pixel_rgb(i, r, g, b)
            time.sleep(0.2) #flash through pixels
            pixels.show()
    else:
        print "no boot image"
    
    #load non-random sound files into global variables
    guiltSfx = pygame.mixer.Sound("ass/guilt/guilt.wav")
    coinSfx = pygame.mixer.Sound("ass/soundFx/coin.wav")
    
    #win sounds
    win1Sfx = pygame.mixer.Sound("ass/win/1.wav")
    win2Sfx = pygame.mixer.Sound("ass/win/2.wav")
    tieSfx = pygame.mixer.Sound("ass/win/t.wav")
    
    #button sfx
    baddnSfx = pygame.mixer.Sound("ass/soundFx/bbaddn.wav")
    badupSfx = pygame.mixer.Sound("ass/soundFx/bbadup.wav")
    badhighSfx = pygame.mixer.Sound("ass/soundFx/bbadhigh.wav")
    badlowSfx = pygame.mixer.Sound("ass/soundFx/bbadlow.wav")
    goodupSfx = pygame.mixer.Sound("ass/soundFx/bgoodup.wav")
    gooddnSfx = pygame.mixer.Sound("ass/soundFx/bgooddn.wav")
    
    #load sfx images into global variables
    idleFx = Image.open("ass/ledFx/idle.png").convert('RGB')
    #guiltFx = Image.open("ass/ledFx/idle.png").convert('RGB')
    coinFx = Image.open("ass/ledFx/coin.png").convert('RGB')
    win1Fx = Image.open("ass/ledFx/win1.png").convert('RGB')
    win2Fx = Image.open("ass/ledFx/win2.png").convert('RGB')
    tieFx = Image.open("ass/ledFx/tie.png").convert('RGB')
    
    #load max global values for fades
    idleMax, height = idleFx.size
    #guiltMax, height = 
    coinMax, height = coinFx.size
    win1Max, height = win1Fx.size
    win2Max, height = win2Fx.size
    tieMax, height = tieFx.size
    
    #correct for 0 index
    idleMax -= 1
    coinMax -= 1 
    win1Max -= 1
    win2Max -= 1
    tieMax -= 1
    startMax = 255
    
    #print str(idleMax) + " " + str(coinMax) + " " + str(win1Max) + " " + str(win2Max) + " " + str(tieMax)
    
    #start fade thread
    Thread(target=loop_LED).start()
    Thread.daemon = True
    
    #wait for sound to stop
    while pygame.mixer.get_busy():
        pass
    time.sleep(1)
    allClear()
    
    #make sure idle runs initially
    t = time.time() - idle_time
    t2 = time.time() - guilt_time
    
    return state_idle
    
#==============IDLING STATES==============
def state_idle():
    #global timing flags
    global tick, t, t2
    
    #global button/etc flags
    global idleRun
    global startPress, startRun, startWatch
    global beamWatch
  
    #break beam
    if (credits < 1) and (time.time() - t2 > guilt_time):
        beamWatch = 1
    else:
        beamWatch = 0  
        
    # #fade start if there's enough credits
    if credits >= round_cost:
    
        #enable start button
        startWatch = 1
    
        #fade start
        startRun = 1
        
        # #players hit start to gaem
        if startPress:
            startPress = 0
            startWatch = 0
            return state_game
   
    #timer for  idle screen
    #this just runs and ignores flags until it exist
    #so needs to be fast, 8 frames-ish
    
    #revision, idle was running every 30 seconds reported by client
    #if (time.time() - t) > idle_time:
    if time.time() - t > idle_time:
        creditScrn(1)
        t = time.time()
    elif coinRun:
        creditScrn(0)

    if tick:
        pixels.show()
        tick = 0
    
    return state_idle

#==============Game STATES==============
def state_game():
    #global startWatch
    global tick
    global startPress
    global gameWatch
    global idleRun
    
    idleRun = 0
    
    #enable player buttons    
    gameWatch = 1 

    #score to display
    displayScore()
    
    #flags/interaction
    #runs second so it shows bad number and rips it away from player
    scoreCheck()
    
    #starpress only active from scorecheck
    if startPress:
        gameWatch = 0
        startPress = 0
        if  p1_score == p2_score:
            return state_lannister
        elif p1_score >= win_score:
            return state_team1Win
        else:
            return state_team2Win
            
    #display them
    if tick:
        pixels.show()
        tick = 0

    return state_game
    
#================WIN states!===============
def state_team1Win():
    print "team1 wins"
    global tick
    global win1Run
    
    print "team 1 wins"
    win1 = Image.open("ass/win/1.png").convert('RGB')
    matrix.SetImage(win1)
    pygame.mixer.stop()
    win1Sfx.play()
    
    #led fx
    win1Run = 1
    
    #wait for sound to stop
    while pygame.mixer.get_busy():
        if tick:
            pixels.show()
            tick = 0
            
    time.sleep(winWait)
    
    return state_reset
        
def state_team2Win():
    global win2Run
    global tick
    
    print "team2 wins"
    win2 = Image.open("ass/win/2.png").convert('RGB')
    matrix.SetImage(win2)
    pygame.mixer.stop()
    win2Sfx.play()
    
    #led fx   
    win2Run = 1
    
    while pygame.mixer.get_busy():
        if tick:
            pixels.show()
            tick = 0
        
    time.sleep(winWait)
    
    return state_reset
    
def state_lannister():
    global tieRun
    global tick

    print "tie win"
    tie = Image.open("ass/win/t.png").convert('RGB')
    matrix.SetImage(tie)
    pygame.mixer.stop()
    tieSfx.play()
    
    #led fx
    tieRun = 1
    
    while pygame.mixer.get_busy():
        if tick:
            pixels.show()
            tick = 0
        
    time.sleep(winWait)
    
    return state_reset

#===============reset game=================
def state_reset():
    global credits
    global p1_score
    global p2_score
    global p1hitWin
    global p2hitWin
    #reset all variables/flags
    
    #scores
    p1_score = 0
    p2_score = 0
    
    #max score hits
    p1hitWin = 0
    p2hitWin = 0
    
    #take yo money
    credits -= round_cost

    #make sure idle runs initially
    t = time.time() - idle_time
    
    print "game reset"
    
    return state_idle
    
#============COIN/BUTTON callbacks================
#buttons DO NOT REPEAT, btn_delay is just an
#interaction delay
def coin_insert():
    global coinRun
    global credits
    #anime LEDs keeyaaah!
    coinSfx.play()
    coinRun = 1
    print "coin inserted"
    credits += coin_each

def beam_break():
    global beamWatch
    global t2

    print "beam broke"
    if beamWatch:
       guiltSfx.play()
       beamWatch = 0
       t2 = time.time()

def start_button():
    global startPress

    if startWatch:
        startPress = 1
    else:
        badhighSfx.play()
        
    print "start prossed"
    
def p1_up():
    global p1_score
    
    print "p1 up press"
    if gameWatch:
        goodupSfx.play()
        p1_score += button_inc
    else: 
       badupSfx.play()
    
def p1_dn():
    global p1_score

    print "p1 dn press"
    if gameWatch:
        gooddnSfx.play()
        p1_score -= button_inc
    else:
       baddnSfx.play()
    
def p2_up():
    global p2_score
    
    print "p2 up press"
    if gameWatch:
        goodupSfx.play()
        p2_score += button_inc
    else:
        badupSfx.play()
    
def p2_dn():
    global p2_score
    
    print "p2 dn press"
    if gameWatch:
        gooddnSfx.play()
        p2_score -= button_inc
    else:
        baddnSfx.play()
    
#==============UTILITIES==================
def scoreCheck():
    global p1_score
    global p2_score
    global p1hitWin
    global p2hitWin
    global startWatch, startRun

    #checks for out of bounds scores, plays a berrp
    #global flags p1hitWin and p2hitWin
    #using global settings for score limits
    if (p1_score < win_score) and (p2_score < win_score):
        startWatch = 0
    
    if p1_score >= win_score:
        p1hitWin = 1
        startWatch = 1
        startRun = 1
                
    if p1_score > win_score:
        p1_score -= button_inc
        pygame.mixer.stop()
        badhighSfx.play()
        
    if p1_score < min_score:
        p1_score += button_inc
        pygame.mixer.stop()
        badhighSfx.play()
        
    if p1hitWin and (p1_score < (win_score - down_limit)):
        p1_score += button_inc
        pygame.mixer.stop()
        badlowSfx.play()

    if p2_score >= win_score:
        p2hitWin = 1
        startWatch = 1
        startRun = 1
            
    if p2_score > win_score:
        p2_score -= button_inc
        pygame.mixer.stop()
        badhighSfx.play()
        
    if p2_score < min_score:
        p2_score += button_inc
        pygame.mixer.stop()
        badhighSfx.play()
        
    if p2hitWin and (p2_score < (win_score - down_limit)):
        p2_score += button_inc
        pygame.mixer.stop()
        badlowSfx.play()
        

        
def creditScrn(newScreen):
    global idleRun
    global base
    #displays a dark credits remaining screen
    #also applies random fx from folder to fade it in
    
    #background image remains unless flagged
    if newScreen:
        location = "ass/idle/" + str(random.randint(1,len(os.listdir("ass/idle/")))) + ".png"
    
        base = Image.open(location).convert('RGBA')
        #base = Image.new("RGBA", (65, 32), (0,0,0,255))
    
    #=============Credits overlay Settings==================
    #color
    ccol = (255,255,255,255)
    
    #files
    cfont_file = "ass/font/credit.ttf"
    
    #position
    posx, posy = 1, 18
    
    #size
    cfontSize = 10
    
    #text content
    ctxt= "credits: %d/2" % credits 
    
    #shadow fade and offset
    sfade = 200
    soff = 1

    #=====Set/calc all text parameters=========
    #load font       
    cfont = ImageFont.truetype(cfont_file, cfontSize)
    
    #generate canvas and initiate draw-er
    imageTxt = Image.new("RGBA", (64, 32), (0,0,0,0))
    d = ImageDraw.Draw(imageTxt)
    
   
    #shadow
    d.text((posx-soff, posy-soff), ctxt, font=cfont, fill=(0,0,0,sfade))
    d.text((posx+soff, posy-soff), ctxt, font=cfont, fill=(0,0,0,sfade))
    d.text((posx-soff, posy+soff), ctxt, font=cfont, fill=(0,0,0,sfade))
    d.text((posx+soff, posy+soff), ctxt, font=cfont, fill=(0,0,0,sfade))
    #text
    d.text((posx,posy), ctxt, font=cfont, fill=ccol)
    
    #do the overlay, convert back to rgb
    layover = Image.alpha_composite(base, imageTxt)
      
    if newScreen:
        #fx fade in
        path = "ass/inFx/"
        folder = path + random.choice(os.listdir(path))
        #folder = path + "3"
        
        #the LebTvLive method
        filelist = []
        for thing in os.listdir(folder):
            if ".wav" in thing:
                #sound file name/location loaded up
                soundLoc = folder + "/" + thing
                effect = pygame.mixer.Sound(soundLoc)
            if ".png" in thing:
                filelist.append(int(thing.strip(".png")))
                
        filelist.sort()
        filelist = [folder + "/" + str(x) + ".png" for x in filelist]
        
        #play sound, start the LEDs
        effect.play()
        idleRun = 1
        
        for item in filelist:
            #fade in using fx folder list
            d = Image.open(item).convert('RGBA')
            layover2 = Image.alpha_composite(layover, d).convert('RGB')
            matrix.SetImage(layover2)
            time.sleep(frame_rate)
    else:
        layover2 = layover.convert('RGB')
        matrix.SetImage(layover2)

def displayScore():
    #========Team text Settings=========
    #colors
    t1col = (255,255,255,255)
    t2col = (255,255,255,255)
    
    #files
    t1font_file = "ass/font/t1.ttf"
    t2font_file = "ass/font/t2.ttf"
    
    #size
    t1fontSize = 10
    t2fontSize = 10
    
    #offset of the team names
    t1xOff = 0
    t1yOff = 0
    t2xOff = 0
    t2yOff = 0

    #text content
    t1txt= "TEAM 1"
    t2txt= "TEAM 2"

    #========Score number text Settings=========
    #colors
    n1col = (255,255,255,255)
    n2col = (255,255,255,255)
    
    #files
    n1font_file = "ass/font/n1.ttf"
    n2font_file = "ass/font/n2.ttf"
    
    #size
    n1fontSize = 40
    n2fontSize = 40
    
    #offset position
    n1xOff = 2
    n1yOff = 2
    n2xOff = 2
    n2yOff = 2
    
    #text content
    n1txt= str(p1_score)
    n2txt= str(p2_score)
    
    #=====Set/calc all text parameters=========
    #load fonts       
    t1font = ImageFont.truetype(t1font_file, t1fontSize)
    t2font = ImageFont.truetype(t2font_file, t2fontSize)
    n1font = ImageFont.truetype(n1font_file, n1fontSize)
    n2font = ImageFont.truetype(n2font_file, n2fontSize)
    
    #get object sizes
    t1w,t1h = t1font.getsize(t1txt)
    t2w,t2h = t2font.getsize(t2txt)
    n1w,n1h = n1font.getsize(n1txt)
    n2w,n2h = n2font.getsize(n2txt)
    
    #Position calculation
    t1posx, t1posy = ((32-t1w)/2) + t1xOff, t1yOff 
    t2posx, t2posy = ((32-t2w)/2) + 32 + t2xOff, t2yOff
    n1posx, n1posy = ((32-n1w)/2) + n1xOff, n1yOff
    n2posx, n2posy = ((32-n2w)/2) + 32 + n2xOff, n2yOff
    
    #========generate canvas to overlay========
    imageTxt = Image.new("RGBA", (64, 32), (0,0,0,0))   #black bckr
    d = ImageDraw.Draw(imageTxt)                        #draw instance
    
    #========generate shadow========
    #probably needs a function to reduce reptition
    
    #========generate text on the canvas========
    d.text((t1posx,t1posy), t1txt, font=t1font, fill=t1col)
    d.text((t2posx,t2posy), t2txt, font=t2font, fill=t2col)
    d.text((n1posx,n1posy), n1txt, font=n1font, fill=n1col)
    d.text((n2posx,n2posy), n2txt, font=n2font, fill=n2col)
    
    #========gradient under text========
    #canvas as (0,0,0,255)
    #text as (0,0,0,0)
    #layover = Image.alpha_composite(gradient, d)
    
    #========image overlay========
    #layover = Image.alpha_composite(layover, d).convert('RGB')
    
    #========display on screen========
    display = imageTxt.convert('RGB')
    matrix.SetImage(display) #maybe place in main loop?

def clearPix():
#sets player up/down buttons if the game is running
    for i in range(pixel_count):
        pixels.set_pixel_rgb(i, 0, 0, 0)
    if gameWatch:
        r, g, b = p1_upCol
        pixels.set_pixel_rgb(1, r, g, b)
        
        r, g, b = p1_dnCol
        pixels.set_pixel_rgb(2, r, g, b)
        
        r, g, b = p2_upCol
        pixels.set_pixel_rgb(3, r, g, b)
        
        r, g, b = p2_dnCol
        pixels.set_pixel_rgb(4, r, g, b)    
    
def loop_LED():
    #global incrementers
    global idleInc, guiltInc, coinInc, win1Inc, win2Inc, tieInc, startInc, coinInc
    #global guiltInc
    
    #global run flags
    global idleRun, win1Run, win2Run, tieRun, startRun, coinRun
    #global guiltRun
        
    #global animation flag
    global tick
    
    #if the flag is set this will iterate through frame by frame
    #and reset the flag when finished
    #multiple flags have hierarchy of what to display via re-writing
    #has to allow start fade to process in parallel
    
    change = 0
    changeLast = 0
    
    #write the pixels
    while True:
        #specific callback will handle sound
        #my incrementers were inside the pixel loops, whoops
        if gameWatch:
            clearPix()
            change = 1
        
        if idleRun:
            if idleInc > idleMax:
                idleInc = 0
                idleRun = 0
                clearPix()
            else:
                for i in range(32):
                    r, g, b = idleFx.getpixel((idleInc, i))
                    pixels.set_pixel_rgb(i, r, g, b)
                idleInc += 1
                
            change = 1
            
        #if guiltRun:
        #    pass
        
        if win1Run:
            if win1Inc > win1Max:
                win1Inc = 0
                win1Run = 0
                clearPix()
            else:
                for i in range(32):
                    r, g, b = win1Fx.getpixel((win1Inc, i))
                    pixels.set_pixel_rgb(i, r, g, b)
                win1Inc += 1
            
            change = 1
            
        if win2Run:
            if win2Inc > win2Max:
                win2Inc = 0
                win2Run = 0
                clearPix()
            else:
                for i in range(32):
                    r, g, b = win2Fx.getpixel((win2Inc, i))
                    pixels.set_pixel_rgb(i, r, g, b)
                win2Inc += 1
                
            change = 1
            
        if tieRun:
            if tieInc > tieMax:
                tieInc = 0
                tieRun = 0
                clearPix()
            else:
                for i in range(32):
                    r, g, b = tieFx.getpixel((tieInc, i))
                    pixels.set_pixel_rgb(i, r, g, b)
                tieInc += 1
                
            change = 1
            
        if coinRun:
            if coinInc > coinMax:
                coinInc = 0
                coinRun = 0
                clearPix()
            else:
                for i in range(32):
                    r, g, b = coinFx.getpixel((coinInc, i))
                    pixels.set_pixel_rgb(i, r, g, b)
                coinInc += 1
 
            change = 1
            
        if startRun: 
            if startInc > startMax:
                startInc = 0
                startRun = 0
            else:   
                for i in range (32):
                    r = startInc/2 #kinda white
                    g = startInc
                    b = startInc
                    pixels.set_pixel_rgb(0, r, g, b)
                    
                startInc += 5            
            change = 1
                   
        if change:
            tick = 1
            time.sleep(fade_rate)
            changeLast = 1
            change = 0
            while tick:
                pass
        else:
            clearPix()
            if changeLast:
                tick = 1
                time.sleep(fade_rate)
                while tick:
                    pass
                changeLast = 0

def allClear():
    
    for i in range(pixel_count):
        pixels.set_pixel_rgb(i, 0, 0, 0)
    
    pygame.mixer.fadeout(1000)
    pixels.show()
    matrix.Clear()
        
#============MAIN LOOP================ 
#state machine
state = state_boot
prevState = state_boot  

#input actions
btn_coin.when_pressed = coin_insert
btn_breakbeam.when_pressed = beam_break
btn_start.when_pressed = start_button
btn_p1up.when_pressed = p1_up
btn_p1dn.when_pressed = p1_dn
btn_p2up.when_pressed = p2_up
btn_p2dn.when_pressed = p2_dn

while state:
    try:
        if prevState != state:
            print state.__name__, "credits: %d" % credits
            prevState = state
        state=state() #state machine
    except KeyboardInterrupt:
        print "Bye"
        pixels.clear()
        pixels.show()
        pygame.mixer.quit()
        sys.exit()