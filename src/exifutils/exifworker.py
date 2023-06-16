from abc import (
    ABC,
    abstractmethod
)

from src.exifutils.styles import (
    DEFAULT_STYLE,
    DEFAULT_STYLE_FF,
    PRETTY_STYLE,
    PRETTY_STYLE_FF,
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

    def get_description(self, style=DEFAULT_STYLE) -> str:
        mapping = {
            'camera': self.get_camera(),
            'lens': self.get_lens(),
            'focal_length': self.get_focal_length(),
            'focal_length_in_35mm': self.get_focal_length_in_35mm(), # 'focal_length_35mm' is added to the mapping
            'aperture': self.get_aperture(),
            'shutter_speed': self.get_shutter_speed(),
            'iso': self.get_iso(),
            'exposure_compensation': self.get_exposure_compensation(),
            'datetime': self.get_datetime()
        }
        focal_length = self.get_focal_length()
        focal_length_in_35mm = self.get_focal_length_in_35mm()

        try:
            if focal_length_in_35mm[:len(focal_length)] == focal_length or focal_length_in_35mm.startswith("Unknown"):
                logging.info("Output in FF format")
                if style == DEFAULT_STYLE:
                    style = DEFAULT_STYLE_FF
                elif style == PRETTY_STYLE:
                    style = PRETTY_STYLE_FF
            template = Template(style)
            description = template.safe_substitute(mapping)
            return description
        except KeyError as e:
            logging.error(f"Invalid style: {e}")
            return ""
