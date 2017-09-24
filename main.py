from PIL import Image
import cv2
import numpy as np
from operator import eq

import math
import random
import time
import pyautogui
pyautogui.FAILSAFE = False

import AT
import os

# button we press to confirm buying or AT reinforcing
BUY_BUTTON_POS = (1275, 600)
# position of the arrow that opens the AT panel
OPEN_PANEL_POS = (1698, 173)
# position of the arrow that closes the AT panel
CLOSE_PANEL_POS = (1505, 173)
# position of 'Close' button in the battle view
CLOSE_POS = (658, 794)
# position of 'No, Thanks' button in AT deployment menu
NO_THANKS_POS = (960, 790)
# position of the first blue star on the top of the screen
FIRST_STAR = (541, 135)
# step between blue stars, used to count how many cities we control
STAR_STEP = 37

# colors
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
SCROLLING_STEP = 2000 # do not change
SCROLLING_SLEEP = 2 # seconds to wait between mouse wheel scrolls
TRANSLATION_SLEEP = 2.5 # seconds to wait after teleporting to somewhere
INTERFACE_SLEEP = 2 # seconds to wait after UI interactions

# if an AT is within this radius from any RED town, we consider it to be on frontline
# send debug=True into get_position_sitrep() to see these circles on screenshots in DEBUG_DIR
FRONTLINE_DANGER_ZONE = 250

# directory where we store debug information
DEBUG_DIR = 'D:/Diana/'
# directory with templates
TEMPLATES_DIR = 'data/templates/'

QUEUE_TEMPLATE = cv2.imread(TEMPLATES_DIR + 'Queue.png',0)
DEPLOY_TEMPLATE = cv2.imread(TEMPLATES_DIR + 'Deploy.png',0)
RETREAT_TEMPLATE = cv2.imread(TEMPLATES_DIR + 'Retreat.png',0)
REINFORCE_TEMPLATE = cv2.imread(TEMPLATES_DIR + 'Reinforce.png',0)
MORALE_TEMPLATE = cv2.imread(TEMPLATES_DIR + 'Morale.png',0)
MOVINGTO_TEMPLATE = cv2.imread(TEMPLATES_DIR + 'Moving_to.png',0)

AT_TEMPLATES = [
    # template, type, [maxSoldiers, maxVehicles, maxMorale]
    # Reinforcements must have last parameter set to [0,0,0] or they'll be treated as usual ATs
    [cv2.imread(TEMPLATES_DIR + 'Assault_Teams/infantry.png', 0), 'Infantry_Reinforcement', [0, 0, 0]],
    [cv2.imread(TEMPLATES_DIR + 'Assault_Teams/motorcycles.png', 0), 'Vehicle_Reinforcement', [0, 0, 0]],
    #[cv2.imread(TEMPLATES_DIR + 'Assault_Teams/light_armor.png', 0), 'Light_Armor', [20, 16, 100]],
    [cv2.imread(TEMPLATES_DIR + 'Assault_Teams/motorized_guard.png', 0), 'Motorized_Guard', [36, 12, 100]],
    [cv2.imread(TEMPLATES_DIR + 'Assault_Teams/guard.png', 0), 'Guard', [36, 0, 100]],
    #[cv2.imread(TEMPLATES_DIR + 'Assault_Teams/motorized_recon.png', 0), 'Motorized_Recon', [24, 24, 100]],
    #[cv2.imread(TEMPLATES_DIR + 'Assault_Teams/mechanized_recon.png', 0), 'Mechanized_Recon', [28, 14, 100]],
    #[cv2.imread(TEMPLATES_DIR + 'Assault_Teams/fighter_recon.png', 0), 'Fighter_Recon', [20, 16, 100]]
]

MAJOR_CITIES_TEMPLATES = []
directory = TEMPLATES_DIR + 'Major_Cities/'
files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
for file in files:
    filepath = directory + file
    cv2_template = cv2.imread(filepath, 0)
    MAJOR_CITIES_TEMPLATES.append((cv2_template, file[:-4]))

# used as flag to detect if the program was run the first time and altitude calibration has not been made
CURRENT_ALTITUDE = -1

