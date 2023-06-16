import math
from fractions import Fraction
from PIL import Image, ExifTags
import logging
from string import Template
from enum import IntEnum

from src.exifutils.styles import (
    DEFAULT_STYLE
)


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

    def __init__(self, img_path: str) -> None:
        with Image.open(img_path) as img:
            self.img = img
            self.exif = {**img.getexif(), **img.getexif().get_ifd(ExifTags.Base.ExifOffset)}
    
    def get_tag_with_log(self, tag: IntEnum) -> str:
        tag_info = self.exif.get(tag, '')
        if tag_info == '':
            logging.warning(f"No {tag.name} found")
        return tag_info

    def get_camera(self) -> str:
        cam_make = self.get_tag_with_log(ExifTags.Base.Make).lower()
        cam_model = self.get_tag_with_log(ExifTags.Base.Model)

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
            if cam_make or cam_model:
                cam_make = cam_make if cam_make else "Unknown Make"
                cam_model = cam_model if cam_model else "Unknown Model"
                return f"{cam_make} {cam_model}"
            else:
                return "Unknown Camera"

    def get_lens(self) -> str:
        lens_make = self.get_tag_with_log(ExifTags.Base.LensMake)
        lens_model = self.get_tag_with_log(ExifTags.Base.LensModel)
    
        if lens_make.startswith("nikon"):
            lens = lens_model
            if lens_model.startswith("NIKKOR"):
                lens = lens_model[7:]
                # Replace Z with DOUBLE-STRUCK CAPITAL Z
                lens = f"\u2124{lens[1:]}" if lens[0] == 'Z' else lens
            return f"Nikkor {lens}"
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
            if lens_make or lens_model:
                lens_make = lens_make if lens_make else "Unknown Make"
                lens_model = lens_model if lens_model else "Unknown Model"
                return f"{lens_make} {lens_model}"
            else:
                return "Unknown Lens"

    def get_focal_length(self) -> str:
        focal_length = self.get_tag_with_log(ExifTags.Base.FocalLength)
        return f"{int(float(focal_length))}mm" if focal_length != "" else ""

    def get_aperture(self) -> str:
        aperture = self.get_tag_with_log(ExifTags.Base.FNumber)
        return f"f/{aperture}" if aperture else ""

    def get_shutter_speed(self) -> str:
        shutter_speed = self.get_tag_with_log(ExifTags.Base.ExposureTime)
        return f"{self.float2frac(float(shutter_speed))}s" if shutter_speed != "" else ""

    def get_iso(self) -> str:
        iso = self.get_tag_with_log(ExifTags.Base.ISOSpeedRatings)
        return f"ISO {iso}" if iso != "" else ""

    def get_exposure_compensation(self) -> str:
        exposure_comp = self.get_tag_with_log(ExifTags.Base.ExposureBiasValue)
        return f"{float(exposure_comp):.2f} EV" if exposure_comp != "" else ""

    def get_datetime(self) -> str:
        date_time = self.get_tag_with_log(ExifTags.Base.DateTimeOriginal)
        return date_time if date_time != "" else ""

    def get_description(self, style=DEFAULT_STYLE) -> str:
        mapping = {
            'camera': self.get_camera(),
            'lens': self.get_lens(),
            'focal_length': self.get_focal_length(),
            'aperture': self.get_aperture(),
            'shutter_speed': self.get_shutter_speed(),
            'iso': self.get_iso(),
            'exposure_compensation': self.get_exposure_compensation(),
            'datetime': self.get_datetime()
        }
        
        try:
            template = Template(style)
            return template.safe_substitute(mapping)
        except KeyError as e:
            logging.error(f"Invalid style: {e}")
            return ""
