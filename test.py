import ctypes
from ctypes import wintypes

def get_icon_location(extension):
    ASSOCF_NONE = 0
    ASSOCSTR_DEFAULTICON = 2
    S_OK = 0
    
    size = wintypes.DWORD(1024)
    buf = ctypes.create_unicode_buffer(size.value)
    
    result = ctypes.windll.Shlwapi.AssocQueryStringW(
        ASSOCF_NONE,
        ASSOCSTR_DEFAULTICON,
        extension,
        None,
        buf,
        ctypes.byref(size)
    )
    
    if result == S_OK:
        return buf.value
    else:
        return None

icon_location = get_icon_location('.exe')
print(f"Icon location for .jar: {icon_location}")
print("#frbro")