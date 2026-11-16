# Third-party credits and licensing

| Component | Used for | License |
| --- | --- | --- |
| [face_recognition](https://github.com/ageitgey/face_recognition) by Adam Geitgey | Face detection and 128-number face embeddings (installed with pip, not copied here) | MIT |
| [dlib](http://dlib.net/) by Davis King | HOG face detector and the face-embedding model behind face_recognition (installed with pip) | Boost Software License |
| [OpenCV](https://opencv.org/) | Camera capture and drawing boxes on photos (installed with pip) | Apache-2.0 |
| [Adafruit CircuitPython Fingerprint](https://github.com/adafruit/Adafruit_CircuitPython_Fingerprint) | Fingerprint sensor driver (installed with pip). `device/hardware.py` and `device/tools/fingerprint_admin.py` follow the enroll / search steps of Adafruit's example. | MIT |
| [RPLCD](https://github.com/dbrgn/RPLCD) | 16x2 I2C LCD driver (installed with pip) | MIT |
| [the-raspberry-pi-guy/lcd](https://github.com/the-raspberry-pi-guy/lcd) | Alternative LCD driver, used if RPLCD isn't installed. Not copied into this repository. | See that project |
| [mysql-connector-python](https://dev.mysql.com/doc/connector-python/en/) | Database access from the station (installed with pip) | GPL-2.0 with the FOSS exception |
| [openpyxl](https://openpyxl.readthedocs.io/) | Excel export (installed with pip) | MIT |
| [Chart.js](https://www.chartjs.org/) 4 (`web/assets/vendor/chart.umd.min.js`) | Analytics bar chart | MIT, see `web/assets/vendor/chart.js-LICENSE.md` |
| [Poppins](https://fonts.google.com/specimen/Poppins) font (`web/assets/fonts/`, via @fontsource) | Website typeface | SIL Open Font License 1.1 |
| [Material Icons Sharp](https://fonts.google.com/icons) (`web/assets/fonts/`, via the material-icons package) | Website icons | Apache-2.0 |

The chat and login pages follow the layout of free tutorial templates (CodingNepal's chat app and an
"animated login form"); their code here is written for this project. The illustrations, wave, avatar
and subject pictures are original SVG drawings made for this repository.

Each third-party component stays under its own license. This project's own code, documents and
images are under the MIT license in [LICENSE](LICENSE).
