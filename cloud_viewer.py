import serial
import struct
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# ───────────── CONFIG ─────────────
PORT       = 'COM9'            # adjust to your COM port
BAUD       = 921600
POINTS     = 12
PKT_SZ     = 1 + 1 + 2 + 2 + POINTS*(2+1) + 2 + 2 + 1
FMT        = '<BBHH' + 'HB'*POINTS + 'HHB'

# ─────────── RESOLUTION SETUP ──────
BINS       = 2160
RESOLUTION = 360.0 / BINS
bin_degrees = np.arange(0, 360, RESOLUTION)
thetas      = np.deg2rad(bin_degrees[:BINS])

# sensor valid range (mm)
MIN_R, MAX_R = 50, 8000

# buffer for one full revolution
distances = np.full(BINS, np.nan, dtype=float)

# ─────────── SERIAL SETUP ──────────
ser = serial.Serial(PORT, BAUD, timeout=0.1)
ser.reset_input_buffer()

# ─────────── CRC / CHECKSUM ──────────
def verify_crc(raw: bytes) -> bool:
    # Replace with your sensor’s actual CRC logic if available
    return True

# ─────────── READ & PARSE ──────────
def read_one_packet():
    """Read exactly one packet starting with 0x54 or return None."""
    while True:
        hdr = ser.read(1)
        if not hdr:
            return None
        if hdr[0] == 0x54:
            break

    rest = ser.read(PKT_SZ - 1)
    if len(rest) != PKT_SZ - 1:
        return None
    raw = hdr + rest

    if not verify_crc(raw):
        return None

    return raw

def unpack_packet(raw):
    """Unpack one valid packet into a list of (bin_idx, distance)."""
    try:
        f = struct.unpack(FMT, raw)
    except struct.error:
        return []

    start = f[3] / 100.0
    end   = f[4 + 2*POINTS] / 100.0
    step  = (end - start) / (POINTS - 1)

    updates = []
    idx = 4
    for i in range(POINTS):
        r   = f[idx]
        ang = start + step*i
        idx += 2

        # drop out-of-range readings
        if not (MIN_R <= r <= MAX_R):
            continue

        bin_idx = int(round(ang / RESOLUTION)) % BINS
        updates.append((bin_idx, r))

    return updates

# ─────────── PLOT SETUP ───────────
plt.ion()
fig = plt.figure()
ax  = fig.add_subplot(111, projection='polar')
sc  = ax.scatter(thetas, distances, s=1)
ax.set_theta_zero_location('N')
ax.set_theta_direction(-1)      # change to +1 if you want CCW
ax.set_ylim(0, MAX_R + 200)
ax.set_title('STL-27L Live: Full-Scan Only (0.167° Resolution)')

# ─────────── SCROLL / WHEEL ZOOM ───────────
def on_scroll(event):
    if event.inaxes is not ax:
        return
    base_scale = 1.2
    # scroll 'up' = zoom in, 'down' = zoom out
    scale = (1/base_scale if event.button == 'up' else base_scale)
    rmin, rmax = ax.get_ylim()
    ax.set_ylim(rmin, rmax * scale)
    fig.canvas.draw_idle()

fig.canvas.mpl_connect('scroll_event', on_scroll)

# ─────────── UPDATE LOOP ───────────
last_start = None

def update(_):
    global last_start

    # read & apply all queued packets
    while ser.in_waiting >= PKT_SZ:
        raw = read_one_packet()
        if raw is None:
            continue

        # peek at start angle (degrees) to detect wrap
        start_deg = struct.unpack_from('<BBHH', raw)[3] / 100.0

        # if angle decreased, we’ve just finished a revolution
        if last_start is not None and start_deg < last_start:
            # draw the full scan
            sc.set_offsets(np.column_stack((thetas, distances)))
            # clear for the next revolution
            distances[:] = np.nan

        last_start = start_deg

        # unpack & write this packet’s valid points
        for bin_idx, r in unpack_packet(raw):
            distances[bin_idx] = r

    return sc,

ani = animation.FuncAnimation(fig, update, interval=50, blit=True)
plt.show(block=True)

ser.close()
