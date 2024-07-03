from ppadb.client import Client
import subprocess

import cv2
import numpy as np

import pytesseract
from PIL import Image

import questionary
import time

# Screen Shot
screenshot_image   = "data//screenshot.png"

# Common
boost_icon_image         = "data//boost-icon.jpg"
energy_icon_image        = "data//energy-icon.jpg"
upgradable_booster_image = "data//upgradable-card.jpg"
confirm_button_image     = "data//confirm-button.jpg"

# Mining page
mining_page_image = "data//mining-page.jpg"
energy_level_image     = "data//energy-level.jpg"

# Card page
card_page_image  = "data//card-page.jpg"
card_section_1_image  = "data//card-section-1.jpg"
card_section_2_image  = "data//card-section-2.jpg"
card_section_3_image  = "data//card-section-3.jpg"
upgradable_card_image = "data//upgradable-card.jpg"
timer_icon_image = "data//upgradable-card.jpg"

def extract_text(image):
    text = pytesseract.image_to_string(Image.open(image), config='--psm 6')
    return text.replace(" ","")

def take_screenshot():
    with open(screenshot_image, "wb") as f:
        f.write(device.screencap())

def detect(image, threshold=0.9, time_out=4):
    initial_time = time.time()
    obj_img = cv2.imread(image, cv2.IMREAD_COLOR)
    obj_height, obj_width = obj_img.shape[:2]
    
    while True:
        take_screenshot()
        screenshot_obj = cv2.imread(screenshot_image, cv2.IMREAD_COLOR)
        result = cv2.matchTemplate(screenshot_obj, obj_img, cv2.TM_CCOEFF_NORMED)
        y_loc, x_loc = np.where(result >= threshold)
        
        rectangles = [[int(x), int(y), int(obj_width), int(obj_height)] for x, y in zip(x_loc, y_loc)]
        rectangles, _ = cv2.groupRectangles(rectangles * 2, 1, 0.7)
        
        if len(rectangles) > 0 or (time.time() - initial_time) >= time_out:
            break

    coordinates = [(int(x + w / 2), int(y + h / 2)) for x, y, w, h in rectangles]
    return coordinates

def go_to_page(page):
    if page == "mining":
        page_button = detect(mining_page_image,threshold=0.6)
    elif page == "card":
        page_button = detect(card_page_image)
    elif page == "booster":
        page_button = detect(boost_icon_image)

    if page_button:
        device.shell(f"input tap {page_button[0][0]} {page_button[0][1]}")


def setup_device():
    subprocess.run(["adb","devices"])
    adb = Client(host="127.0.0.1",port=5037)
    devices = adb.devices()
    if len(devices)!=0:
        print("Client Connection Successful")
        return devices[0]

def check_energy_level():
    energy_icon_coords = detect(energy_icon_image)
    if energy_icon_coords:
        img = cv2.imread(screenshot_image)
        cropped_img = img[energy_icon_coords[0][1]-40:energy_icon_coords[0][1]+40, energy_icon_coords[0][0]+25:energy_icon_coords[0][0]+300]
        cv2.imwrite(energy_level_image, cropped_img)

    return extract_text(energy_level_image)

def mine_coins(times):
    for i in range(times):
        device.shell(f"input tap {dw/2} {(dh/2) + dh/18}")

def upgrade_boosters():
    # check for boosters and upgrade
    upgradable_boosters = detect(upgradable_booster_image,threshold=0.95,time_out=2)
    if upgradable_boosters:
        device.shell(f"input tap {upgradable_boosters[0][0]} {upgradable_boosters[0][1]}")
        confirm_button = detect(confirm_button_image,0.6)
        if confirm_button != []:
            device.shell(f"input tap {confirm_button[0][0]} {confirm_button[0][1]}")
            detect(mining_page_image,threshold=0.6)
            upgrade_boosters()

    #check for daily boosters and use
    full_energy_booster = detect(energy_icon_image,threshold=0.6)
    if full_energy_booster:
        device.shell(f"input tap {full_energy_booster[0][0]} {full_energy_booster[0][1]}")
        confirm_button = detect(confirm_button_image,0.6,time_out=2)
        if confirm_button:
            device.shell(f"input tap {confirm_button[0][0]} {confirm_button[0][1]}")
            return True

