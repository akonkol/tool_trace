import click
import cv2
import logging
from pathlib import Path
import svg
import yaml
from lib import helpers

log = logging.getLogger("Calibration")

def create_svg_from_square(dimension, padding=10) -> svg.SVG:
  sq= svg.Rect(
     width = dimension,
     height = dimension,
     stroke="red",
     stroke_width=2,
     fill="transparent",
   )
  return svg.SVG(
      width=dimension + padding,
      height=dimension + padding,
      elements=[sq]
  )


def get_square_width(image):
  contours, hierarchy = cv2.findContours(image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
  contours = sorted(contours, key=cv2.contourArea, reverse=True)
  ref_contour = contours[1]
  ref_bounding_rect = cv2.minAreaRect(helpers.smooth_contour(ref_contour))
  center, size, angle = ref_bounding_rect
  return max(size[0], size[1]) # take the longer side and use that as the square dimension

@click.command("calibrate")
@click.argument("filename")
@click.option('-w', '--known-width', default=10)
@click.option('-o', '--output-config-file', default="config.yaml")
@click.option('-r', '--save-reference-svg', default=True)
@click.option('-s', '--save-scaled-reference-svg', default=True)
@click.version_option("0.1.0", prog_name="Calibrate")
def calibrate(filename, known_width, output_config_file, save_reference_svg, save_scaled_reference_svg):
  """ Given a picture of a square of a known dimension, produces the amount a svg needs to be scaled to have accurate dimensions when imported into Fusion 360

 For example: calibrate square.jpg

 Processing a picture of a 10mm square, this script it may say the object is 149 pixels wide.
 This same file imported as a SVG into Fusion 360 may have dimensions of 38.3 mm

 General steps taken:
 - Detect the square
 - Detect the boundaries of the square
 - Extract width of the detected object
 - Draw a square with the extracted width to a file
 - Import file into Fusion 360 and measure the width of the square
 - Input measurement
 - Output scaling factor
 """
  filepath = Path(filename)
  if not filepath.is_file():
    log.error("{} doesn't exist".format(filepath))
    raise SystemExit(1)

  ref_image = helpers.convert_image_to_high_contrast(filepath)
  sq_dimension = get_square_width(ref_image)
  sq = create_svg_from_square(sq_dimension)

  svg_filepath = Path('images/svg/{}-unscaled.svg'.format(filepath.stem))
  helpers.write_svg_to_file(svg_filepath, sq)

  # now get the scaling factor, and transform the rectangle
  print("Start a new fusion sketch and import {}".format(str(svg_filepath)))
  print("Using the Inspect > Measure tool, measure the length of one of the sides of the square")
  fusion_width = input("Enter your value: ")
  print("{} pixels in this program is {} mm in fusion".format(sq_dimension, fusion_width))
  scaling_factor = known_width / float(fusion_width)
  if scaling_factor < 1:
    print("Our contours should be scaled down by {}%".format(scaling_factor))
  else:
    print("Our contours should be scaled up by {}%".format(scaling_factor))

  log.info("Updating scaling factor to {} in {}".format(scaling_factor, output_config_file))
  if output_config_file:
    with open(output_config_file, 'w') as outfile:
        yaml.dump({'scaling_factor': scaling_factor}, outfile, default_flow_style=False)

  if save_scaled_reference_svg:
    log.info("Producing fusion scale svg")
    s_sq = create_svg_from_square(sq_dimension * scaling_factor)
    helpers.write_svg_to_file("images/svg/{}-scaled.svg".format(filepath.stem), s_sq)
