from abc import (
    ABC,
    abstractmethod
)
import logging
from string import Template

class ExifWorker(ABC):

    @abstractmethod
    def get_camera(self) -> str:
        pass

    @abstractmethod
    def get_lens(self) -> str:
        pass

    @abstractmethod
    def get_focal_length(self) -> str:
        pass

    @abstractmethod
    def get_focal_length_in_35mm(self) -> str:
        pass

    @abstractmethod
    def get_aperture(self) -> str:
        pass

    @abstractmethod
    def get_dof_in_35mm(self) -> str:
        pass

    @abstractmethod
    def get_shutter_speed(self) -> str:
        pass

    @abstractmethod
    def get_iso(self) -> str:
        pass

    @abstractmethod
    def get_exposure_compensation(self) -> str:
        pass

    @abstractmethod
    def get_datetime(self) -> str:
        pass
    
    @abstractmethod
    def get_metering_mode(self) -> str:
        pass

    @abstractmethod
    def get_orientation(self) -> int:
        pass
    
    @abstractmethod
    def get_image_dimensions(self) -> str:
        pass
    
    @abstractmethod
    def get_bits_per_sample(self) -> str:
        pass

    @abstractmethod 
    def get_author(self) -> str:
        pass
        
    @abstractmethod
    def get_title(self) -> str:
        pass
        
    @abstractmethod
    def get_country(self) -> str:
        pass
        
    @abstractmethod
    def get_location(self) -> str:
        pass
        
    @abstractmethod
    def get_keywords(self) -> str:
        pass

    @abstractmethod
    def get_latitude_longitude(self) -> str:
        pass

    @abstractmethod
    def get_f_latitude_longitude(self) -> str:
        pass


    def get_description(self, template: str) -> str:
        mapping = {
            'camera': self.get_camera(),
            'lens': self.get_lens(),
            'focal_length': self.get_focal_length(),
            'focal_length_in_35mm': self.get_focal_length_in_35mm(), # 'focal_length_35mm' is added to the mapping
            'aperture': self.get_aperture(),
            'dof_in_35mm': self.get_dof_in_35mm(),
            'shutter_speed': self.get_shutter_speed(),
            'iso': self.get_iso(),
            'exposure_compensation': self.get_exposure_compensation(),
            'datetime': self.get_datetime(),
            'metering_mode': self.get_metering_mode(),
            'image_dimensions': self.get_image_dimensions(),
            'bits_per_sample': self.get_bits_per_sample(),
            'author': self.get_author(),
            'title': self.get_title(),
            'country': self.get_country(),
            'location': self.get_location(),
            'keywords': self.get_keywords(),
            'gps_coordinates': self.get_latitude_longitude(),
        }

        try:
            template = Template(template)
            description = template.safe_substitute(mapping)
            return description
        except KeyError as e:
            logging.error(f"Invalid style: {e}")
            return ""
