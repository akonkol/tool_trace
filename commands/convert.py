import click
import cv2
import logging
from pathlib import Path
import svg
import yaml
from lib import helpers
import math

log = logging.getLogger(__name__)

pixel_mm_ratio=None

@click.command("convert")
@click.argument("image_filepath")
@click.option('-s', '--scaling-factor', default=0)
@click.option('--no-dugout', is_flag=True)
@click.version_option("0.1.0", prog_name="tool trace")
def convert(image_filepath, scaling_factor, no_dugout):
  filepath = Path(image_filepath)
  if not filepath.is_file():
    log.error("{} doesn't exist".format(image_filepath))
    raise SystemExit(1)
  if scaling_factor:
    scale_factor = scaling_factor
  # else:
  #   scale_factor = helpers.get_scaling_factor_from_config_file(config_filepath)

  bw_image = helpers.convert_image_to_high_contrast(filepath)

  aruco_perimeter = helpers.get_aruco_perimeter(bw_image)
  KNOWN_DIMENSION = 40 # mm of one side of square
  pixel_mm_ratio = aruco_perimeter / (KNOWN_DIMENSION * 4)
  aruco_dimension_mm =  (aruco_perimeter / 4 ) / pixel_mm_ratio

  contours, hiearchy = cv2.findContours(bw_image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
  contours = sorted(contours, key=cv2.contourArea, reverse=True)

  aruco_contour_index = helpers.get_aruco_contour_index(contours, aruco_dimension_mm, pixel_mm_ratio)
  filtered_contours = helpers.filter_contours(contours, aruco_contour_index, pixel_mm_ratio)
  svg_contours = helpers.create_svgs_from_contours(filtered_contours)
  print(len(svg_contours))

  # tool_contour = helpers.force_perpendicular(bw_image, helpers.smooth_contour(contours[1]))
  tool_contour = filtered_contours[0]
  scale_factor = 0
  rect = cv2.minAreaRect(filtered_contours[0])
  center, size, angle = rect
  print(size)

  svg = helpers.create_svg_from_elements(svg_contours, 2000, 2000)
  helpers.write_svg_to_file('sup.svg', svg)
  # scaled_tool_contour = helpers.scale_contour(tool_contour, scale_factor)
  # plate = helpers.generate_svg(scaled_tool_contour, scale_factor, no_dugout)
  # helpers.write_svg_to_file("images/svg/{}.svg".format(filepath.stem), plate)
