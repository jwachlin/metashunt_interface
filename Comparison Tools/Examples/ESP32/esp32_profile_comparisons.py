
import sys

sys.path.append('../../')

import metashunt_profile_processing as mpp

if __name__ == "__main__":
    metashunt_profile_1 = mpp.PROFILE(filename="metashunt_v2_esp32.csv", filetype=mpp.FILETYPE.METASHUNT_LOG, 
                                      alignment_type=mpp.ALIGNMENTTYPE.NOALIGN, label="V2.1")

    arc_profile_1 = mpp.PROFILE(filename="otii_arc_esp32.csv", filetype=mpp.FILETYPE.OTII_LOG, 
                                      alignment_type=mpp.ALIGNMENTTYPE.TIMESHIFT, label="Otii Log", t_shift=-2.7629)


    
    profiles = [metashunt_profile_1,arc_profile_1]

    mpp.plot_profiles(profiles)
