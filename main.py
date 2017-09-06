from PIL import Image
import cv2
import numpy as np
from operator import eq

import math
import random
import time
import pyautogui
pyautogui.FAILSAFE = True

import AT
import os

BUY_BUTTON_POS = (1275, 600)
FIRST_STAR = (541, 135)
STAR_STEP = 37

GRAY_BGR = (197, 213, 218)
BLACK = (0, 0, 0)
GREEN = (46, 129, 37)
BLUE = (53, 88, 204)
BLUE_BGR = (BLUE[2], BLUE[1], BLUE[0])
RED = (175, 43, 30)
RED_BGR = (RED[2], RED[1], RED[0])
YELLOW_BGR = (97, 255, 255)

SCREEN_RESOLUTION = pyautogui.size()
SCREEN_CENTER = (SCREEN_RESOLUTION[0] / 2, SCREEN_RESOLUTION[1] / 2)
SCROLLING_STEP = 2000
SCROLLING_SLEEP = 0.5
TRANSLATION_SLEEP = 1.5
INTERFACE_SLEEP = 1.5

AT_VERTICAL_STEP = 106 # vertical step between AT's in sidebar
AT_VERTICAL_SPACING = 150 # the list of ATs starts at this height
FRONTLINE_DANGER_ZONE = 250 # if an AT is within this radius from any RED town, we consider it to be on frontline. Distance is for 4 ticks.

QUEUE_TEMPLATE = cv2.imread('templates/Queue.png',0)
DEPLOY_TEMPLATE = cv2.imread('templates/Deploy.png',0)
RETREAT_TEMPLATE = cv2.imread('templates/Retreat.png',0)
REINFORCE_TEMPLATE = cv2.imread('templates/Reinforce.png',0)
MORALE_TEMPLATE = cv2.imread('templates/Morale.png',0)
MOVINGTO_TEMPLATE = cv2.imread('templates/Moving_to.png',0)
AT_TEMPLATES = [
    # template, name, [maxSoldiers, maxVehicles, maxMorale]
    [cv2.imread('templates/Assault_Teams/light_armor.png', 0), 'Light_Armor', [20, 16, 100]],
    [cv2.imread('templates/Assault_Teams/motorized_guard.png', 0), 'Motorized_Guard', [36, 12, 100]],
    [cv2.imread('templates/Assault_Teams/motorized_recon.png', 0), 'Motorized_Recon', [24, 24, 100]],
    [cv2.imread('templates/Assault_Teams/mechanized_recon.png', 0), 'Mechanized_Recon', [28, 14, 100]],
    [cv2.imread('templates/Assault_Teams/fighter_recon.png', 0), 'Fighter_Recon', [20, 16, 100]]
]

MAJOR_CITIES_TEMPLATES = []
directory = "templates/Major_Cities/"
files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
for file in files:
    filepath = directory + file
    cv2_template = cv2.imread(filepath, 0)
    MAJOR_CITIES_TEMPLATES.append((cv2_template, file[:-4]))

DEBUG_DIR = 'movements/'
CURRENT_ALTITUDE = -1

def die():
    print 'Make sure you\'re running H&G in 1920x1080 window, your tab is set to GLOBAL & your color scheme is RED-BLUE.'
    exit()

def get_rnd_mouse_speed():
    return random.random() + 0.5

def get_unique_screenshot_name():
    name = str(int(time.time()))
    rnd = random.randint(100, 999)
    return name + '_' + str(rnd) + '.png'

def make_screenshot(saveDirectory=None):
    """
    Makes a screenshot, returns a PIL image, saves the file in given path if saveDirectory was specified
    :param saveDirectory: if specified, must end with '/', like 'screenshots/'
    :return: returns a PIL image
    """
    screenshot = pyautogui.screenshot()
    if saveDirectory is not None:
        screenshot_name = saveDirectory + get_unique_screenshot_name(saveDirectory)
        screenshot.save(screenshot_name)
    return screenshot