def buy_cards():
    while True:
        # get the first upgradable card available
        card_coords = detect(upgradable_card_image,time_out=1.5)

        # buy/upgrades the card 
        if card_coords :
            device.shell(f"input tap {card_coords[0][0]} {card_coords[0][1]}")
            confirm_button = detect(confirm_button_image,0.6)
            if confirm_button != []:
                device.shell(f"input tap {confirm_button[0][0]} {confirm_button[0][1]}")
                detect(mining_page_image)
        
        # handles if it does not find card
        else:
            device.shell(f"input swipe {dw/2} {dh/2} {dw/2} {(dh/2)-(dh/3.5)} 350")
            if detect(boost_icon_image,time_out=1.5)!=[]:
                break

def coin_miner(time_limit):
    global device,dw,dh
    device = setup_device()
    dw,dh  = [int(i) for i in device.shell('wm size').split(":")[1].split("x")]
    start_time = time.time()
    print("Program Running...")
    while device:
        if (time.time() - start_time)/60 >= time_limit:
            break
        # check for energy
        go_to_page("mining")
        energy_level = check_energy_level()
        
        # Mine coins if there is sufficiant energy
        try:
            if eval(energy_level) >= 0.5 and eval(energy_level) <=1:
                no_of_times = int(int(energy_level.split("/")[0])/14)
                mine_coins(no_of_times)
        except:
            continue

        # use daily free energy 
        go_to_page("booster")
        full_energy_booster = detect(energy_icon_image,threshold=0.6)
        if full_energy_booster:
            device.shell(f"input tap {full_energy_booster[0][0]} {full_energy_booster[0][1]}")
            confirm_button = detect(confirm_button_image,0.6,time_out=2)
            if confirm_button:
                device.shell(f"input tap {confirm_button[0][0]} {confirm_button[0][1]}")
                
def hybrid_miner(time_limit):
    global device,dw,dh
    device = setup_device()
    dw,dh  = [int(i) for i in device.shell('wm size').split(":")[1].split("x")]
    start_time = time.time()
    print("Program Running...")
    while device:
        if (time.time() - start_time)/60 >= time_limit:
            break
        # check for energy
        go_to_page("mining")
        energy_level = check_energy_level()
        
        # Mine coins if there is sufficiant energy
        try:
            if eval(energy_level) >= 0.5 and eval(energy_level) <=1:
            
                no_of_times = int(int(energy_level.split("/")[0])/11)
                mine_coins(no_of_times)
        except:
            continue

        # Upgrade boosters
        go_to_page("booster")
        if upgrade_boosters():continue

        # buy and upgrade cards
        go_to_page("card")
        for card_section_img in [card_section_1_image,card_section_2_image,card_section_3_image]:
            card_section_button = detect(card_section_img)
            if card_section_button:
                device.shell(f"input tap {card_section_button[0][0]} {card_section_button[0][1]}")
                buy_cards()
       

def main():
    ch = questionary.select(
    "Select A  Mode:",
    choices=["1. Mine Coins And Also Buy","2. Mine Coins Only", "3. Exit"],
        ).ask()
    
    want_time_limit = questionary.confirm("Do You Want To Set A Time Limit: ").ask()
    time_limit = 6000
    if want_time_limit:
        time_limit = int(questionary.text("Enter Time Limit In Minutes: ").ask())

    
    if ch =="1. Mine Coins And Also Buy":
        hybrid_miner(time_limit)
    elif ch=="2. Mine Coins Only":
        coin_miner(time_limit)
    elif ch=="3. Exit":
        return


if __name__=="__main__":
    main()
    print("Program Terminated")