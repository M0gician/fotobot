import math
from fractions import Fraction
from PIL import Image, ExifTags
import logging
from string import Template

DEFAULT_STYLE = """
——————————
Camera: $camera
Lens: $lens
$focal_length, $aperture, $shutter_speed, $iso, $exposure_compensation
"""


class ExifWorker:

    @staticmethod
    def float2frac(f_value: float) -> str:
        if math.isclose(f_value, 0.0):
            return "0"
        elif math.isclose(f_value, 0.33):
            return "1/3"
        elif math.isclose(f_value, -0.33):
            return "-1/3"
        elif math.isclose(f_value, 0.67):
            return "2/3"
        elif math.isclose(f_value, -0.67):
            return "-2/3"

        frac = Fraction(f_value).limit_denominator(64000)
        numerator, denominator = frac.numerator, frac.denominator
        return f"{numerator}/{denominator}" if numerator != 0 else "0"

    def __init__(self, img: Image) -> None:
        self.img = img
        self.exif = {**img.getexif(), **img.getexif().get_ifd(ExifTags.Base.ExifOffset)}

    def get_camera(self) -> str:
        cam_make, cam_model = "", ""
        if ExifTags.Base.Make not in self.exif:
            logging.warning("No camera make found")
        else:
            cam_make = self.exif[ExifTags.Base.Make].lower()

        if ExifTags.Base.Model not in self.exif:
            logging.warning("No camera model found")
        else:
            cam_model = self.exif[ExifTags.Base.Model]

        if cam_make.startswith("nikon"):
            subtype = cam_model
            if cam_model.startswith("NIKON"):
                subtype = cam_model[6:]
                # Replace Z with DOUBLE-STRUCK CAPITAL Z
                subtype = f"\u2124{subtype[1:]}" if subtype[0] == 'Z' else subtype
            return f"Nikon {subtype}"
        elif cam_make.startswith("sony"):
            subtype = cam_model
            if cam_model.startswith("ILCE-"):
                subtype = cam_model[5:]
            # Add alpha symbol to Sony Models
            return f"Sony \u03B1{subtype}"
        elif cam_make.startswith("canon"):
            return cam_model
        elif cam_make.startswith("fujifilm"):
            return f"Fujifilm {cam_model}"
        else:
            logging.warning("Unknown camera make, return as is")
            return f"{cam_make} {cam_model}"

    def get_lens(self) -> str:
        lens_make, lens_model = "", ""
        if ExifTags.Base.LensMake not in self.exif:
            logging.warning("No lens make found")
        else:
            lens_make = self.exif[ExifTags.Base.LensMake].lower()

        if ExifTags.Base.LensModel not in self.exif:
            logging.warning("No lens model found")
        else:
            lens_model = self.exif[ExifTags.Base.LensModel]

        if lens_make.startswith("nikon"):
            subtype = lens_model
            if lens_model.startswith("NIKKOR"):
                subtype = lens_model[7:]
                # Replace Z with DOUBLE-STRUCK CAPITAL Z
                subtype = f"\u2124{subtype[1:]}" if subtype[0] == 'Z' else subtype
            return f"Nikkor {subtype}"
        elif lens_make.startswith("sony") or lens_model[:2] in ('FE', 'E '):
            return f"Sony {lens_model}"
        elif lens_make.startswith("canon") or lens_model[:2] in ('EF', 'RF'):
            if lens_model[:2] in ('EF', 'RF'):
                # EF/RF for full frame, EF-S/EF-M/RF-S for crop
                if lens_model[2] == '-':
                    lens_model = f"{lens_model[:4]} {lens_model[4:]}"
                else:
                    lens_model = f"{lens_model[:2]} {lens_model[2:]}"
            return f"Canon {lens_model}"
        elif lens_make.startswith("fujifilm"):
            if lens_model[:2] in ('XF', 'GF'):
                # Separate mount info from focal length
                lens_model = f"{lens_model[:2]} {lens_model[2:]}"
                # Separate focal length and aperture info
                lens_model = lens_model.replace('mm', 'mm ', 1)
            return f"Fujinon {lens_model}"
        else:
            logging.warning("Unknown lens make, return as is")
            return f"{lens_make} {lens_model}"

    def get_focal_length(self) -> str:
        if ExifTags.Base.FocalLength not in self.exif:
            logging.warning("No focal length found")
            return ""
        else:
            return f"{int(float(self.exif[ExifTags.Base.FocalLength]))}mm"

    def get_aperture(self) -> str:
        if ExifTags.Base.FNumber not in self.exif:
            logging.warning("No f-number found")
            return ""
        else:
            return f"f/{self.exif[ExifTags.Base.FNumber]}"

    def get_shutter_speed(self) -> str:
        if ExifTags.Base.ExposureTime not in self.exif:
            logging.warning("No shutter speed found")
            return ""
        else:
            return f"{self.float2frac(float(self.exif[ExifTags.Base.ExposureTime]))}s"

    def get_iso(self) -> str:
        if ExifTags.Base.ISOSpeedRatings not in self.exif:
            logging.warning("No ISO found")
            return ""
        else:
            return f"ISO {self.exif[ExifTags.Base.ISOSpeedRatings]}"

    def get_exposure_compenstation(self) -> str:
        if ExifTags.Base.ExposureBiasValue not in self.exif:
            logging.warning("No exposure compensation found")
            return ""
        else:
            return f"{self.float2frac(float(self.exif[ExifTags.Base.ExposureBiasValue]))} EV"

    def get_datetime(self) -> str:
        if ExifTags.Base.DateTimeOriginal not in self.exif:
            logging.warning("No datetime found")
            return ""
        else:
            return self.exif[ExifTags.Base.DateTimeOriginal]

    def get_description(self, style=DEFAULT_STYLE) -> str:
        mapping = {
            'camera': self.get_camera(),
            'lens': self.get_lens(),
            'focal_length': self.get_focal_length(),
            'aperture': self.get_aperture(),
            'shutter_speed': self.get_shutter_speed(),
            'iso': self.get_iso(),
            'exposure_compensation': self.get_exposure_compenstation(),
            'datetime': self.get_datetime()
        }

        try:
            template = Template(style)
            return template.safe_substitute(mapping)
        except KeyError as e:
            logging.error(f"Invalid style: {e}")
            return ""