def move_to_altitude(alt):
    """
    Sets the camera to be on alt ticks above the map.
    :param alt: ticks to zoom out
    :return:
    """
    pyautogui.moveTo(SCREEN_CENTER[0], SCREEN_CENTER[1], get_rnd_mouse_speed())

    global CURRENT_ALTITUDE
    if CURRENT_ALTITUDE == -1:
        # Zoom in fully
        scroll(1, 15)
        # Zoom out to reach needed altitude
        scroll(-1, alt)
        CURRENT_ALTITUDE = alt
    else:
        while alt > CURRENT_ALTITUDE:
            scroll(-1, 1)
            CURRENT_ALTITUDE += 1
        while alt < CURRENT_ALTITUDE:
            scroll(1, 1)
            CURRENT_ALTITUDE -= 1


def scroll(direction=1, ticks=1, delay=0):
    """
    Rotates mouse wheel.
    :param direction: 1 or -1
    :param ticks: how many wheel ticks to do
    :param delay: delay before the first tick
    :return: nothing
    """
    time.sleep(delay)
    for i in xrange(ticks):
        pyautogui.scroll(direction * SCROLLING_STEP)
        time.sleep(SCROLLING_SLEEP)

def move_screen_to_city(cityNumber):
    """
    Performs a mouse click on a given city.
    :param cityNumber: the city we want to click on
    :return: nothing
    """
    x, y = get_city_pos(cityNumber)
    pyautogui.moveTo(x, y, get_rnd_mouse_speed())
    pyautogui.click(x, y)
    pyautogui.moveTo(SCREEN_CENTER[0], SCREEN_CENTER[1], get_rnd_mouse_speed())
    time.sleep(0.5)
    scroll(-1, 2)  # to compensate zooming out
    time.sleep(0.5)

def convert_CV2ToPIL(cv2_image, conversionType=cv2.COLOR_BGR2RGB):
    return Image.fromarray(cv2.cvtColor(cv2_image, conversionType))

def convert_PILToCV2(PIL_image, conversionType=cv2.COLOR_RGB2BGR):
    return cv2.cvtColor(np.array(PIL_image), conversionType)

def count_major_cities(PIL_image=None):
    """
    Makes a screenshot and then counts how many main cities are controlled by BLUE faction.
    :param PIL_image: if specified, uses this screenshot instead
    :return: number of cities found
    """
    if PIL_image is None:
        PIL_image = make_screenshot()
    x, y = FIRST_STAR
    RGB = PIL_image.getpixel((x, y))
    length = 0
    #cv2_image = convert_PILToCV2(PIL_image)
    while any(map(eq, RGB, BLUE)):
        length += 1
        x += STAR_STEP
        RGB = PIL_image.getpixel((x, y))
        # cv2.line(cv2_image, (x, y), (x, y), (0, 0, 255), 4)
    #cv2.imshow('', cv2_image)
    return length


def get_mask(color, cv2_image, range=80):
    """
    Converts a BGR image into black and white mask with white color representing specified color.
    :param color: this color will become white on the mask
    :param cv2_image: the base BGR image
    :param range: number defining the strictness of the color picking
    :return: black and white CV2 image
    """
    # Calculating upper and lower shades
    lower_color = np.array([color[0] - range, color[1] - range, color[2] - range])
    upper_color = np.array([color[0] + range / 3, color[1] + range / 3, color[2] + range / 3])
    # Threshold the HSV image to get only key colors
    mask = cv2.inRange(cv2_image, lower_color, upper_color)
    return mask

def distance(pos1, pos2):
    x1, y1 = pos1
    x2, y2 = pos2
    return math.hypot(math.fabs(x1 - x2), math.fabs(y1 - y2))

