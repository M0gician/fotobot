from PIL import Image, ExifTags, IptcImagePlugin

# registry for Exif workers
WORKER_REGISTRY = {}


def register_worker(name: str):
    """Class decorator to register Exif workers."""
    def decorator(cls):
        WORKER_REGISTRY[name] = cls
        return cls
    return decorator


def get_worker(name: str, *args, **kwargs):
    """Instantiate a registered worker."""
    if name not in WORKER_REGISTRY:
        raise ValueError(f"Unknown worker: {name}")
    return WORKER_REGISTRY[name](*args, **kwargs)


def convert_to_degrees(value: tuple[int, int, int]) -> float:
    """Convert GPS tuple to degrees."""
    degrees = value[0]
    minutes = value[1] / 60.0
    seconds = value[2] / 3600.0
    return degrees + minutes + seconds


def load_metadata(path: str):
    """Read width, height, exif and iptc data from ``path`` using Pillow."""
    with Image.open(path) as img:
        width, height = img.size
        exif = {
            **img.getexif(),
            **img.getexif().get_ifd(ExifTags.Base.ExifOffset),
        }
        gps = img.getexif().get_ifd(ExifTags.Base.GPSInfo)
        if gps:
            exif |= {**gps}
        iptc_data = IptcImagePlugin.getiptcinfo(img)
        iptc = {**iptc_data} if iptc_data else {}
    return width, height, exif, iptc
