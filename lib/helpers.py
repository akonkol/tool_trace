import cv2
import logging
import math
import numpy
from pathlib import Path
import svg
import yaml

log = logging.getLogger(__name__)

PX_TO_FUSION_MM = 3.8 #draw something as pixel, then scale by this
GRIDFINITY_DIMENSION = 42
STROKE_WIDTH=1

def convert_image_to_high_contrast(filename):
  image = cv2.imread(str(filename), cv2.IMREAD_GRAYSCALE)
  alpha = 1.5 # Contrast control
  beta = 10 # Brightness control
  ret,thresh = cv2.threshold(image, 128, 255, cv2.THRESH_BINARY)
  adjusted = cv2.convertScaleAbs(thresh, alpha=alpha, beta=beta)
  ret,thresh2 = cv2.threshold(adjusted, 128, 255, cv2.THRESH_BINARY)
  log.info("Adjusted image contrast of {}".format(str(filename)))
  return thresh2

def smooth_contour(contour):
  log.info("Smoothing/reducing contour points")
  peri = cv2.arcLength(contour, True)
  return cv2.approxPolyDP(contour, 0.00039999999999 * peri, True)

def write_svg_to_file(filepath, svg):
  with open(str(filepath), "w+") as f:
    log.info("Writing SVG to: {}".format(filepath))
    f.write(str(svg))

def force_perpendicular(contour):
  REF_ANGLE = 90
  rect = cv2.minAreaRect(contour)
  center, size, angle = rect
  box = cv2.boxPoints(rect)
  box = numpy.int0(box)

  log.debug("Original angle found: {}".format(angle))
  if size[0] < size[1]:
      adjustment_angle = 0 - angle
  else:
      adjustment_angle = REF_ANGLE - angle

  log.info("Rotating contour by: {}".format(adjustment_angle))
  return rotate_contour(contour, adjustment_angle)

def cart2pol(x, y):
  theta = numpy.arctan2(y, x)
  rho = numpy.hypot(x, y)
  return theta, rho

def pol2cart(theta, rho):
  x = rho * numpy.cos(theta)
  y = rho * numpy.sin(theta)
  return x, y

def rotate_contour(contour, angle):
  M = cv2.moments(contour)
  cx = int(M['m10']/M['m00'])
  cy = int(M['m01']/M['m00'])

  contour_norm = contour - [cx, cy]

  coordinates = contour_norm[:, 0, :]
  xs, ys = coordinates[:, 0], coordinates[:, 1]
  thetas, rhos = cart2pol(xs, ys)

  thetas = numpy.rad2deg(thetas)
  thetas = (thetas + angle) % 360
  thetas = numpy.deg2rad(thetas)

  xs, ys = pol2cart(thetas, rhos)

  contour_norm[:, 0, 0] = xs
  contour_norm[:, 0, 1] = ys

  contour_rotated = contour_norm + [cx, cy]
  contour_rotated = contour_rotated.astype(numpy.int32)

  return contour_rotated

def create_svg_from_contour(contour) -> svg.SVG:
  log.debug("Creating Path for contour")
  contour_points=[]
  for i in range(len(contour)):
      x, y = contour[i][0]
      if i == 0:
        contour_points.append(svg.M(x,y))
      else:
        contour_points.append(svg.L(x,y))
      if i == len(contour)-1:
        contour_points.append(svg.Z())
  cx, cy = find_center_coords(contour)
  return svg.Path(
      d= contour_points,
      fill="none",
      stroke="blue",
      stroke_width=STROKE_WIDTH,
  )

def create_svg_from_elements(elements, width, height):
  return svg.SVG(
      width=width,
      height=height,
      elements=elements
  )

def shift_origin(contour, x_offset=0, y_offset=0):
  x,y,w,h = cv2.boundingRect(contour)
  for coord in contour:
    coord[0][0] -= (x - x_offset)
    coord[0][1] -= (y - y_offset)
  return contour

