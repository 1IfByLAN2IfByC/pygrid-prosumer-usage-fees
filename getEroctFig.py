''' go to Ercot LMP page and download the .png every 6 minutes'''

import requests
import time
from datetime import datetime

site = 'http://www.ercot.com/content/cdr/contours/rtmLmpHg.png'
while True:
    timer = datetime.now()

    filename = 'ERCOT_LMP_{}'.format(
        timer.strftime("%m-%d, %H%M"))

    image = requests.get(site).content
    with open(filename+'.png', 'wb') as f:
        f.write(image)

    print('saved {}'.format(filename+'.png'))
    time.sleep(60*5)