# how many unsuccessful actions are needed before we recalibrate altitude
FAILED_ATTEMPTS = 0
FAILED_ATTEMPTS_LIM = 3

# array used to store assault teams and reinforcements
TEAMS = []

########################################################################################################################

def die():
    print 'Make sure you\'re running H&G in 1920x1080 window, your tab is set to GLOBAL & your color scheme is RED-BLUE.'
    print 'A screenshot was made to capture the moment of this exit.'
    make_screenshot(DEBUG_DIR)
    exit()

########################################################################################################################

def get_rnd_mouse_speed():
    return random.random() + 0.5

########################################################################################################################

def get_unique_screenshot_name():
    name = str(int(time.time()))
    rnd = random.randint(100, 999)
    return name + '_' + str(rnd) + '.png'

########################################################################################################################

def make_screenshot(saveDirectory=None):
    """
    Makes a screenshot, returns a PIL image, saves the file on drive at given path if saveDirectory was specified
    :param saveDirectory: if specified, must end with '/', like 'screenshots/'
    :return: returns a PIL image
    """
    screenshot = pyautogui.screenshot()
    if saveDirectory is not None:
        screenshot_name = saveDirectory + get_unique_screenshot_name()
        screenshot.save(screenshot_name)
    return screenshot

########################################################################################################################

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

########################################################################################################################

def scroll(direction, ticks=1):
    """
    Rotates mouse wheel.
    :param direction: 1 or -1
    :param ticks: how many wheel ticks to do
    :param delay: delay before the first tick
    :return: nothing
    """
    for i in xrange(ticks):
        pyautogui.scroll(direction * SCROLLING_STEP)
        time.sleep(SCROLLING_SLEEP)

########################################################################################################################

def move_screen_to_city(cityNumber):
    """
    Performs a mouse click on a given city.
    :param cityNumber: the city we want to click on
    :return: nothing
    """
    pyautogui.click(get_city_pos(cityNumber), duration=get_rnd_mouse_speed())
    pyautogui.moveTo(SCREEN_CENTER[0], SCREEN_CENTER[1], get_rnd_mouse_speed())
    time.sleep(0.5)
    scroll(-1, 1)  # to compensate zooming in
    time.sleep(0.5)

########################################################################################################################

def convert_CV2ToPIL(cv2_image, conversionType=cv2.COLOR_BGR2RGB):
    return Image.fromarray(cv2.cvtColor(cv2_image, conversionType))

########################################################################################################################

def convert_PILToCV2(PIL_image, conversionType=cv2.COLOR_RGB2BGR):
    return cv2.cvtColor(np.array(PIL_image), conversionType)

########################################################################################################################

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

########################################################################################################################

def get_mask(color, cv2_image, range=80):
    """
    Converts a BGR image into black and white mask with white color representing specified color.
    :param color: this color will become white on the mask
    :param cv2_image: the base BGR image
    :param range: number defining the strictness of the color picking, 0 means extract the exact color
    :return: black and white CV2 image
    """
    # Calculating upper and lower shades
    lower_color = np.array([color[0] - range, color[1] - range, color[2] - range])
    upper_color = np.array([color[0] + range / 3, color[1] + range / 3, color[2] + range / 3])
    # Threshold the HSV image to get only key colors
    mask = cv2.inRange(cv2_image, lower_color, upper_color)
    return mask

########################################################################################################################

def distance(pos1, pos2):
    """
    Returns the distance between two 2D points.
    :return: distance between points
    """
    x1, y1 = pos1
    x2, y2 = pos2
    return math.hypot(math.fabs(x1 - x2), math.fabs(y1 - y2))

########################################################################################################################

