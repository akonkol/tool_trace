# tool_trace
![photo-to-svg](https://github.com/akonkol/tool_trace/blob/main/images/docs/photo-to-svg.gif?raw=true)

Take pictures of your tools and create an outline in svg.

For this to work, you will need to make sure that you take quality pictures with adequate lighting
from a consistent distance.

I use a phone stand and a light panel


## Calibration
The distance between the camera and tool may very from person to person. To adjust for this 
variance there is a simple calibration process.

1) Take a picture of a 10mm x 10mm square
2) Run the calibrate command and follow the prompts
3) As long as you never change the following you should never have to calibrate again:
  - distance between tool and camera 
  - camera/phone 

```
python3 tool_trace.py calibrate  /path/to/square.jpg

Adjusted image contrast of square.jpg
Smoothing/reducing contour points
Writing SVG to: images/svg/square-unscaled.svg
Start a new fusion sketch and import images/svg/square-unscaled.svg
Using the Inspect > Measure tool, measure the length of one of the sides of the square
Enter your value: 38.2
149.41903686523438 pixels in this program is 38.2 mm in fusion
Our contours should be scaled down by 0.2617801047120419%
Updating scaling factor to 0.2617801047120419 in config.yaml
Producing fusion scale svg
Writing SVG to: images/svg/square-scaled.svg
```

## Convert Image to SVG
1) Take a picture of the tool
2) Run the convert command
3) Import resulting svg file into Fusion 360 (or whatever you use)

```
python3 tool_trace.py convert images/src/micro-cutters.jpg
Adjusted image contrast of images/src/micro-cutters.jpg
Extracted contours from image
Smoothing/reducing contour points
Rotating contour by: -1.6011782884597778
Generated dugout
Writing SVG to: images/svg/micro-cutters.svg
```

## I don't any of the extra generated stuff (dugouts) 

![photo-to-svg-no-dugout](https://github.com/akonkol/tool_trace/blob/main/images/docs/micro-cutters-no-dugout.jpg?raw=true)
```
python3 tool_trace.py convert  images/src/micro-cutters.jpg --no-dugout
```


## Example workflow
1) Take picture of tool in phone stand
2) Share photo to host computer via AirDrop
3) Run `./grab_last_image_upload.sh` to retrieve the last image downloaded
4) Give the tool a name
5) Convert to svg
6) Create new Fusion 360 Design
7) Generate a gridfinity bin using [this](https://apps.autodesk.com/FUSION/en/Detail/Index?id=7197558650811789&appLang=en&os=Mac) generator
8) Import svg onto the face of the bin
9) Offset the tool contour by 1.5mm
10) Extrude dugout and tool contour into bin
11) 3D Print