def find_battles_on_screen(debug=False):
    """
    Makes two screenshots with 1.5s interval, merges their masks to compensate glowing and then returns the array of found circles, or None. We anticipate every circle to represent a battle, but false positives are possible.
    :return: numpy array of circles with elements (circle_center_x, circle_center_y, radius)
    """
    # Making first screenshot
    PIL_image_1 = make_screenshot()
    time.sleep(1.5)
    # Making second screenshot
    PIL_image_2 = make_screenshot()

    # Getting masks
    cv2_image_1 = convert_PILToCV2(PIL_image_1)
    cv2_image_2 = convert_PILToCV2(PIL_image_2)
    mask_1 = get_mask(YELLOW_BGR, cv2_image_1)
    mask_2 = get_mask(YELLOW_BGR, cv2_image_2)

    # Merging masks to compensate glowing
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.add(mask_1, mask_2)

    # Connecting rings into one circle via Dilation followed by Erosion
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    # mask = cv2.medianBlur(mask, 7)

    # Finding circles aka battles
    circles = cv2.HoughCircles(mask, cv2.HOUGH_GRADIENT, 1, 14, param1=20, param2=9, minRadius=7, maxRadius=11)
    if circles is not None:
        circles = np.uint16(np.around(circles))
        if debug:
            cv2_image = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
            for i in circles[0, :]:
                cv2.circle(cv2_image, (i[0], i[1]), i[2], (0, 255, 0), 2)
                cv2.circle(cv2_image, (i[0], i[1]), 2, (0, 0, 255), 3)
            cv2.circle(cv2_image, SCREEN_CENTER, 2, (255, 150, 150), 2)
            cv2.imwrite(DEBUG_DIR + get_unique_screenshot_name(), cv2_image)

    return circles

def find_frontline_city(countOfControlledCities=None):
    """
    Returns the city closest to the frontline, battle's coordinates and distance from the city to that battle.
    :param countOfControlledCities: integer, how many cities we have captured
    :return: None, or array (city, (battle's X and Y while given city is in the center of the screen), distance between these two places)
    """
    city = None
    if countOfControlledCities is None:
        countOfControlledCities = count_major_cities()
    for k in xrange(countOfControlledCities):
        move_screen_to_city(k)
        cur_city_pos = SCREEN_CENTER
        battles = find_battles_on_screen(debug=True)
        if battles is not None:
            for i in battles[0, :]:
                x, y, r = (i[0], i[1], i[2])
                if city is None:
                    city = (k, (x, y), distance(cur_city_pos, (x,y)))
                else:
                    if distance(cur_city_pos, (x,y)) < city[2]:
                        city = (k, (x, y), distance(cur_city_pos, (x, y)))
    return city

def is_AT_panel_opened(PIL_image=None):
    """
    Searches for morale icon, then decides whether AT panel is opened or not based on its location.
    :param PIL_image: if provided, an image to search in. If None, a new screenshot will be made
    :return: boolean
    """
    if PIL_image is None:
        PIL_image = make_screenshot()

    cv2_gray = convert_PILToCV2(PIL_image, cv2.COLOR_RGB2GRAY)

    w, h = MORALE_TEMPLATE.shape[::-1]
    res = cv2.matchTemplate(cv2_gray, MORALE_TEMPLATE, cv2.TM_CCOEFF)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    top_left = max_loc
    #bottom_right = (top_left[0] + w, top_left[1] + h)
    #cv2.rectangle(cv2_grayImage, top_left, bottom_right, 255, 2)

    # 1531 is unfolded morale (with scrollbar)
    # 1729 is folded morale (with scrollbar)
    if top_left[0] > 1700:
        return True
    return False

def toggle_AT_panel(action, PIL_image=None):
    isOpen = is_AT_panel_opened(PIL_image)
    if isOpen & (action == 'open'):
        return
    if not isOpen & (action == 'close'):
        return
    if action == 'open':
        pyautogui.click(1505, 173)
        print 'Opening AT panel...'
    if action=='close':
        pyautogui.click(1698, 173)
        print 'Closing AT panel...'
    time.sleep(1.5)