def find_battles_on_screen(debug=False):
    """
    Makes two screenshots with 1.5s interval, merges their masks to compensate glowing and then returns the array of
    found circles, or None. We anticipate every circle to represent a battle, but false positives are possible.
    :return: numpy array of circles with elements (circle_center_x, circle_center_y, radius)
    """

    # This function was calibrated for altitude level 7
    move_to_altitude(7)

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
    mask = cv2.add(mask_1, mask_2)

    # Patching up holes left by gray AT rectangles
    patch = get_mask(GRAY_BGR, cv2_image_1, range=10)
    mask = cv2.add(mask, patch)

    # Connecting rings into one circle via Dilation followed by Erosion
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    # mask = cv2.medianBlur(mask, 7)

    # Excluding interface from the picture by coloring specific areas of the screen into black
    # Excluding major towns and some of the interface on top
    upper_left = (0, 0)
    bottom_right = (SCREEN_RESOLUTION[0], 180)
    cv2.rectangle(mask, upper_left, bottom_right, 0, -1)
    # Excluding AT panel
    upper_left = (1542, 149)
    bottom_right = (SCREEN_RESOLUTION[0], 150 + TEAMS.__len__() * 100)
    cv2.rectangle(mask, upper_left, bottom_right, 0, -1)

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

########################################################################################################################

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
        battles = find_battles_on_screen(debug=False)
        if battles is not None:
            for i in battles[0, :]:
                x, y, r = (i[0], i[1], i[2])
                if city is None:
                    city = (k, (x, y), distance(cur_city_pos, (x,y)))
                else:
                    if distance(cur_city_pos, (x,y)) < city[2]:
                        city = (k, (x, y), distance(cur_city_pos, (x, y)))
    return city

########################################################################################################################

