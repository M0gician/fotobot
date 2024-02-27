from enum import Enum


class Style(Enum):
    DEFAULT = 1
    FULL = 2
    PRETTY = 3


def get_default_style(full_frame=False, special=False, unknown=False,
                      country=False, location=False, title=False, gps=False) -> str:
    style = ""
    if title:
        style += "$title\n"
    else:
        style += "\n"

    style += "——————————\n"
    style += "Camera: $camera\n"
    style += "Lens: $lens\n"

    if unknown:
        style += "Parameters unknown\n"
    elif full_frame:
        style += "$focal_length, $aperture, $shutter_speed, $iso\n"
    else:
        if special:
            style += "$focal_length_in_35mm, $aperture, $shutter_speed, $iso\n"
        else:
            style += "$focal_length ($focal_length_in_35mm equiv), $aperture ($dof_in_35mm equiv), $shutter_speed, $iso\n"

    if location or country:
        if country and country:
            style += "🗺️: $location, $country\n"
        elif country:
            style += "🗺️: $country\n"
        else:
            style += "🗺️: $location\n"
    if gps:
        style += "📍: $gps_coordinates\n"
    
    return style[:-1]

def get_full_style(full_frame=False, exposure_compensation=False, metering=False, author=False,
                   title=False, country=False, location=False, gps=False, keywords=False
                   ) -> str:
    style = "<pre>\n"
    style += "[Camera]\n" + "    $camera\n"
    style += "[Lens]\n" + "    $lens\n"
    style += "[Focal Length]\n" + "    $focal_length\n"

    if not full_frame:
        style += "[Focal Length in 35mm]\n" + "    $focal_length_in_35mm\n"
        style += "[Depth of Field in 35mm]\n" + "    $dof_in_35mm\n"

    style += "[Aperture]\n" + "    $aperture\n"
    style += "[Shutter Speed]\n" + "    $shutter_speed\n"
    style += "[ISO]\n" + "    $iso\n"

    if exposure_compensation:
        style += "[Exposure Compensation]\n" + "    $exposure_compensation\n"
    if metering:
        style += "[Metering Mode]\n" + "    $metering_mode\n"

    style += "[Image Dimensions]\n" + "    $image_dimensions\n"
    if author:
        style += "[Author]\n" + "    $author\n"
    if title:
        style += "[Title]\n" + "    $title\n"
    if location or country:
        style += "[Location]\n"
        if location:
            style += "    $location\n"
        if country:
            style += "    $country\n"
    if gps:
        style += "[GPS Coordinates]\n" + "    $gps_coordinates\n"
    if keywords:
        style += "[Keywords]\n" + "    $keywords\n"
    
    style += "[DateTime Original]\n" + "    $datetime </pre>"

    return style

def get_pretty_style(full_frame=False, is_unknown=False, country=False, location=False, title=False, gps=False) -> str:
    style = ""
    if title:
        style += "💭: $title\n"
    else:
        style += "💭: \n"

    style += "——————————\n"
    style += "📸: $camera / $lens\n"

    if is_unknown:
        style += "📝: Parameters Unknown\n"
    elif full_frame:
        style += "📝: $focal_length, $aperture, $shutter_speed, $iso\n"
    else:
        style += "📝: $focal_length_in_35mm, $aperture, $shutter_speed, $iso\n"

    style += "📅: $datetime\n"

    if location or country:
        if location and country:
            style += "🗺️: $location, $country\n"
        elif location:
            style += "🗺️: $location\n"
        else:
            style += "🗺️: $country\n"
    if gps:
        style += "📍: $gps_coordinates\n"
    
    return style[:-1]
