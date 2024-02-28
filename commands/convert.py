import click
import cv2
import logging
from pathlib import Path
import svg
import yaml
from lib import helpers
import math

log = logging.getLogger(__name__)
@click.command("convert")
@click.argument("image_filepath")
@click.option('-c', '--config-filepath', default=Path().resolve() / "config.yaml")
@click.option('-s', '--scaling-factor', default=0)
@click.option('--no-dugout', is_flag=True)
@click.version_option("0.1.0", prog_name="tool trace")
def convert(image_filepath, config_filepath, scaling_factor, no_dugout):
  filepath = Path(image_filepath)
  if not filepath.is_file():
    log.error("{} doesn't exist".format(image_filepath))
    raise SystemExit(1)
  if scaling_factor:
    scale_factor = scaling_factor
  else:
    scale_factor = helpers.get_scaling_factor_from_config_file(config_filepath)

  bw_image = helpers.convert_image_to_high_contrast(filepath)
  contours, hierarchy = cv2.findContours(bw_image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
  contours = sorted(contours, key=cv2.contourArea, reverse=True)
  log.info("Extracted contours from image")

  tool_contour = helpers.force_perpendicular(helpers.smooth_contour(contours[1]))

  PX_TO_FUSION_MM = 3.8 #draw something as pixel, then scale by this
  CAM_PX_TO_FUSION_MM = scale_factor
  GRIDFINITY_DIMENSION = 42

  scaled_tool_contour = helpers.scale_contour(tool_contour, scale_factor)
  plate = helpers.generate_svg(scaled_tool_contour, scale_factor, no_dugout)
  helpers.write_svg_to_file("images/svg/{}.svg".format(filepath.stem), plate)
