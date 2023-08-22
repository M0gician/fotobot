import math
from fractions import Fraction
from PIL import Image, ExifTags, IptcImagePlugin
import logging
import math
from datetime import datetime
from enum import IntEnum
from src.exifutils.exifworker import ExifWorker

class PillowWorker(ExifWorker):

    @staticmethod
    def float2frac(f_value: float) -> str:
        if f_value >= 1.0:
            return str(f_value)
        
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

    @staticmethod  
    def convert_to_degrees(value: (int, int, int)) -> float:
        """Helper function to convert the GPS coordinates stored in the EXIF to degrees in float format"""
        degrees = value[0]
        minutes = value[1] / 60.0
        seconds = value[2] / 3600.0

        return degrees + minutes + seconds

    def __init__(self, img_path: str) -> None:
        with Image.open(img_path) as img:
            self.img = img
            self.width, self.height = img.size
            self.exif = {
                **img.getexif(),
                **img.getexif().get_ifd(ExifTags.Base.ExifOffset)
            }
            self.iptc = {}

            gps_info = img.getexif().get_ifd(ExifTags.Base.GPSInfo)
            iptc = IptcImagePlugin.getiptcinfo(img)
            if gps_info:
                self.exif |= {**gps_info}
            if iptc:
                self.iptc = {**iptc}
    
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
                subtype = subtype.replace('_2', ' II', 1)
            return f"Nikon {subtype}"
        elif cam_make.startswith("sony"):
            subtype = cam_model
            if cam_model.startswith("ILCE-"):
                subtype = cam_model[5:]
            # Add alpha symbol to Sony Models
            return f"Sony \u03B1{subtype}"
        elif cam_make.startswith("canon"):
            if cam_model[-2:] == "m2":
                cam_model = cam_model[:-2] + ' Mark II'
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
        lens_make = self.get_tag_with_log(ExifTags.Base.LensMake).lower()
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
        return f"{int(float(focal_length))}mm" if focal_length != "" else "Unknown Focal Length"
    
    def get_focal_length_in_35mm(self) -> str:
        focal_length_35mm = self.get_tag_with_log(ExifTags.Base.FocalLengthIn35mmFilm)
        return f"{focal_length_35mm}mm" if focal_length_35mm != "" else "Unknown Focal Length in 35mm format"

    def get_aperture(self) -> str:
        aperture = self.get_tag_with_log(ExifTags.Base.FNumber)
        return f"f/{aperture}" if aperture else "Unknown Aperture"

    def get_shutter_speed(self) -> str:
        shutter_speed = self.get_tag_with_log(ExifTags.Base.ExposureTime)
        return f"{self.float2frac(float(shutter_speed))}s" if shutter_speed != "" else "Unknown Shutter Speed"

    def get_iso(self) -> str:
        iso = self.get_tag_with_log(ExifTags.Base.ISOSpeedRatings)
        return f"ISO {iso}" if iso != "" else "Unknown ISO"

    def get_exposure_compensation(self) -> str:
        exposure_comp = self.get_tag_with_log(ExifTags.Base.ExposureBiasValue)
        return f"{float(exposure_comp):.2f} EV" if exposure_comp != "" else "Unknown Exposure Compensation"

    def get_datetime(self) -> str:
        date_time = self.get_tag_with_log(ExifTags.Base.DateTimeOriginal)
        if date_time:
            date_time_obj = datetime.strptime(date_time, '%Y:%m:%d %H:%M:%S')
            return str(date_time_obj)
        return "Unknown DateTime Original"
    
    def get_metering_mode(self) -> str:
        mode = self.get_tag_with_log(ExifTags.Base.MeteringMode)
        return str(mode) if mode else "Unknown Metering Mode"
    
    def get_orientation(self) -> int:
        orientation = self.get_tag_with_log(ExifTags.Base.Orientation)
        return int(orientation) if orientation else 1
    
    def get_image_dimensions(self) -> str:
        if self.width and self.height:
            return f"{self.width} x {self.height}"
        return "Unknown Image Dimensions"
    
    def get_bits_per_sample(self) -> str:
        bits_per_sample = self.get_tag_with_log(ExifTags.Base.BitsPerSample)
        return f"{bits_per_sample} bit" if bits_per_sample else "Unknown Bit"
        
    def get_author(self) -> str:
        author = self.get_tag_with_log(ExifTags.Base.Artist)
        if not author and self.iptc and (2, 80) in self.iptc:
            author = self.iptc[(2, 80)].decode('utf-8', errors='replace')
        return author if author else "Unknown Photographer"
    
    def get_title(self) -> str:
        if self.iptc and (2, 5) in self.iptc:
            return self.iptc[(2, 5)].decode('utf-8', errors='replace')
        return ""
    
    def get_country(self) -> str:
        country = "Unknown Country"
        code = "Unknown Code"
        if self.iptc and (2, 101) in self.iptc:
           country = self.iptc[(2, 101)].decode('utf-8', errors='replace')
        if self.iptc and (2, 100) in self.iptc:
           code = self.iptc[(2, 100)].decode('utf-8', errors='replace')
        
        return f"{country}, {code}"
    
    def get_location(self) -> str:
        city = "Unknown City"
        province = "Unknown Province or State"
        if self.iptc and (2, 90) in self.iptc:
            city = self.iptc[(2, 90)].decode('utf-8', errors='replace')
        if self.iptc and (2, 95) in self.iptc:
            province = self.iptc[(2, 95)].decode('utf-8', errors='replace')
        
        return f"{province}, {city}" 
    
    def get_keywords(self) -> str:
        keywords = []
        if self.iptc and (2, 25) in self.iptc:
            for keyword in self.iptc[(2, 25)]:
                keywords.append(keyword.decode('utf-8', errors='replace'))

        return ", ".join(keywords) if keywords else "Unknown Keywords"
    
    def get_f_latitude_longitude(self) -> (float, float):
        lat = None
        lon = None

        gps_latitude = self.get_tag_with_log(ExifTags.GPS.GPSLatitude)
        gps_latitude_ref = self.get_tag_with_log(ExifTags.GPS.GPSLatitudeRef)
        gps_longitude = self.get_tag_with_log(ExifTags.GPS.GPSLongitude)
        gps_longitude_ref = self.get_tag_with_log(ExifTags.GPS.GPSLongitudeRef)

        if gps_latitude and gps_latitude_ref and gps_longitude and gps_longitude_ref:
            lat = self.convert_to_degrees(gps_latitude)
            if gps_latitude_ref != "N":                     
                lat = 0 - lat

            lon = self.convert_to_degrees(gps_longitude)
            if gps_longitude_ref != "E":
                lon = 0 - lon
        
        return lat, lon
    
    def get_latitude_longitude(self) -> str:
        lat = None
        lon = None
        gps_latitude_ref = self.get_tag_with_log(ExifTags.GPS.GPSLatitudeRef)
        gps_longitude_ref = self.get_tag_with_log(ExifTags.GPS.GPSLongitudeRef)

        lat, lon = self.get_f_latitude_longitude()
        if lat and lon and not math.isnan(lat) and not math.isnan(lon):
            return f"{lat:.6f}° {gps_latitude_ref}, {lon:.6f}° {gps_longitude_ref}"
        return "Unknown GPS Coordinate"