def find_center_coords(contour):
  M = cv2.moments(contour)
  cX = int(M["m10"] / M["m00"])
  cY = int(M["m01"] / M["m00"])
  return cX, cY

def get_scaling_factor_from_config_file(filepath):
  with open(filepath, 'r') as stream:
          data_loaded = yaml.safe_load(stream)
  return data_loaded['scaling_factor']

def scale_contour(contour, scale):
    M = cv2.moments(contour)
    cx = int(M['m10']/M['m00'])
    cy = int(M['m01']/M['m00'])

    contour_norm = contour - [cx, cy]
    contour_scaled = contour_norm * scale
    contour_scaled = contour_scaled + [cx, cy]
    contour_scaled = contour_scaled.astype(numpy.int32)
    log.debug("Scaled contour by {}%".format(scale))
    return contour_scaled

def generate_svg(tool_contour, scale_factor, no_dugout):
  DUGOUT_MARGIN = 5
  tool_x,tool_y,tool_width, tool_height = cv2.boundingRect(tool_contour)

  width_gunits = math.ceil(tool_width * scale_factor / GRIDFINITY_DIMENSION)
  height_gunits = math.ceil(tool_height * scale_factor / GRIDFINITY_DIMENSION)

  perimeter_width = width_gunits * GRIDFINITY_DIMENSION
  perimeter_height = height_gunits * GRIDFINITY_DIMENSION
  log.info("Tool is {} x {} Gridfinity Units".format(width_gunits, height_gunits))
  log.debug("Perimeter {} x {}".format(perimeter_width, perimeter_height))
  log.debug("Tool {} x {}".format(tool_width, tool_height))

  centered_tool_x_position = (perimeter_width * PX_TO_FUSION_MM - tool_width) / 2
  centered_tool_y_position = (perimeter_height * PX_TO_FUSION_MM - tool_height) / 2
  log.debug("Centered {}, {}".format(centered_tool_x_position, centered_tool_y_position))

  centered_tool_contour = shift_origin(tool_contour, centered_tool_x_position , centered_tool_y_position)
  tool_svg = create_svg_from_contour(centered_tool_contour)

  perimeter = svg.Rect(
          x=0,
          y=0,
          width=perimeter_width,
          height=perimeter_height,
          rx=3.8,
          stroke="red",
          fill="transparent",
          stroke_width=STROKE_WIDTH,
          transform=[
            svg.Scale(PX_TO_FUSION_MM,PX_TO_FUSION_MM)
          ]
  )
  perimeter_center = svg.Circle(
          cx=perimeter_width / 2,
          cy=perimeter_height / 2,
          r=1,
          stroke="blue",
          fill="transparent",
          stroke_width=STROKE_WIDTH,
          transform=[
            svg.Scale(PX_TO_FUSION_MM,PX_TO_FUSION_MM)
          ]
  )
  log.debug("Plate: {} x {}".format(perimeter.width, perimeter.height))
  dugout_width = perimeter.width - (2 * DUGOUT_MARGIN)
  DUGOUT_HEIGHT = 55
  DUGOUT_RADIUS = 7
  dugout = svg.Rect(
          x=DUGOUT_MARGIN,
          y=perimeter.height - DUGOUT_HEIGHT - DUGOUT_MARGIN,
          width=dugout_width,
          height=DUGOUT_HEIGHT,
          rx=DUGOUT_RADIUS,
          stroke="green",
          fill="none",
          stroke_width=STROKE_WIDTH,
          transform=[
            svg.Scale(PX_TO_FUSION_MM,PX_TO_FUSION_MM)
          ]
  )

  if no_dugout:
    elements=[tool_svg]
  else:
    elements=[
        perimeter,
        perimeter_center,
        dugout,
        tool_svg,
    ]
    log.info("Generated dugout")

  plate = svg.SVG(
    width= width_gunits * GRIDFINITY_DIMENSION *  PX_TO_FUSION_MM + 10,
    height= height_gunits * GRIDFINITY_DIMENSION *  PX_TO_FUSION_MM + 10,
    elements=elements
  )
  return plate
