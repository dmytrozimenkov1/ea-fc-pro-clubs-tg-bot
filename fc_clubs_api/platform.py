from enum import Enum

class Platform(str, Enum):
    COMMON_GEN5 = 'common-gen5'
    COMMON_GEN4 = 'common-gen4'
    NX = 'nx'

PLATFORMS = [Platform.COMMON_GEN5, Platform.COMMON_GEN4, Platform.NX]
