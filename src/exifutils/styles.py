from enum import Enum

class Style(Enum):
    DEFAULT = 1
    FULL = 2
    PRETTY = 3

DEFAULT_STYLE = """

——————————
Camera: $camera
Lens: $lens
$focal_length, $aperture, $shutter_speed, $iso
"""

FULL_INFO_STYLE = """
```
Camera               : $camera
Lens                 : $lens
Focal Length         : $focal_length
Aperture             : $aperture
Shutter Speed        : $shutter_speed
ISO                  : $iso
Exposure Compensation: $exposure_compensation
DateTime Original    : $datetime
```
"""

PRETTY_STYLE = """
💭: 
——————————
📸: $camera / $lens
📝: $focal_length, $aperture, $shutter_speed, $iso
📅: $datetime
"""