def is_panel_opened(PIL_image=None, debug=False):
    """
    Searches for morale icon, then decides whether AT panel is opened or not based on its location.
    :param PIL_image: if provided, an image to search in. If None, a new screenshot will be made
    :return: boolean
    """
    if PIL_image is None:
        PIL_image = make_screenshot()

    cv2_gray = convert_PILToCV2(PIL_image, cv2.COLOR_RGB2GRAY)
    cv2_gray = get_cropped(cv2_gray, box=((1480, 140), (SCREEN_RESOLUTION[0], 200)))

    w, h = MORALE_TEMPLATE.shape[::-1]
    res = cv2.matchTemplate(cv2_gray, MORALE_TEMPLATE, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    top_left = max_loc

    if debug:
        bottom_right = (top_left[0] + w, top_left[1] + h)
        cv2.rectangle(cv2_gray, top_left, bottom_right, 255, 2)
        cv2.putText(cv2_gray, '%s' % max_val, max_loc, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 255, 1)
        cv2.imwrite(DEBUG_DIR + get_unique_screenshot_name(), cv2_gray)

    # if the icon in the left half of the cropped image, the panel is opened
    w, h = cv2_gray.shape[::-1]
    if top_left[0] < w / 2:
        return True
    return False

########################################################################################################################

def toggle_panel(action, PIL_image=None, debug=False):
    """
    Toggles the AT panel on the right side of the screen.
    :param action: either 'open' or 'close'
    :param PIL_image: if provided, a screenshot used to find out whether the panel already opened or not
    :param debug: True to create debug screenshots
    :return:
    """
    isOpen = is_panel_opened(PIL_image, debug)
    isClosed = not isOpen
    action = action.lower()

    if (isOpen & (action == 'open')) | (isClosed & (action == 'close')):
        return
    if isClosed & (action == 'open'):
        pyautogui.click(OPEN_PANEL_POS, duration=get_rnd_mouse_speed())
        print '%s AT panel is closed, opening...' % get_loc_time()
    if isOpen & (action=='close'):
        pyautogui.click(CLOSE_PANEL_POS, duration=get_rnd_mouse_speed())
        print '%s AT panel is opened, closing...' % get_loc_time()
    time.sleep(INTERFACE_SLEEP)

########################################################################################################################

def template_on_image(cv2_gray, template, threshold, debug=False):
    """
    Checks whether given template is found on the given image.
    :param cv2_gray: gray image to search on
    :param template: template to search
    :param threshold: how sure we must be to consider template being found, 0.0 - 1.0
    :param debug: True to create debug screenshots
    :return:
    """
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

########################################################################################################################

def get_cropped(cv2_image, box):
    """
    :param cv2_image: cv2 image to crop from
    :param box: an array [top_left_point, bottom_right_point]
    :return: cropped area of cv2_image
    """
    x1 = box[0][0]
    x2 = box[1][0]
    y1 = box[0][1]
    y2 = box[1][1]
    cv2_cropped = cv2_image[y1:y2, x1:x2]
    return cv2_cropped

########################################################################################################################

def parse_team_status(PIL_image, top_left, maxStats):

    maxSoldiers, maxVehicles, maxMorale = maxStats

    vehicles_bar_pos = (top_left[0] + 95, top_left[1] + 19)
    soldiers_bar_pos = (vehicles_bar_pos[0], vehicles_bar_pos[1] + 22)
    morale_bar_pos = (vehicles_bar_pos[0] - 75, vehicles_bar_pos[1] - 28)
    bar_width = 50

    # Counting the length of the vehicles bar
    length = count_bar_pixels(PIL_image, GREEN, vehicles_bar_pos) + count_bar_pixels(PIL_image, RED, vehicles_bar_pos)
    vehicle_bar_status = length / float(bar_width) * maxVehicles

    # Counting the length of the soldiers bar
    length = count_bar_pixels(PIL_image, GREEN, soldiers_bar_pos) + count_bar_pixels(PIL_image, RED, soldiers_bar_pos)
    soldiers_bar_status = length / float(bar_width) * maxSoldiers

    # Counting the length of the morale bar
    morale_bar_width = 42
    length = count_bar_pixels(PIL_image, GREEN, morale_bar_pos) + count_bar_pixels(PIL_image, RED, morale_bar_pos)
    morale_bar_status = length / float(morale_bar_width) * maxMorale

    # Check if the AT is currently in queue
    # Cropping AT sheet
    bottom_right = (SCREEN_RESOLUTION[0], top_left[1] + 50)
    cv2_gray = convert_PILToCV2(PIL_image, cv2.COLOR_RGB2GRAY)
    cv2_gray = get_cropped(cv2_gray, box=((top_left[0], top_left[1] - 25), bottom_right))

    inQueue = template_on_image(cv2_gray, QUEUE_TEMPLATE, 0.825, debug=False)
    canBeDeployed = template_on_image(cv2_gray, DEPLOY_TEMPLATE, 0.825, debug=False)
    isInBattle = template_on_image(cv2_gray, RETREAT_TEMPLATE, 0.825, debug=False)
    isMoving = template_on_image(cv2_gray, MOVINGTO_TEMPLATE, 0.8, debug=False)
    canBeReinforced = template_on_image(cv2_gray, REINFORCE_TEMPLATE, 0.825, debug=False)

    #cv2_image = convert_PILToCV2(PIL_image)
    #cv2.line(cv2_image, vehicles_bar_pos, soldiers_bar_pos, (0,0,255))
    #cv2.imshow(name, cv2_image)
    curStats = (soldiers_bar_status, vehicle_bar_status, morale_bar_status, inQueue, canBeDeployed, isMoving, canBeReinforced, isInBattle)

    return curStats

########################################################################################################################

def get_teams(PIL_image, debug=False):
    """
    Analyzes sidebar panel and returns an array of all available teams.
    :param cv2_gray: if provided, searches in the image instead, otherwise makes a new screenshot
    :param debug: boolean, if true, shows an image with highlighted ATs and their type
    :return: an array of assault teams with [type, XY, [0, 0, 0], [maxsoldiers, maxvehicles, maxmorale]] elements
    """
    cv2_gray = convert_PILToCV2(PIL_image, cv2.COLOR_RGB2GRAY)

    # Excluding parts of the picture that do not contain AT panel
    cv2.rectangle(cv2_gray, (0,0), (CLOSE_PANEL_POS[0], SCREEN_RESOLUTION[1]), 0, -1)

    # Preallocating memory for our Assault Teams
    teams = []

    for elem in AT_TEMPLATES:
        template, type, maxStats = elem

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
            team = AT.AssaultTeam(type, pt, maxStats)
            team.setStatus(status)
            teams.append(team)
            if debug:
                print status
                cv2.rectangle(cv2_gray, pt, (pt[0] + w, pt[1] + h), 255, 2)
                cv2.putText(cv2_gray, '%s' % type, (pt[0], pt[1]), cv2.FONT_HERSHEY_SIMPLEX, 1, 255, 1)

    if debug:
        cv2.imwrite(DEBUG_DIR + get_unique_screenshot_name(), cv2_gray)

    return teams

########################################################################################################################

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

########################################################################################################################

def get_city_pos(city):
    x, y = FIRST_STAR
    x += STAR_STEP * city
    return (x, y)

########################################################################################################################

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

########################################################################################################################

def move_team_to(team, pos):
    x, y = team.getPos()
    pyautogui.moveTo(x, y, get_rnd_mouse_speed())
    # pyautogui.dragTo(pos, 1)

    pyautogui.mouseDown(team.getPos())
    pyautogui.moveTo(pos[0], pos[1], 2)
    pyautogui.mouseUp(pos)

########################################################################################################################

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

########################################################################################################################

def move_screen_to_team(team):
    pyautogui.click(team.getPos(), duration=get_rnd_mouse_speed())
    time.sleep(INTERFACE_SLEEP)
    pyautogui.doubleClick(team.getPos(), interval=0.3)
    time.sleep(TRANSLATION_SLEEP)

########################################################################################################################

def get_position_sitrep(debug=False):

    # This function was calibrated for altitude level 4
    move_to_altitude(4)

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

    # 5. Finding the closest BLUE town
    closestBlueTown = find_closest_circle(SCREEN_CENTER, blue_towns)

    # 6. Checking if we are out of the FRONTLINE_DANGER_ZONE
    isInSafeTown = True
    closestRed = find_closest_circle(SCREEN_CENTER, red_towns)
    if closestRed is not None:
        dist, (x, y) = closestRed
        if dist < FRONTLINE_DANGER_ZONE:
            isInSafeTown = False

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
        #cv2.imwrite(DEBUG_DIR + get_unique_screenshot_name(), cv2.add(cv2_mask_rg, cv2_mask_bg))

    return isInSafeTown, closestBlueTown

########################################################################################################################

def get_loc_time():
    return time.strftime('%c', time.localtime(int(time.time())))

########################################################################################################################

def simulate_activity(debug=False):

    # activity2 will remain unused for now, as I suspect it could be tracked way too easily
    # clicking on towns every minute or so may appear inconsistent with average GLOBAL map usage
    activities = (activity2, activity2)
    func = random.choice(activities)
    func(debug)

    return

def activity1(debug=False):
    # Dragging camera in random direction
    range = (-300, 300)
    minDragDistance = 100

    x, y = SCREEN_CENTER
    i, j = (x - random.randrange(range[0], range[1]), y + random.randrange(range[0], range[1]))

    # Simple trick to make sure we actually drag over some distance
    while distance(SCREEN_CENTER, (i, j)) < minDragDistance:
        i, j = (x - random.randrange(range[0], range[1]), y + random.randrange(range[0], range[1]))

    pyautogui.moveTo(x, y, get_rnd_mouse_speed())
    pyautogui.mouseDown(SCREEN_CENTER)
    pyautogui.moveTo(i, j, get_rnd_mouse_speed())
    pyautogui.mouseUp(i, j)

def activity2(debug=False):
    # Moving camera to a random city
    count = count_major_cities()
    if count == 0:
        die()
    random_city = random.choice(xrange(count))
    if debug:
        cityName = get_city_name(random_city)
        print '%s Moving camera to %s (ID %d)' % (get_loc_time(), cityName, random_city)
    move_screen_to_city(random_city)


########################################################################################################################

def get_towns_to_deploy(PIL_image=None, debug=False):
    if PIL_image is None:
        PIL_image = make_screenshot()
    cv2_image = convert_PILToCV2(PIL_image)
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

########################################################################################################################

def find_template_by_type(team_type):
    for sheet in AT_TEMPLATES:
        if sheet[1].lower() == team_type.lower():
            return sheet[0]
    return None

########################################################################################################################

def find_team_by_reinforcement(reinforcement):
    global TEAMS
    x1, y1 = reinforcement.getPos()
    closestTeam = None
    minDist = None
    for t in TEAMS:
        if t.isReinforcement(): continue
        x2, y2 = t.getPos()
        if y2 > y1: continue
        # 't' is above 'team' in the panel
        if closestTeam is None:
            closestTeam = t
            minDist = y1 - y2
        if y1 - y2 < minDist:
            closestTeam = t
            minDist = y1 - y2
    return closestTeam

########################################################################################################################

def has_reinforcements_rolling(team):
    # We need to find an AT located right below 'team' and check if it is a reinforcement
    Y = team.getPos()[1]
    hasReinforcementsRolling = False

    min = SCREEN_RESOLUTION[1]
    minT = None

    for t in TEAMS:
        if t is team:
            continue
        x, y = t.getPos()
        if y < Y:
            continue
        # Here we have all ATs located below 'team'
        if y - Y < min:
            min = y - Y
            minT = t

    if minT is not None:
        hasReinforcementsRolling = minT.isReinforcement()

    return hasReinforcementsRolling

########################################################################################################################

def reset_altitude():
    global CURRENT_ALTITUDE
    global FAILED_ATTEMPTS
    print '%s Resetting altitude.' % get_loc_time()
    CURRENT_ALTITUDE = -1
    FAILED_ATTEMPTS = 0

########################################################################################################################

def manage_team(team, debug=False):
    """
    Makes a decision what to do with given assault team: deploy, send to attack, send to retreat, nothing
    :param team:
    :return: nothing
    """

    global FAILED_ATTEMPTS

    # First we need to confirm if the AT is still on it's place in the panel
    # AT could be shifted down or up in the panel by reinforcements
    screencap = make_screenshot()
    cv2_gray = convert_PILToCV2(screencap, cv2.COLOR_RGB2GRAY)
    x, y = team.getPos()
    margin = 5

    template = find_template_by_type(team.getType())
    w, h = template.shape[::-1]
    top_left = (x - margin, y - margin)
    bottom_right = x + w + 2 * margin, y + h + 2 * margin
    cv2_gray = get_cropped(cv2_gray, box=(top_left, bottom_right))
    invalidPos = not template_on_image(cv2_gray, template, 0.8)

    # If the team was shifted, all coordinates the team has stored
    # become invalid, we can't rely on them, so we just return
    if invalidPos:
        print '%s %s\'s icon was shifted by reinforcement team(s), waiting for another cycle.' % (
        get_loc_time(), team.getType())
        if debug:
            cv2.imwrite(DEBUG_DIR + get_unique_screenshot_name(), cv2_gray)
        return

    # By this point, what we see on the screencap matches what the team icon should look like
    # which usually indicates nothing got shifted anywhere and we can proceed
    if team.isReinforcement():
        mainTeam = find_team_by_reinforcement(team)
        if mainTeam is None:
            print '%s couldn\'t find a team that is being reinforced, can\'t correct %s\'s way.' % (get_loc_time(), team.getType())
        else:
            # On a lower altitude the accuracy of sending troops is better, so we go with level 4 here
            move_to_altitude(4)
            move_screen_to_team(mainTeam)
            move_team_to(team, SCREEN_CENTER)

            # Debug snippet
            if debug:
                screencap = make_screenshot()
                cv2_image = convert_PILToCV2(screencap)
                cv2.arrowedLine(cv2_image, team.getPos(), SCREEN_CENTER, (0, 255, 0), 2)
                cv2.putText(cv2_image, 'Correcting %s' % team.getType(), SCREEN_CENTER, cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.imwrite(DEBUG_DIR + get_unique_screenshot_name(), cv2_image)
            # Debug snipped end

            print '%s Trying to correct %s on it\'s way to %s' % (get_loc_time(), team.getType(), mainTeam.getType())
        return

    if team.canBeDeployed():
        print '%s %s can be deployed, trying to deploy...' % (get_loc_time(), team.getType())

        # Buying troops
        toggle_panel('open')

        pyautogui.click(team.getIconPos(), duration=get_rnd_mouse_speed())
        time.sleep(INTERFACE_SLEEP)

        pyautogui.click(BUY_BUTTON_POS, duration=get_rnd_mouse_speed())
        time.sleep(INTERFACE_SLEEP)

        # Getting color of one pixel on 'No, Thanks' button
        screencap = make_screenshot()
        col1 = screencap.getpixel(NO_THANKS_POS)

        # Looking for towns to click on
        deploy_points = get_towns_to_deploy(screencap, debug=False)
        if deploy_points is None:
            print 'Couldn\'t find any towns in the list of towns to deploy, but that list can\'t be empty!'
            die()

        # TODO implement text recognition to deliberately choose the city we want to spawn at

        # Since reading text is not implemented yet, we simply click on a random town to deploy
        circle = random.choice(deploy_points)
        x, y, r = circle[0, :]
        pyautogui.click(x, y, duration=get_rnd_mouse_speed())

        # Checking if the team was spawned successfully
        time.sleep(INTERFACE_SLEEP)
        screencap = make_screenshot()
        col2 = screencap.getpixel(NO_THANKS_POS)

        # If colors match, then the team wasn't deployed and the window is not closed, then we close it manually
        NotEnoughMorale = any(map(eq, col1, col2))
        if NotEnoughMorale:
            pyautogui.click(NO_THANKS_POS, duration=get_rnd_mouse_speed())
            print '%s %s doesn\'t have enough morale to get deployed (failed to deploy).' % (get_loc_time(), team.getType())
        else:
            print '%s %s now stands in queue to be deployed in random city.' % (get_loc_time(), team.getType())

        return

    if team.isKIA() | team.isInQueue() | team.isMoving() | team.isInBattle():
        return
    # Team is deployed, not in battle, not in queue

    move_screen_to_team(team)

    # Check if it needs rest\reinforcements
    if team.needsRest() | team.needsReinforcements():

        isInSafeTown, safeTown = get_position_sitrep(debug=True)
        if safeTown is not None:
            safeTownDistance, safeTownPos = safeTown

        if isInSafeTown:
            if team.needsRest():
                # If team needs rest, we will reinforce it even if it has only minor casualties
                if team.canBeReinforced():
                    # Reinforce the team
                    print '%s %s is resting and could use reinforcement. Putting it in queue to get one.' % (get_loc_time(), team.getType())
                    toggle_panel('open')
                    pyautogui.click(team.getIconPos(), duration=get_rnd_mouse_speed())
                    time.sleep(INTERFACE_SLEEP)
                    pyautogui.click(BUY_BUTTON_POS, duration=get_rnd_mouse_speed())
                else:
                    print '%s %s is fully reinforced and resting in safe place.' % (get_loc_time(), team.getType())
                    return
            else:
                # If rest is not needed, but team is in need of reinforcements
                if team.needsReinforcements():
                    if team.canBeReinforced():
                        # Reinforce the team
                        print '%s Putting %s in queue for reinforcements.' % (get_loc_time(), team.getType())
                        toggle_panel('open')
                        pyautogui.click(team.getIconPos(), duration=get_rnd_mouse_speed())
                        time.sleep(INTERFACE_SLEEP)
                        pyautogui.click(BUY_BUTTON_POS, duration=get_rnd_mouse_speed())
                    return
        else:
            # Send team away from the frontline
            if safeTown is None:
                print '%s Can\'t send %s away from the frontline. No safe towns around.' % (get_loc_time(), team.getType())

                # Part of the self correction snippet
                FAILED_ATTEMPTS += 1
                if FAILED_ATTEMPTS > FAILED_ATTEMPTS_LIM:
                    reset_altitude()

                # TODO this is a potential loop here. Assault team will stand still until the town is found.
            else:
                print '%s Sending %s away from the frontline.' % (get_loc_time(), team.getType())

                # Debug snippet
                if debug:
                    screencap = make_screenshot()
                    cv2_image = convert_PILToCV2(screencap)
                    cv2.arrowedLine(cv2_image, SCREEN_CENTER, safeTownPos, (0, 255, 0), 2)
                    cv2.putText(cv2_image, '%s retreats' % team.getType(), SCREEN_CENTER, cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    cv2.imwrite(DEBUG_DIR + get_unique_screenshot_name(), cv2_image)
                # Debug snipped end

                move_team_to(team, safeTownPos)
            return

    # Do nothing if we are standing in safe place and there is a reinforcement rolling
    if has_reinforcements_rolling(team):
        print '%s Team %s waiting for reinforcements to reach it.' % (get_loc_time(), team.getType())
        return

    # According to team's thresholds, team's status is OK, and it has no reinforcements to catch up with
    if team.isReady():
        print '%s %s can fight alright, trying to send it in battle...' % (get_loc_time(), team.getType())

        # Looking for battles nearby
        battles = find_battles_on_screen(debug=False)
        if battles is None:
            print 'No battles around :('

            # Findind city closest to the frontline
            count = count_major_cities()
            if count == 0:
                print 'Failed to find major cities on the screen.'
                die()
            print 'At this moment our faction controls %d major cities...' % count

            move_to_altitude(7)
            frontLineCity = find_frontline_city(count)

            # Normally we get None only if the altitude got broken
            if frontLineCity is None:
                print 'Can\'t find frontline city.'
                reset_altitude()
                return

            cityID, battlePos, distanceToBattle = frontLineCity
            cityName = get_city_name(cityID)

            print 'The closest battle is next to %s, sending %s there.' % (cityName, team.getType())
            move_screen_to_city(cityID)

            # Debug snippet
            if debug:
                screencap = make_screenshot()
                cv2_image = convert_PILToCV2(screencap)
                cv2.arrowedLine(cv2_image, team.getPos(), SCREEN_CENTER, (0, 255, 0), 2)
                cv2.putText(cv2_image, 'Sending %s to %s' % (team.getType(), cityName), SCREEN_CENTER, cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.imwrite(DEBUG_DIR + get_unique_screenshot_name(), cv2_image)
            # Debug snipped end

            move_team_to(team, SCREEN_CENTER)

        else:
            # Sending team to the battlefield
            battleDist, battlePos = find_closest_circle(SCREEN_CENTER, battles)

            # Debug snippet
            screencap = make_screenshot()
            cv2_image = convert_PILToCV2(screencap)
            cv2.arrowedLine(cv2_image, SCREEN_CENTER, battlePos, (0, 255, 0), 2)
            cv2.putText(cv2_image, '%s attacks' % team.getType(), SCREEN_CENTER, cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
            cv2.imwrite(DEBUG_DIR + get_unique_screenshot_name(), cv2_image)
            # Debug snipped end

            move_team_to(team, battlePos)

            # Check if we sent a team that can not be sent, and accidentally clicked on battle
            time.sleep(INTERFACE_SLEEP)
            screencap = make_screenshot()
            col1 = screencap.getpixel(CLOSE_POS)

            time.sleep(INTERFACE_SLEEP)
            screencap = make_screenshot()
            col2 = screencap.getpixel(CLOSE_POS)

            # If colors don't match, then there is an overlapping window appeared, and we need to close it
            ClickedOnBattle = not any(map(eq, col1, col2))
            if ClickedOnBattle:
                print '%s Accidentally clicked on town, closing the window now.' % get_loc_time()

                # Debug snipped
                if debug:
                    cv2_image = convert_PILToCV2(screencap)
                    cv2.circle(cv2_image, CLOSE_POS, 15, (0, 255, 0), 2)
                    cv2.imwrite(DEBUG_DIR + get_unique_screenshot_name(), cv2_image)
                # Debug snipped end

                pyautogui.click(CLOSE_POS, duration=get_rnd_mouse_speed())

    return

########################################################################################################################

def main():

    global FAILED_ATTEMPTS
    global CURRENT_ALTITUDE
    global TEAMS

    time.sleep(3)

    while True:
        # Open AT panel
        toggle_panel(action='open', debug=False)

        screencap = make_screenshot()

        TEAMS = get_teams(screencap, debug=False)
        if TEAMS.__len__() == 0:
            print 'No assault teams found, nothing to deploy.'
            die()

        # Managing ATs
        for team in TEAMS:
            manage_team(team, debug=True)

        time.sleep(10 + random.randrange(0, 15))
        simulate_activity(debug=False)
        time.sleep(5 + random.randrange(0, 15))

########################################################################################################################


if __name__ == "__main__":
    main()