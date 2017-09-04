from PIL import Image
import cv2
import numpy as np
from operator import eq

import math
import time
import pyautogui
pyautogui.FAILSAFE = True

import AT

FIRST_STAR = (541, 135)
STAR_STEP = 37

BLACK = (0, 0, 0)
GREEN = (46, 129, 37)
BLUE = (53, 88, 204)
RED = (175, 43, 30)
YELLOW_BGR = (97, 255, 255)

SCREEN_RESOLUTION = None
SCROLLING_STEP = 2000
SCROLLING_SLEEP = 0.25

QUEUE_TEMPLATE = cv2.imread('templates/Queue.png',0)
DEPLOY_TEMPLATE = cv2.imread('templates/Deploy.png',0)
RETREAT_TEMPLATE = cv2.imread('templates/Retreat.png',0)
MORALE_TEMPLATE = cv2.imread('templates/Morale.png',0)
AT_TEMPLATES = [
    # template, name, [maxSoldiers, maxVehicles, maxMorale]
    [cv2.imread('templates/light_armor.png', 0), 'Light_Armor', [20, 16, 100]],
    [cv2.imread('templates/motorized_guard.png', 0), 'Motorized_Guard', [36, 12, 100]],
    [cv2.imread('templates/motorized_recon.png', 0), 'Motorized_Recon', [24, 24, 100]],
    [cv2.imread('templates/mechanized_recon.png', 0), 'Mechanized_Recon', [28, 14, 100]],
    [cv2.imread('templates/fighter_recon.png', 0), 'Fighter_Recon', [20, 16, 100]]
]
MAXIMUM_ATs_ON_PANEL = 20 # how many AT's can fit in sidebar, make it bigger than the actual number
AT_VERTICAL_STEP = 106 # vertical step between AT's in sidebar
AT_VERTICAL_SPACING = 150 # the list of ATs starts at this height

def die():
    print 'Make sure you\'re running H&G in 1920x1080 window, your tab is set to GLOBAL & your color scheme is RED-BLUE.'
    exit()

def make_screenshot(saveDirectory=None):
    """
    Makes a screenshot, returns a PIL image, saves the file in given path if saveDirectory was specified
    :param saveDirectory: if specified, must end with '/', like 'screenshots/'
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
    time.sleep(0.5)
    scroll(-1, 2, SCROLLING_SLEEP)  # to compensate zooming out
    time.sleep(0.5)

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

def toggle_AT_panel(PIL_image=None, action=None):
    if action is None:
        if is_AT_panel_opened(PIL_image):
            action = 'close'
        else:
            action = 'open'
    if action == 'open':
        pyautogui.click(1505, 173)
        print 'Opening AT panel...'
    if action=='close':
        pyautogui.click(1698, 173)
        print 'Closing AT panel...'

def template_on_image(cv2_gray, template, threshold, debug=False):
    w, h = template.shape[::-1]
    res = cv2.matchTemplate(cv2_gray, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
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
    cv2_gray = get_cropped(cv2_gray, box=(top_left, bottom_right))
    inQueue = template_on_image(cv2_gray, QUEUE_TEMPLATE, 0.85, debug=False)
    canBeDeployed = template_on_image(cv2_gray, DEPLOY_TEMPLATE, 0.85, debug=False)
    isInBattle = template_on_image(cv2_gray, RETREAT_TEMPLATE, 0.85, debug=False)
    #cv2_image = convert_PILToCV2(PIL_image)
    #cv2.line(cv2_image, vehicles_bar_pos, soldiers_bar_pos, (0,0,255))
    #cv2.imshow(name, cv2_image)
    curStats = (soldiers_bar_status, vehicle_bar_status, morale_bar_status, inQueue, canBeDeployed, isInBattle)
    print curStats
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

def manage_team(team):
    """
    Makes a dicision on what to do with given assault team: deploy, send to attack, send to retreat, nothing
    :param team:
    :return: nothing
    """

    if team.canBeDeployed():
        # Deploy the team in the frontline city
        print 'Deploying %s...' % team.getName()
        # Findind city closest to the frontline
        count = count_main_cities()
        if count == 0:
            print 'Failed to find main cities on the screen.'
            die()
        print 'At this moment our faction controls %d main cities...' % count
        move_to_altitude()
        city = find_frontline_city(count)
        print 'City #%d has the closest battle (distance %d), deploying ATs in there...' % (city[0], city[2])

        pyautogui.click(team.getIconPos())
        # To be continued...

        return

    if team.needsRest() | team.needsReinforcements():
        # Sending team to retreat
        if team.needsRest():
            print ' It needs rest.',
        if team.needsReinforcements():
            print ' It needs to be reinforced.',

    if team.isReady():
        # Sending team to the battlefield
        print '%s still can fight alright, sending it to a battlefield...'
        return






def main():

    time.sleep(3)

    # Counting main cities
    #count = count_main_cities()
    #if count == 0:
    #    print 'Failed to find main cities on the screen.'
    #    die()
    #print 'It looks like our faction controls %d main cities...' % count

    while True:

        screencap = make_screenshot()

        # Open AT panel if it's closed
        if not is_AT_panel_opened:
            toggle_AT_panel(screencap, 'open')

        teams = get_teams(screencap, debug=False)
        if teams.__len__() == 0:
            print 'No assault teams found, nothing to deploy.'
            die()



        # Managing ATs

        cv2.waitKey(0)
        exit()
    # Gathering information about available ATs

    # Selecting a deploy point
    #move_to_altitude()
    #city = find_frontline_city(count)
    #print 'City #%d has the closest battle (distance %d), deplying ATs in there...' % (city[0], city[2])

    # obsolete
    #print 'Creating an attack plan...'
    #move_to_city(city[0])
    #plan = make_screenshot()
    #cv2_plan = convert_PILToCV2(plan)
    #cur_city_pos = (SCREEN_RESOLUTION[0] / 2, SCREEN_RESOLUTION[1] / 2)
    #cv2.rectangle(cv2_plan, cur_city_pos, cur_city_pos, (0,255,0), 10)
    #cv2.putText(cv2_plan, 'City #%d sending ATs' % city[0], cur_city_pos, cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
    #cv2.line(cv2_plan, cur_city_pos, city[1], (0, 0, 255), 4)
    #cv2.imwrite(str(int(time.time())) + '.png', cv2_plan)




if __name__ == "__main__":
    main()