from enum import Enum

class Style(Enum):
    DEFAULT = 1
    FULL = 2
    PRETTY = 3

DEFAULT_STYLE = """
$title
——————————
Camera: $camera
Lens: $lens
$focal_length ($focal_length_in_35mm equiv), $aperture, $shutter_speed, $iso
"""

DEFAULT_STYLE_FF = """
$title
——————————
Camera: $camera
Lens: $lens
$focal_length, $aperture, $shutter_speed, $iso
"""

FULL_INFO_STYLE = """<pre>
[Camera]
    $camera
[Lens]
    $lens
[Focal Length]
    $focal_length
[Focal Length in 35mm]
    $focal_length_in_35mm
[Aperture]
    $aperture
[Shutter Speed]
    $shutter_speed
[ISO]
    $iso
[Exposure Compensation]
    $exposure_compensation
[Metering Mode]
    $metering_mode
[Image Dimensions]
    $image_dimensions
[Author]
    $author
[Title]
    $title
[Location]
    $location
    $country
[GPS Coordinates]
    $gps_coordinates
[Keywords]
    $keywords
[DateTime Original]
    $datetime </pre>
"""

PRETTY_STYLE = """
💭: $title
——————————
📸: $camera / $lens
📝: $focal_length_in_35mm, $aperture, $shutter_speed, $iso
📅: $datetime
"""

PRETTY_STYLE_FF = """
💭: $title
——————————
📸: $camera / $lens
📝: $focal_length, $aperture, $shutter_speed, $iso
📅: $datetime
"""