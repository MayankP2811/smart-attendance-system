# Setup guide

Three ways to run the project, from easiest to the full hardware:

1. [Website on your computer](#1-website-on-your-computer) (XAMPP, or PHP's built-in server)
2. [Docker](#2-docker) (one command)
3. [The station on a Raspberry Pi](#3-the-station-on-a-raspberry-pi) (fingerprint sensor, camera, LCD)

You can try everything except the real hardware on a laptop: the station has a `--mock` mode.

---

## 1. Website on your computer

### What you need

- PHP 8.1 or newer with the `pdo_mysql` extension (`php -m` lists it)
- MySQL 8 or MariaDB 10.6+
- Python 3.10+ (only for the station and the tests)

On Windows, [XAMPP](https://www.apachefriends.org/) gives you PHP, MariaDB and phpMyAdmin.

### Steps

1. **Settings.** Copy `.env.example` to `.env` in the repository root. Choose a database password and put it in `DB_PASSWORD`.

2. **Database.** Open `database/create_database.sql`, replace both `change-me` with the same password, then run the three files as the MySQL root user:

   ```bash
   mysql -u root -p < database/create_database.sql
   mysql -u root -p smart_attendance < database/schema.sql
   mysql -u root -p smart_attendance < database/demo_data.sql    # optional: made-up demo data
   ```

   In XAMPP you can paste each file into phpMyAdmin → *SQL* instead.

3. **Start the website.**

   - **Linux / macOS / any PHP install:** `./scripts/run_local.sh`, then open http://127.0.0.1:8000
     (or run `php -S 127.0.0.1:8000 -t web web/router.php` yourself).
   - **XAMPP:** copy or link the whole repository into `C:\xampp\htdocs\smart-attendance` and open
     http://localhost/smart-attendance/web/. The `.htaccess` files block the `includes/` and `cli/` folders
     and stop scripts from running in `uploads/`.

4. **Log in** with a demo account (password `Demo@123` for all):

   | Role | E-mail |
   | --- | --- |
   | Student (good attendance) | aarav.sharma@example.com |
   | Student (low attendance, shows the warning) | rohan.kulkarni@example.com |
   | Faculty (teaches Engineering Mathematics) | priya.deshmukh@example.com |

### Real accounts

- **Students** register themselves at *Create an account*. The roll number must be the same one used for their face photos (see [face recognition](#face-recognition)).
- **Faculty** accounts can't be created on the website. The admin creates them:

  ```bash
  php web/cli/create_user.php --role=faculty --first=Priya --last=Deshmukh \
      --email=priya@college.edu --subjects=maths
  ```

  The script asks for the password. `--subjects` links the teacher to subjects by their code.
- **Subjects** are rows in the `subjects` table (code, name, teacher, fingerprint slot). The demo data has five; add or rename them with phpMyAdmin or SQL.

To start with an empty system, load `schema.sql` without `demo_data.sql`.

---

## 2. Docker

```bash
docker compose up -d                 # MySQL + website, demo data loaded on first start
# open http://localhost:8080

docker compose run --rm station --finger 4 --lecture-seconds 20   # simulate a maths lecture
docker compose down                  # stop (add -v to delete the database too)
```

Set `DB_PASSWORD` in `.env` (or the shell) before the first start if you want a different password.
The Docker setup hasn't been tested yet; please report anything that fails.

---

## 3. The station on a Raspberry Pi

### Mounting and wiring

See the [classroom picture](images/classroom-setup.svg): the **fingerprint sensor and LCD** go outside the classroom door at hand height, the **camera** on the front wall above the board so it sees every row, and the **Raspberry Pi** in a box on the wall between them.

See the [wiring diagram](images/hardware-wiring.svg).

| Part | Connect to |
| --- | --- |
| Fingerprint sensor | USB-to-serial adapter: sensor TX → adapter RX, sensor RX → adapter TX, 5V (or 3.3V, check your sensor), GND. Plug into a USB port; it appears as `/dev/ttyUSB0`. |
| 16×2 LCD with PCF8574 I2C backpack | VCC → pin 2 (5V), GND → pin 6, SDA → pin 3 (GPIO2), SCL → pin 5 (GPIO3). Enable I2C in `raspi-config`. `i2cdetect -y 1` should show `27` (or `3f`; set `LCD_I2C_ADDRESS`). |
| Camera | Pi camera on the CSI connector, or a USB webcam. |

### Software

```bash
sudo apt install -y python3-venv python3-dev cmake build-essential libopenblas-dev i2c-tools
git clone https://github.com/MayankP2811/smart-attendance-system.git
cd smart-attendance-system
python3 -m venv .venv
.venv/bin/pip install -r requirements-hardware.txt    # dlib is compiled here: this can take 30-60 minutes
cp .env.example .env                                  # DB_HOST = the computer running MySQL
```

The station talks to MySQL over the network. On the database server, allow the Pi's user to connect from the Pi's address, for example `CREATE USER 'attendance_app'@'192.168.1.%' ...`, and make MySQL listen on the network (`bind-address`).

**Camera note:** OpenCV reads the camera through V4L2. A USB webcam works directly. A CSI camera on Raspberry Pi OS Bookworm uses the libcamera stack; if `CAMERA_INDEX=0` gives no picture, start the station with `libcamerify .venv/bin/python -m device.main`, or use a USB webcam.

### Enroll teachers' fingers

Each sensor slot belongs to one subject. A teacher with two subjects enrolls one finger for each.

```bash
.venv/bin/python -m device.tools.fingerprint_admin enroll 4 --subject maths
.venv/bin/python -m device.tools.fingerprint_admin list
.venv/bin/python -m device.tools.fingerprint_admin test
```

### Face recognition

1. Collect photos of each student **with their consent**: one or more clear, front-facing photos per student, one face per photo. Name them by roll number:

   ```text
   dataset/
     TE01.jpg
     TE02/
       front.jpg
       left.jpg
   ```

2. Build the known-faces file (`device/data/encodings.npz`; both folders are git-ignored):

   ```bash
   .venv/bin/python -m device.tools.build_encodings dataset
   ```

   Photos with no face or with two faces are skipped with a warning.

3. Try it on a laptop with some classroom photos before going to the Pi:

   ```bash
   .venv/bin/pip install -r requirements-face.txt
   .venv/bin/python -m device.main --mock --finger 4 --images path/to/classroom_photos --lecture-seconds 30
   ```

   With `SAVE_CAPTURES=1`, each analysed photo is saved in `device/captures/` with a box and roll number on every face.

**Tuning** (in `.env`): `FACE_TOLERANCE` (0.5 by default; lower = stricter, fewer wrong matches), `FACE_UPSAMPLE` (2 finds smaller, farther faces but is slower), `CAPTURE_COUNT` (photos per lecture, 6) and `MIN_PRESENCE` (share of the photos a student must be in to be present, 0.6).

### Start the station

```bash
.venv/bin/python -m device.main
```

To start it at boot, create `/etc/systemd/system/attendance.service`:

```ini
[Unit]
Description=Smart Attendance station
After=network-online.target
Wants=network-online.target

[Service]
User=pi
WorkingDirectory=/home/pi/smart-attendance-system
ExecStart=/home/pi/smart-attendance-system/.venv/bin/python -m device.main
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

then `sudo systemctl enable --now attendance`. Use the [Pi test checklist](pi-test-checklist.md) the first time.

### Excel export

```bash
.venv/bin/python -m device.tools.export_excel 2024-01-15 -o reports/
```

Writes `reports/attendance_2024-01-15.xlsx` with one sheet per subject (roll no, name, subject, date, day, time, photos seen in, status). Faculty can also download a CSV per subject from the website.

[Back to README](../README.md)
