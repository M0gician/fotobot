import logging
import exiftool
import math
from collections import defaultdict
from datetime import datetime
from geopy.geocoders import Nominatim
from PIL import ExifTags

from fotobot.exif.exifworker import ExifWorker
from fotobot.exif.base import (
    convert_to_degrees,
    load_metadata,
    register_worker,
)

@register_worker("exiftool")
class ExifToolWorker(ExifWorker):

    def __init__(self, img_path: str) -> None:
        self.img_path = img_path
        self.width, self.height, self.exif, self.iptc = load_metadata(img_path)

        with exiftool.ExifToolHelper(common_args=None) as et:
            metadata = et.get_metadata(img_path, params=['-fast1'])
            if len(metadata) == 0:
                logging.error(f"Fail to parse file: {img_path}")
            else:
                self.exif |= metadata[0]
    
    def get_tag_with_log(self, tag: str) -> str:
        tag_info = self.exif.get(tag, '')
        if tag_info == '':
            logging.warning(f"No {tag} found")
        return tag_info
    
    def get_camera(self) -> str:
        cam_make = self.get_tag_with_log("Make").lower()
        cam_model = self.get_tag_with_log("Model")

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
            if cam_model.startswith("ILCE-") and not cam_model.startswith("ILCE-XQ"):
                subtype = f"\u03B1{cam_model[5:]}"
            # Add alpha symbol to Sony Models
            return f"Sony {subtype}"
        elif cam_make.startswith("canon"):
            if cam_model[-2:] == "m2":
                cam_model = cam_model[:-2] + ' Mark II'
            return cam_model
        elif cam_make.startswith("fujifilm"):
            return f"Fujifilm {cam_model}"
        else:
            logging.warning("Unknown camera make, return as is")
            if cam_make or cam_model:
                if cam_make and cam_model:
                    if cam_model.lower().startswith(cam_make):
                        return cam_model
                cam_make = cam_make if cam_make else "Unknown Make"
                cam_model = cam_model if cam_model else "Unknown Model"
                return f"{cam_make} {cam_model}"
            else:
                return "Unknown Camera"
        
    def get_lens(self) -> str:
        cam_make = self.get_tag_with_log("Make").lower()
        lens_make = self.get_tag_with_log("LensMake")
        lens_id = self.get_tag_with_log("LensID")
        lens_model = self.get_tag_with_log("LensModel")
        lens_lens = self.get_tag_with_log("Lens")

        if lens_make:
            if lens_make == "NIKON":
                lens = lens_model
                if lens_model.startswith("NIKKOR"):
                    lens = lens_model[7:]
                    # Replace Z with DOUBLE-STRUCK CAPITAL Z
                    lens = f"\u2124{lens[1:]}" if lens[0] == 'Z' else lens
                return f"Nikkor {lens}"
            elif lens_make == "FUJIFILM":
                if lens_model[:2] in ('XF', 'GF'):
                    # Separate mount info from focal length
                    lens_model = f"{lens_model[:2]} {lens_model[2:]}"
                    # Separate focal length and aperture info
                    lens_model = lens_model.replace('mm', 'mm ', 1)
                return f"Fujinon {lens_model}"
        
        if cam_make == "sony":
            if lens_id[:2] in ('FE', 'E '):
                return f"Sony {lens_model}"
            elif lens_id.lower().startswith("sony"):
                return lens_id.capitalize()
        elif cam_make == "canon":
            if lens_id[:5] == "Canon":
                return lens_id
        
        counter = defaultdict(int)
        if lens_id and not lens_id.strip().startswith("Unknown"):
            counter[lens_id] += 1
        if lens_make and not lens_make.strip().startswith("Unknown"):
            counter[lens_make] += 1
        if lens_model and not lens_model.strip().startswith("Unknown"):
            counter[lens_model] += 1
        if lens_lens and not lens_model.strip().startswith("Unknown"):
            counter[lens_lens] += 1
        
        cnt, most_voted_lens = 0, "Unknown"
        if counter:
            most_voted = sorted((cnt, lens) for lens, cnt in counter.items())[-1]
            cnt, most_voted_lens = most_voted[0], most_voted[1]
        if cnt > 1:
            return most_voted_lens
        if cnt == 1:
            return lens_id if lens_id in counter else lens_make if lens_make in counter else lens_model
        logging.warning("Unknown lens, return as is")
        return "Unknown Lens"
    
    def get_focal_length(self) -> str:
        focal_length = self.get_tag_with_log("FocalLength").replace('.0', '', 1)
        return focal_length if focal_length else "Unknown Focal Length"
    
    def get_focal_length_in_35mm(self) -> str:
        focal_length_35mm = self.get_tag_with_log("FocalLengthIn35mmFormat").replace('.0', '', 1)
        if not focal_length_35mm:
            focal_length_35mm = self.get_tag_with_log("FocalLength35efl").replace('.0', '', 1)
        return focal_length_35mm if focal_length_35mm else "Unknown Focal Length in 35mm format"
    
    def get_aperture(self) -> str:
        aperture = self.get_tag_with_log("Aperture")
        return f"f/{aperture}" if aperture else "Unknown Aperture"
    
    def get_shutter_speed(self) -> str:
        shutter_speed = self.get_tag_with_log("ShutterSpeed")
        return f"{shutter_speed}s" if shutter_speed else "Unknown Shutter Speed"
    
    def get_iso(self) -> str:
        iso = self.get_tag_with_log("ISO")
        return f"ISO {iso}" if iso else "Unknown ISO"
    
    def get_exposure_compensation(self) -> str:
        exposure_compensation = self.get_tag_with_log("ExposureCompensation")
        return f"{exposure_compensation} EV" if exposure_compensation else "Unknown Exposure Compensation"
    
    def get_datetime(self) -> str:
        date_time = self.get_tag_with_log("DateTimeOriginal")
        if date_time:
            date_time_obj = datetime.strptime(date_time, '%Y:%m:%d %H:%M:%S')
            return str(date_time_obj)
        return "Unknown DateTime Original"
    
    def get_metering_mode(self) -> str:
        mode = self.get_tag_with_log("MeteringMode")
        return mode if mode else "Unknown Metering Mode"
    
    def get_orientation(self) -> int:
        orientation = self.get_tag_with_log("Orientation")
        if orientation == "Rotate 90 CW":
            return 6
        if orientation == "Rotate 180":
            return 3
        if orientation == "Rotate 270 CW":
            return 8
        return 1
    
    def get_image_dimensions(self) -> str:
        if self.width and self.height:
            return f"{self.width} x {self.height}"
        return "Unknown Image Dimensions"
    
    def get_bits_per_sample(self) -> str:
        bits_per_sample = self.get_tag_with_log("BitsPerSample")
        return f"{bits_per_sample} bit" if bits_per_sample else "Unknown Bit"
    
    def get_author(self) -> str:
        author = self.get_tag_with_log("Artist")
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
        
        if city.startswith("Unknown") or province.startswith("Unknown"):
            lat, lon = self.get_f_latitude_longitude()
            if lat and lon and not math.isnan(lat) and not math.isnan(lon):
                geolocator = Nominatim(user_agent="fotobot")
                location = geolocator.reverse((lat, lon), exactly_one=True)
                return location.address
            
        return f"{province}, {city}" 
    
    def get_keywords(self) -> str:
        keywords = []
        if self.iptc and (2, 25) in self.iptc:
            for keyword in self.iptc[(2, 25)]:
                if isinstance(keyword, int):
                    keywords.append(str(keyword))
                else:
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
            lat = convert_to_degrees(gps_latitude)
            if gps_latitude_ref != "N":                     
                lat = 0 - lat

            lon = convert_to_degrees(gps_longitude)
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
