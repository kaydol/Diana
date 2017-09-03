from PIL import Image
import cv2
import numpy as np
from operator import eq

import math
import time
import pyautogui
pyautogui.FAILSAFE = True

FIRST_STAR = (541, 135)
STAR_STEP = 37
BLUE = (53, 88, 204)
RED = (175, 43, 30)
YELLOW_BGR = (97, 255, 255)
SCREEN_RESOLUTION = None
SCROLLING_STEP = 2000
SCROLLING_SLEEP = 0.25

MORALE_TEMPLATE = cv2.imread('templates/morale.png',0)
AT_TEMPLATES = [
    [cv2.imread('templates/light_armor.png', 0), 'Light_Armor', [20, 16, 100]],
    [cv2.imread('templates/motorized_guard.png', 0), 'Motorized_Guard', [36, 12, 100]],
    [cv2.imread('templates/motorized_recon.png', 0), 'Motorized_Recon', [24, 24, 100]],
    [cv2.imread('templates/mechanized_recon.png', 0), 'Mechanized_Recon', [28, 14, 100]],
    [cv2.imread('templates/fighter_recon.png', 0), 'Fighter_Recon', [20, 16, 100]]
]
MAXIMUM_ATs_ON_PANEL = 20 # how many AT's can fit in sidebar, make it bigger than the actual number
AT_VERTICAL_STEP = 106 # vertical step between AT's in sidebar
AT_VERTICAL_SPACING = 150 # the list of ATs starts at this height

def make_screenshot(saveDirectory=None):
    """
    Makes a screenshot, returns a PIL image, saves the file in given path if saveDirectory was specified
    :param saveDirectory: if specified, must have an entailing /, like 'screenshots/'
    :return: returns a PIL image
    """
    global SCREEN_RESOLUTION
    if SCREEN_RESOLUTION is None:
        SCREEN_RESOLUTION = pyautogui.size()
    screenshot = pyautogui.screenshot()
    if saveDirectory is not None:
        screenshot_name = saveDirectory + str(int(time.time())) + '.png'
        screenshot.save(screenshot_name)
    return screenshot

def move_to_altitude():
    """
    Sets the camera to be on 7 ticks above the map.
    :return:
    """
    # Zoom in fully
    scroll(1, 15)
    # Zoom out slightly
    scroll(-1, 7)

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

def move_to_city(cityNumber):
    """
    Performs a mouse click on a given city.
    :param cityNumber: the city we want to click on
    :return: nothing
    """
    x, y = FIRST_STAR
    pyautogui.click(x + STAR_STEP * cityNumber, y)
    pyautogui.moveTo(SCREEN_RESOLUTION[0] / 2, SCREEN_RESOLUTION[1] / 2)

def convert_CV2ToPIL(cv2_image, conversionType=cv2.COLOR_BGR2RGB):
    return Image.fromarray(cv2.cvtColor(cv2_image, conversionType))

def convert_PILToCV2(PIL_image, conversionType=cv2.COLOR_RGB2BGR):
    return cv2.cvtColor(np.array(PIL_image), conversionType)

def count_main_cities(PIL_image=None):
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

def find_battles():
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
    mask = cv2.add(mask_1, mask_2)
    #cv2_image = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
    # Finding circles aka battles
    circles = cv2.HoughCircles(mask, cv2.HOUGH_GRADIENT, 1, 20, param1=15, param2=5, minRadius=4, maxRadius=20)
    if circles is not None:
        circles = np.uint16(np.around(circles))
        #for i in circles[0, :]:
        #    cv2.circle(cv2_image, (i[0], i[1]), i[2], (0, 255, 0), 2)
        #    cv2.circle(cv2_image, (i[0], i[1]), 2, (0, 0, 255), 3)
        #cv2.imwrite(str(int(time.time())) + '.png', cv2_image)
    return circles

def find_frontline_city(countOfControlledCities=None):
    """
    Returns the city closest to the frontline, battle's coordinates and distance from the city to that battle.
    :param countOfControlledCities: integer, how many cities we have captured
    :return: None, or array (city, (battle's X and Y while given city is in the center of the screen), distance between these two places)
    """
    city = None
    if countOfControlledCities is None:
        countOfControlledCities = count_main_cities()
    for k in xrange(countOfControlledCities):
        move_to_city(k)
        scroll(-1, 2, SCROLLING_SLEEP) # to compensate zooming out
        time.sleep(2)
        cur_city_pos = (SCREEN_RESOLUTION[0] / 2, SCREEN_RESOLUTION[1] / 2)
        battles = find_battles()
        if battles is not None:
            for i in battles[0, :]:
                x, y, r = (i[0], i[1], i[2])
                if city is None:
                    city = (k, (x, y), distance(cur_city_pos, (x,y)))
                else:
                    if distance(cur_city_pos, (x,y)) < city[2]:
                        city = (k, (x, y), distance(cur_city_pos, (x, y)))
    return city

