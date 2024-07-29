import click
import cv2
import logging
from pathlib import Path
import svg
import yaml
from lib import helpers

log = logging.getLogger("Aruco Detection")

ARUCO_ID=7
ARUCO_DICT=cv2.aruco.DICT_4X4_50
pixel_mm_ratio=None

def detect_aruco_marker(image, id=ARUCO_ID):
  aruco_dict = cv2.aruco.getPredefinedDictionary(ARUCO_DICT)
  aruco_parameters = cv2.aruco.DetectorParameters()
  detector = cv2.aruco.ArucoDetector(aruco_dict, aruco_parameters)
  (corners, ids, rejected) = detector.detectMarkers(image)
  marker_found=False
  # We standardized on using a single marker with id 7
  if len(ids) == 1  and ids[0] == ARUCO_ID:
    log.info("Marker detected")
    marker_found = True
  elif len(rejected) > 0:
    log.warning("Potential marker rejected")
  else:
    raise Exception("No calibration object detected")
  return marker_found, corners

@click.command("aruco")
@click.argument("filename")
@click.version_option("0.1.0", prog_name="Aruco")
def aruco(filename ):
  filepath = Path(filename)
  if not filepath.is_file():
    log.error("{} doesn't exist".format(filepath))
    raise SystemExit(1)

  ref_image = helpers.convert_image_to_high_contrast(filepath)
  exists, corners = detect_aruco_marker(ref_image)

  aruco_perimeter = cv2.arcLength(corners[0], True)
  pixel_mm_ratio = aruco_perimeter / (100 * 4)
