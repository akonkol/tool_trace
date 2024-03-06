import cv2
from pathlib import Path
import click
import logging
import numpy

log = logging.getLogger(__name__)

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

def convert_image_to_high_contrast(filename):
  image = cv2.imread(str(filename), cv2.IMREAD_GRAYSCALE)
  alpha = 1.5 # Contrast control
  beta = 10 # Brightness control
  ret,thresh = cv2.threshold(image, 128, 255, cv2.THRESH_BINARY)
  adjusted = cv2.convertScaleAbs(thresh, alpha=alpha, beta=beta)
  ret,thresh2 = cv2.threshold(adjusted, 128, 255, cv2.THRESH_BINARY)
  log.info("Adjusted image contrast of {}".format(str(filename)))
  return thresh2

@click.command("convert")
@click.argument("image_filepath")
@click.version_option("0.1.0", prog_name="tool trace")
def convert(image_filepath):
  bw_image = convert_image_to_high_contrast(image_filepath)
  contours, hierarchy = cv2.findContours(bw_image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
  contours = sorted(contours, key=cv2.contourArea, reverse=True)
  log.info("Extracted contours from image")
  shape_contour = contours[1]

  rect = cv2.minAreaRect(shape_contour)
  center, size, angle = rect
  width = size[0]
  height = size[1]
  box = cv2.boxPoints(rect)
  box = numpy.intp(box)

  cv2.drawContours(bw_image,[box],0,(0,0,255),2)
  log.info("size: {} x {} angle: {}".format(width, height, angle))
  if width > height:
      log.info("width is the long side")
  else:
      log.info("height is the long side")
  font = cv2.FONT_HERSHEY_SIMPLEX
  font_scale=4
  org = (500, 500)
  color = (0,0,0)
  thickness=20

  cv2.putText(bw_image, "Original angle: {} ".format(angle) ,org, font, font_scale, color, thickness, cv2.LINE_AA)
  log.info("90 - {} = {}".format(angle, 90 - angle))
  correction_angle = 90 - angle
  log.info("Rotating contour {} degrees".format(correction_angle))
  r_contour = rotate_contour(shape_contour, correction_angle)
  x,y,w,h = cv2.boundingRect(r_contour)
  if h > w:
      log.info("Height is longer than width, good position")
      cv2.drawContours(bw_image,[r_contour],0,(0,0,255),2)
  else:
      log.info("Width is longer than height, bad position")
      #flip this baddy
      proper_rotation = rotate_contour(r_contour, 90)
      cv2.drawContours(bw_image,[proper_rotation],0,(0,0,255),2)


  # for i in range(90):
  #   rotated_rect = cv2.RotatedRect(center, size, angle + i)
  #   r_box = cv2.boxPoints(rotated_rect)
  #   r_box = numpy.intp(r_box)
  #
  #   cv2.drawContours(bw_image,[r_box],0,(0,0,255),2)
  #   # cv2.putText(bw_image, "angle: {} ".format(angle +i) ,org, font, font_scale, color, thickness, cv2.LINE_AA)
  #   log.info("angle: {} ".format(angle +i))
  cv2.imshow("metadata", bw_image)
  cv2.waitKey(5000)


if __name__ == "__main__":
  logging.basicConfig(
     level=logging.INFO,
     format='%(message)s',
  )
  convert()