def is_AT_panel_opened(cv2_gray=None):
    """
    Searches for morale icon, then decides whether AT panel is opened or not based on its location.
    :param cv2_gray: if provided, an image to search in. If None, a new screenshot will be made
    :return: boolean
    """
    if cv2_gray is None:
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

def toggle_AT_panel(action=None):
    if action is None:
        if is_AT_panel_opened():
            action = 'close'
        else:
            action = 'open'
    if action == 'open':
        pyautogui.click(1505, 173)
        print 'Opening AT panel...'
    if action=='close':
        pyautogui.click(1698, 173)
        print 'Closing AT panel...'

def get_index(y):
    """
    Returns an index of Assault Team based on vertical coordinate.
    :param y: y coordinate of left upper corner of AT's template
    :return: number in range [0, MAXIMUM_ATs_ON_PANEL], or -1 if y < AT_VERTICAL_SPACING
    """
    index = 0
    while y > AT_VERTICAL_SPACING + index * AT_VERTICAL_STEP:
        index += 1
    return index - 1

def get_AT_list(cv2_gray=None, debug=False):
    """
    Analyzes sidebar panel and returns an array of all available teams.
    :param cv2_gray: if provided, searches in the image instead, otherwise makes a new screenshot
    :return: an array of assault teams with [index, AT_name] elements
    """
    if cv2_gray is None:
        PIL_image = make_screenshot()
        cv2_gray = convert_PILToCV2(PIL_image, cv2.COLOR_RGB2GRAY)

    # Preallocating memory for our Assault Teams
    assault_teams = []
    for i in xrange(MAXIMUM_ATs_ON_PANEL):
        assault_teams.append(None)

    for elem in AT_TEMPLATES:
        template, name, [maxsoldiers, maxvehicles, maxmorale] = elem
        w, h = template.shape[::-1]
        res = cv2.matchTemplate(cv2_gray, template, cv2.TM_CCOEFF_NORMED)
        threshold = 0.9
        loc = np.where(res >= threshold)
        for pt in zip(*loc[::-1]):
            i = get_index(pt[1])
            assault_teams[i] = [name, [0, 0, 0], [maxsoldiers, maxvehicles, maxmorale]]
            if debug:
                cv2.rectangle(cv2_gray, pt, (pt[0] + w, pt[1] + h), 255, 2)
                cv2.putText(cv2_gray, '%d:%s' % (i, name), (pt[0], pt[1]), cv2.FONT_HERSHEY_SIMPLEX, 1, 255, 1)

    # Removing empty slots in our array of Assault Teams
    assault_teams.sort()
    for i in xrange(MAXIMUM_ATs_ON_PANEL):
        team = assault_teams[MAXIMUM_ATs_ON_PANEL-i-1]
        if team is None:
            assault_teams.remove(team)
    if debug:
        cv2.imshow('AT sidebar analysis', cv2_gray)
    return assault_teams

def main():
    time.sleep(3)

    count = count_main_cities()
    if count == 0:
        print 'Failed to find main cities on the screen.'
        print 'Make sure you\'re running H&G in 1920x1080 window, your tab is set to GLOBAL & your color scheme is RED-BLUE.'
        exit()

    print 'It looks like our faction controls %d main cities...' % count

    #city = find_frontline_city(count)
    #print 'City #%d has the closest battle (distance %d), deplying ATs in there...' % (city[0], city[2])

    ATs = get_AT_list(debug=False)
    if ATs.__len__() == 0:
        print 'No assault teams found, nothing to deploy.'
        exit()
    print '%d assault teams found: ' % ATs.__len__(),
    for team in ATs:
        print '%s; ' % team[0],

    # Open AT panel if it's closed
    if not is_AT_panel_opened:
        toggle_AT_panel('open')

    # Reading\Updating status of Assault Teams


    #
    # move_to_altitude()
    # PIL_image = make_screenshot()
    # cv2_image = convert_PILToCV2(PIL_image)


    cv2.waitKey(0)

if __name__ == "__main__":
    main()