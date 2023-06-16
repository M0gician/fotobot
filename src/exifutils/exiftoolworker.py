import logging
import exiftool
from string import Template

from src.exifutils.styles import (
    DEFAULT_STYLE
)

class ExifToolWorker:
    def __init__(self, img_path: str) -> None:
        self.img_path = img_path
        with exiftool.ExifToolHelper(common_args=None) as et:
            metadata = et.get_metadata(img_path, params=['-fast1', "-EXIF:All", "-MakerNotes:All", "-Composite:All"])
            self.exif = {}
            if len(metadata) == 0:
                logging.error(f"Fail to parse file: {img_path}")
            else:
                self.exif = metadata[0]
    
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
        cam_make = self.get_tag_with_log("Make").lower()
        lens_make = self.get_tag_with_log("LensMake")
        lens_id = self.get_tag_with_log("LensID")
        lens_model = self.get_tag_with_log("LensModel")

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
            
        if lens_id:
            return lens_id
        else:
            logging.warning("Unknown lens, return as is")
            return "Unknown Lens"
    
    def get_focal_length(self) -> str:
        focal_length = self.get_tag_with_log("FocalLength")
        return focal_length if focal_length else "Unknown Focal Length"
    
    def get_focal_length_35mm(self) -> str:
        focal_length_35mm = self.get_tag_with_log("FocalLengthIn35mmFormat")
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
        datetime = self.get_tag_with_log("DateTimeOriginal")
        return datetime if datetime else "Unknown DateTime Original"

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