def template_on_image(cv2_gray, template, threshold, debug=False):
    w, h = template.shape[::-1]
    res = cv2.matchTemplate(cv2_gray, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

    if debug:
        cv2.rectangle(cv2_gray, max_loc, (max_loc[0] + w, max_loc[1] + h), 255, 2)
        cv2.putText(cv2_gray, '%s' % max_val, max_loc, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 255, 1)
        cv2.imwrite(DEBUG_DIR + get_unique_screenshot_name(), cv2_gray)

    if max_val > threshold:
        return True
    else:
        return False

def get_cropped(cv2_image, box):
    """
    :param cv2_image: cv2 image containing captcha
    :param box: an array [top_left_point, bottom_right_point]
    :return: cropped cv2 image
    """
    x1 = box[0][0]
    x2 = box[1][0]
    y1 = box[0][1]
    y2 = box[1][1]
    cv2_cropped = cv2_image[y1:y2, x1:x2]
    return cv2_cropped

def parse_team_status(PIL_image, top_left, maxStats):

    maxSoldiers, maxVehicles, maxMorale = maxStats

    vehicles_bar_pos = (top_left[0] + 95, top_left[1] + 19)
    soldiers_bar_pos = (vehicles_bar_pos[0], vehicles_bar_pos[1] + 22)
    morale_bar_pos = (vehicles_bar_pos[0] - 75, vehicles_bar_pos[1] - 28)
    bar_width = 50

    # Counting the length of the vehicles bar
    length = count_bar_pixels(PIL_image, GREEN, vehicles_bar_pos)
    vehicle_bar_status = length / float(bar_width) * maxVehicles

    # Counting the length of the soldiers bar
    length = count_bar_pixels(PIL_image, GREEN, soldiers_bar_pos)
    soldiers_bar_status = length / float(bar_width) * maxSoldiers

    # Counting the length of the morale bar
    morale_bar_width = 42
    length = count_bar_pixels(PIL_image, GREEN, morale_bar_pos)
    morale_bar_status = length / float(morale_bar_width) * maxMorale

    # Check if the AT is currently in queue
    # Cropping AT sheet
    bottom_right = (SCREEN_RESOLUTION[0], top_left[1] + 50)
    cv2_gray = convert_PILToCV2(PIL_image, cv2.COLOR_RGB2GRAY)
    cv2_gray = get_cropped(cv2_gray, box=((top_left[0], top_left[1] - 25), bottom_right))

    inQueue = template_on_image(cv2_gray, QUEUE_TEMPLATE, 0.85, debug=False)
    canBeDeployed = template_on_image(cv2_gray, DEPLOY_TEMPLATE, 0.85, debug=False)
    isInBattle = template_on_image(cv2_gray, RETREAT_TEMPLATE, 0.85, debug=False)
    isMoving = template_on_image(cv2_gray, MOVINGTO_TEMPLATE, 0.85, debug=False)
    canBeReinforced = template_on_image(cv2_gray, REINFORCE_TEMPLATE, 0.85, debug=False)

    #cv2_image = convert_PILToCV2(PIL_image)
    #cv2.line(cv2_image, vehicles_bar_pos, soldiers_bar_pos, (0,0,255))
    #cv2.imshow(name, cv2_image)
    curStats = (soldiers_bar_status, vehicle_bar_status, morale_bar_status, inQueue, canBeDeployed, isMoving, canBeReinforced, isInBattle)

    return curStats

def get_teams(PIL_image, debug=False):
    """
    Analyzes sidebar panel and returns an array of all available teams.
    :param cv2_gray: if provided, searches in the image instead, otherwise makes a new screenshot
    :param debug: boolean, if true, shows an image with highlighted ATs and their type
    :return: an array of assault teams with [name, XY, [0, 0, 0], [maxsoldiers, maxvehicles, maxmorale]] elements
    """
    cv2_gray = convert_PILToCV2(PIL_image, cv2.COLOR_RGB2GRAY)

    # Preallocating memory for our Assault Teams
    teams = []

    for elem in AT_TEMPLATES:
        template, name, maxStats = elem

        w, h = template.shape[::-1]
        res = cv2.matchTemplate(cv2_gray, template, cv2.TM_CCOEFF_NORMED)
        threshold = 0.9
        loc = np.where(res >= threshold)
        for pt in zip(*loc[::-1]):
            # First we need to check if there is any other team placed at these coordinates
            # In order to do that, we calculate the minimum distance between pt and locations of teams we found before
            mindist = 1000
            for t in teams:
                d = distance(pt, t.getPos())
                if d < mindist: mindist = d
                # multiple recognition of the same template in the small area usually fall on the next pixels, so 5px is enough to rule that out
            if mindist < 5:
                continue
            # If pt is far enough from teams we've already counted, it must be an uncounted team
            # Therefore we should add this team in the list of teams
            status = parse_team_status(PIL_image, pt, maxStats)
            team = AT.AssaultTeam(name, pt, maxStats)
            team.setStatus(status)
            teams.append(team)
            if debug:
                cv2.rectangle(cv2_gray, pt, (pt[0] + w, pt[1] + h), 255, 2)
                cv2.putText(cv2_gray, '%s' % name, (pt[0], pt[1]), cv2.FONT_HERSHEY_SIMPLEX, 1, 255, 1)

    if debug:
        cv2.imshow('AT sidebar analysis', cv2_gray)

    return teams

def count_bar_pixels(PIL_image, color, point):
    """
    Counts the number of pixels that match given color in the bar at given coordinates.
    :param PIL_image: image to count pixels on
    :param point: array [x, y] of coordinates of the point to start counting at
    :return: number of matching pixels
    """
    x, y = point
    col = PIL_image.getpixel((x, y))
    length = 0
    while any(map(eq, col, color)):
        length += 1
        col = PIL_image.getpixel((x + length, y))
    return length

def get_city_pos(city):
    x, y = FIRST_STAR
    x += STAR_STEP * city
    return (x, y)

def get_city_name(city):
    x, y = get_city_pos(city)
    pyautogui.moveTo(x, y, get_rnd_mouse_speed())
    time.sleep(INTERFACE_SLEEP)
    x, y = FIRST_STAR
    screencap = make_screenshot()
    cv2_gray = convert_PILToCV2(screencap, cv2.COLOR_RGB2GRAY)
    cv2_gray = get_cropped(cv2_gray, box=((x, y), (x + STAR_STEP * 5, y + STAR_STEP * 3)))
    for mct in MAJOR_CITIES_TEMPLATES:
        t, name = mct
        if template_on_image(cv2_gray, t, 0.9):
            return name
    return 'Unknown'


def move_team_to(team, pos):
    x, y = team.getPos()
    pyautogui.moveTo(x, y, get_rnd_mouse_speed())
    # pyautogui.dragTo(pos, 1)

    pyautogui.mouseDown(team.getPos())
    pyautogui.moveTo(pos[0], pos[1], 2)
    pyautogui.mouseUp(pos)

def find_closest_circle(pos, circles):
    closestCircle = None
    if circles is not None:
        for town in circles[0, :]:
            x, y, r = town
            d = distance((x, y), pos)
            if closestCircle is None:
                closestCircle = (d, (x, y))
            else:
                if d < closestCircle[0]:
                    closestCircle = (d, (x, y))
    return closestCircle

def move_screen_to_team(team):
    x, y = team.getPos()
    pyautogui.click(x, y)
    time.sleep(INTERFACE_SLEEP)
    pyautogui.doubleClick(x, y, 0.3)
    time.sleep(TRANSLATION_SLEEP)

def get_position_sitrep(debug=False):
    screencap = make_screenshot()
    cv2_image = convert_PILToCV2(screencap)
    cv2_mask_gray = get_mask(GRAY_BGR, cv2_image, range=10)
    # Assault Teams of both sides are colored in gray, and ATs often stationed in cities
    # to avoid black rectangles in cities we have to add this color to both BLUE and RED masks

    # 1. Getting mask with RED towns
    cv2_mask_red = get_mask(RED_BGR, cv2_image, range=50)
    cv2_mask_rg = cv2.add(cv2_mask_red, cv2_mask_gray)

    # 2. Finding RED towns
    cv2_mask_rg = cv2.medianBlur(cv2_mask_rg, 7)
    red_towns = cv2.HoughCircles(cv2_mask_rg, cv2.HOUGH_GRADIENT, 1, 20, param1=20, param2=9, minRadius=11, maxRadius=15)
    if red_towns is not None:
        red_towns = np.uint16(np.around(red_towns))

    # 3. Getting mask with BLUE towns
    cv2_mask_blue = get_mask(BLUE_BGR, cv2_image, range=80)
    cv2_mask_bg = cv2.add(cv2_mask_blue, cv2_mask_gray)

    # 3. Drawing black circles with centers in RED towns over blue mask
    if red_towns is not None:
        for town in red_towns[0, :]:
            x, y, r = town
            cv2.circle(cv2_mask_bg, (x, y), FRONTLINE_DANGER_ZONE, 0, -2)

    # 4. Finding remaining BLUE towns
    cv2_mask = cv2.medianBlur(cv2_mask_bg, 7)
    blue_towns = cv2.HoughCircles(cv2_mask, cv2.HOUGH_GRADIENT, 1, 20, param1=20, param2=9, minRadius=11, maxRadius=15)
    if blue_towns is not None:
        blue_towns = np.uint16(np.around(blue_towns))

    # 5. Finding the closest BLUE town and checking if AT is already in there
    isInSafeTown = False
    closestBlueTown = find_closest_circle(SCREEN_CENTER, blue_towns)

    # 6. Checking if we are already in that town
    if closestBlueTown is not None:
        if closestBlueTown[0] < 10:
            isInSafeTown = True

    if debug:
        if red_towns is not None:
            # Adding FRONTLINE_DANGER_ZONE areas
            for town in red_towns[0, :]:
                x, y, r = town
                cv2.circle(cv2_image, (x, y), FRONTLINE_DANGER_ZONE, (100, 100, 255), 2)
            # Adding RED towns
            for town in red_towns[0, :]:
                x, y, r = town
                cv2.circle(cv2_image, (x, y), r, (0, 0, 255), -1)
        if blue_towns is not None:
            # Adding green circles on safe towns
            for i in blue_towns[0, :]:
                cv2.circle(cv2_image, (i[0], i[1]), i[2], (0, 255, 0), 2)
                cv2.circle(cv2_image, (i[0], i[1]), 2, (0, 0, 255), 3)
        cv2.imwrite(DEBUG_DIR + get_unique_screenshot_name(), cv2_image)

    return isInSafeTown, closestBlueTown

def get_loc_time():
    return time.strftime('%c', time.localtime(int(time.time())))

def simulate_activity(teams):
    # Moving camera to a random city
    count = count_major_cities()
    if count == 0:
        die()
    move_screen_to_city(random.choice(xrange(count)))
    return

def get_towns_to_deploy(debug=False):
    screencap = make_screenshot()
    cv2_image = convert_PILToCV2(screencap)
    #cv2_image = get_cropped(cv2_image, box=((510, 380), (1405, 750)))
    mask = get_mask(BLUE_BGR, cv2_image)
    # Dilation followed by Erosion
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    circles = cv2.HoughCircles(mask, cv2.HOUGH_GRADIENT, 1, 40, param1=20, param2=9, minRadius=18, maxRadius=20)
    if circles is not None:
        circles = np.uint16(np.around(circles))
        if debug:
            cv2_image = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
            for i in circles[0, :]:
                cv2.circle(cv2_image, (i[0], i[1]), i[2], (0, 255, 0), 2)
                cv2.circle(cv2_image, (i[0], i[1]), 2, (0, 0, 255), 3)
            cv2.imwrite(DEBUG_DIR + get_unique_screenshot_name(), cv2_image)

    return circles

def manage_team(team):
    """
    Makes a decision what to do with given assault team: deploy, send to attack, send to retreat, nothing
    :param team:
    :return: nothing
    """

    if team.canBeDeployed():
        print '%s %s can be deployed, trying to deploy...' % (get_loc_time(), team.getName())
        #return # a temporal plug because deployment is not ready

        # START
        # Deploy the team in the frontline city
        #print '%s Deploying %s...' % (get_loc_time(), team.getName())
        # Findind city closest to the frontline
        #count = count_major_cities()
        #if count == 0:
        #    print 'Failed to find main cities on the screen.'
        #    die()
        #print 'At this moment our faction controls %d main cities...' % count
        #move_to_altitude(7)
        #cityID, battlePos, distanceToBattle = find_frontline_city(count)
        #cityName = get_city_name(cityID)
        #print 'The closest battle is next to %s, next deploy will be there...' % cityName
        # END

        # Buying troops
        toggle_AT_panel('open')
        x, y = team.getIconPos()

        pyautogui.moveTo(x, y, get_rnd_mouse_speed())
        pyautogui.click()
        time.sleep(INTERFACE_SLEEP)

        pyautogui.moveTo(BUY_BUTTON_POS[0], BUY_BUTTON_POS[1], get_rnd_mouse_speed())
        pyautogui.click(BUY_BUTTON_POS)
        time.sleep(INTERFACE_SLEEP)

        deploy_points = get_towns_to_deploy(debug=False)
        if deploy_points is None:
            print 'Couldn\'t find any towns in the list of towns to deploy, but that list can\'t be empty!'
            die()
        circle = random.choice(deploy_points)
        x, y, r = circle[0, :]
        pyautogui.moveTo(x, y, get_rnd_mouse_speed())
        pyautogui.click(x, y)

        print '%s %s was deployed in random city and now stands in queue.' % (get_loc_time(), team.getName())

        return

    if team.isKIA() | team.isInQueue() | team.isMoving() | team.isInBattle():
        return

    # Team is deployed, not in battle, not in queue
    move_to_altitude(4)
    move_screen_to_team(team)

    isInSafeTown, safeTown = get_position_sitrep(debug=True)
    if safeTown is not None:
        safeTownDistance, safeTownPos = safeTown

    if team.needsRest() | team.needsReinforcements():
        if isInSafeTown:
            if team.needsRest():
                # If team needs rest, we will reinforce it even if it has only minor casualties
                if team.canBeReinforced():
                    # Reinforce the team
                    print '%s %s needs rest, meanwhile we will reinforce it. Putting it in reinforcements queue.' % (get_loc_time(), team.getName())
                    toggle_AT_panel('open')
                    pyautogui.click(team.getIconPos())
                    time.sleep(INTERFACE_SLEEP)
                    pyautogui.click(BUY_BUTTON_POS)
                else:
                    print '%s %s is fully reinforced and resting in safe place.' % (get_loc_time(), team.getName())
                    return
            else:
                # If rest is not needed, but team is in need of reinforcements
                if team.needsReinforcements():
                    if team.canBeReinforced():
                        # Reinforce the team
                        print '%s Putting %s in queue for reinforcements.' % (get_loc_time(), team.getName())
                        toggle_AT_panel('open')
                        pyautogui.click(team.getIconPos())
                        time.sleep(INTERFACE_SLEEP)
                        pyautogui.click(BUY_BUTTON_POS)
                    else:
                        print '%s Team %s waiting for reinforcements to reach it.' % (get_loc_time(), team.getName())
                    return

            # old
            #if team.needsReinforcements():
            #    if team.canBeReinforced():
            #        # Reinforce the team!
            #        print '%s Putting %s in queue for reinforcements.' % (get_loc_time(), team.getName())
            #        toggle_AT_panel('open')
            #        pyautogui.click(team.getIconPos())
            #        time.sleep(INTERFACE_SLEEP)
            #        pyautogui.click(BUY_BUTTON_POS)
            #        return
            #    else:
            #        # Reinforcements are en route
            #        print '%s Team %s waiting for reinforcements to reach it.' % (get_loc_time(), team.getName())
            #        return
            #else:
            #    # The team is tired. Resting!
            #    print '%s %s is resting in safe place.' % (get_loc_time(), team.getName())
            #    return
        else:
            # Send team away from the frontline
            if safeTown is None:
                print '%s Can\'t send %s away from the frontline. No safe towns around.' % (get_loc_time(), team.getName())
                # TODO this is a potential loop here. Assault team will stand still until the town is found.
            else:
                print '%s Sending %s away from the frontline.' % (get_loc_time(), team.getName())

                # Debug snippet
                screencap = make_screenshot()
                cv2_image = convert_PILToCV2(screencap)
                cv2.arrowedLine(cv2_image, SCREEN_CENTER, safeTownPos, (0,255,0), 2)
                cv2.putText(cv2_image, '%s retreats' % team.getName(), SCREEN_CENTER, cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.imwrite(DEBUG_DIR + get_unique_screenshot_name(), cv2_image)
                # Debug snipped end

                move_team_to(team, safeTownPos)
            return

    # According to team's thresholds, team's status is OK.
    if team.isReady():
        print '%s %s still can fight alright, trying to send it in battle...' % (get_loc_time(), team.getName())
        # Looking for battles nearby
        move_to_altitude(7)
        battles = find_battles_on_screen(debug=True)
        if battles is None:
            print 'No battles around :('
            # TODO this a potential loop here. Assault team will stand still until the battle appears nearby.
        else:
            # Sending team to the battlefield
            battleDist, battlePos = find_closest_circle(SCREEN_CENTER, battles)

            # Debug snippet
            screencap = make_screenshot()
            cv2_image = convert_PILToCV2(screencap)
            cv2.arrowedLine(cv2_image, SCREEN_CENTER, battlePos, (0, 255, 0), 2)
            cv2.putText(cv2_image, '%s attacks' % team.getName(), SCREEN_CENTER, cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
            cv2.imwrite(DEBUG_DIR + get_unique_screenshot_name(), cv2_image)
            # Debug snipped end

            move_team_to(team, battlePos)

        return


def main():
    #try:
    time.sleep(3)
    #find_battles_on_screen(debug=True)
    #get_towns_to_deploy(debug=True)
    #exit()
    while True:
        # Open AT panel if it's closed
        if not is_AT_panel_opened:
            toggle_AT_panel(action='open')

        screencap = make_screenshot()

        teams = get_teams(screencap, debug=False)
        if teams.__len__() == 0:
            print 'No assault teams found, nothing to deploy.'
            die()

        # Managing ATs
        move_to_altitude(4)
        for team in teams:
            manage_team(team)

        time.sleep(10 + random.randrange(0, 5))
        simulate_activity(teams)
        time.sleep(5 + random.randrange(5, 10))

    #except BaseException:
    #    print BaseException
        # Showing desktop screen in case we got an exception
        #pyautogui.click(SCREEN_RESOLUTION)
        # The idea is: seeing desktop instead of game window
        # after you came back from being AFK will immediately
        # tell you that Octavia is not working anymore


if __name__ == "__main__":
    main()