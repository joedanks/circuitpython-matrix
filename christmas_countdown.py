import time
import board
import displayio
from rtc import RTC
from adafruit_matrixportal.network import Network
from adafruit_matrixportal.matrix import Matrix
from adafruit_bitmap_font import bitmap_font
import adafruit_display_text.label

try:
    from secrets import secrets
except ImportError:
    print('Unable to find secrets.py')
    raise

EVENT_YEAR = 2020
EVENT_MONTH = 12
EVENT_DAY = 25
EVENT_HOUR = 0
EVENT_MINUTE = 0

BITPLANES = 6

try:
    TIMEZONE = secrets['timezone']
except:
    print('No timezone in secrets.py')
    raise


def parse_time(timestring, is_dst=-1):
    """ Given a string of the format YYYY-MM-DDTHH:MM:SS.SS-HH:MM (and
        optionally a DST flag), convert to and return an equivalent
        time.struct_time (strptime() isn't available here). Calling function
        can use time.mktime() on result if epoch seconds is needed instead.
        Time string is assumed local time; UTC offset is ignored. If seconds
        value includes a decimal fraction it's ignored.
    """
    date_time = timestring.split('T')        # Separate into date and time
    year_month_day = date_time[0].split('-') # Separate time into Y/M/D
    hour_minute_second = date_time[1].split('+')[0].split('-')[0].split(':')
    return time.struct_time(int(year_month_day[0]),
                            int(year_month_day[1]),
                            int(year_month_day[2]),
                            int(hour_minute_second[0]),
                            int(hour_minute_second[1]),
                            int(hour_minute_second[2].split('.')[0]),
                            -1, -1, is_dst)


def get_current_time():
    time_data = NETWORK.fetch_data('http://worldtimeapi.org/api/timezone/' + TIMEZONE,
                       json_path=[['datetime'], ['dst'],
                                  ['utc_offset']])
    time_struct = parse_time(time_data[0], time_data[1])
    RTC().datetime = time_struct
    return time_struct, time_data[2]


def get_time_until():
    event_time = time.struct_time(
        (
            EVENT_YEAR,
            EVENT_MONTH,
            EVENT_DAY,
            EVENT_HOUR,
            EVENT_MINUTE,
            0, # seconds
            -1,
            -1,
            False
        )
    )
    print(get_current_time())
    remaining = time.mktime(event_time) - time.mktime(time.localtime())
    if remaining <= 0:
        MATRIX.set_text("MERRY CHRISTMAS")
        return
    remaining //= 60
    mins_remaining = remaining % 60
    remaining //= 60
    hours_remaining = remaining % 24
    remaining //= 24
    days_remaining = remaining

    if days_remaining == 1:
        days_remaining = '{} Day'.format(days_remaining)
    elif days_remaining == 0:
        days_remaining = ''
    else:
        days_remaining = '{} Days'.format(days_remaining)

    return days_remaining, '{}:{}'.format(hours_remaining, mins_remaining)


# --- Display setup ---
MATRIX = Matrix(bit_depth=BITPLANES)
DISPLAY = MATRIX.display

SMALL_FONT = bitmap_font.load_font('/fonts/helvR10.bdf')

GROUP = displayio.Group(max_size=10)

FILENAME = 'christmas/christmas_tree_small.bmp'
BITMAP = displayio.OnDiskBitmap(open(FILENAME, 'rb'))
TILE_GRID = displayio.TileGrid(BITMAP,
                               pixel_shader=displayio.ColorConverter(),)
GROUP.append(TILE_GRID)
GROUP.append(adafruit_display_text.label.Label(SMALL_FONT, color=0xFFFF00, text='00 Days', x=25, y=8))
GROUP.append(adafruit_display_text.label.Label(SMALL_FONT, color=0xFFFF00, text='00:00', x=32, y=24))

DISPLAY.show(GROUP)

NETWORK = Network(status_neopixel=board.NEOPIXEL, debug=False)
NETWORK.connect()

while True:
    days, hours = get_time_until()
    GROUP[1].text = days
    GROUP[2].text = hours
    DISPLAY.refresh()
    time.sleep(15)