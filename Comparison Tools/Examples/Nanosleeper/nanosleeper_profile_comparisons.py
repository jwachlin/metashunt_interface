
import sys

sys.path.append('../../')

import metashunt_profile_processing as mpp

if __name__ == "__main__":
    metashunt_profile_1 = mpp.PROFILE(filename="metashunt_v1_nanosleeper.csv", filetype=mpp.FILETYPE.METASHUNT_LOG, 
                                      alignment_type=mpp.ALIGNMENTTYPE.TIMESHIFT, label="MetaShunt V1", t_shift=-6.1659)

    metashunt_profile_2 = mpp.PROFILE(filename="metashunt_v2_nanosleeper.csv", filetype=mpp.FILETYPE.METASHUNT_LOG, 
                                      alignment_type=mpp.ALIGNMENTTYPE.TIMESHIFT, label="MetaShunt V2", t_shift=3.26803)
    
    arc_profile_1 = mpp.PROFILE(filename="otii_arc_nanosleeper.csv", filetype=mpp.FILETYPE.OTII_LOG, 
                                      alignment_type=mpp.ALIGNMENTTYPE.TIMESHIFT, label="Otii Log", t_shift=0.0)
    model_profile_1 = mpp.PROFILE(filename="Nanosleeper_sim.csv", filetype=mpp.FILETYPE.EMBEDDED_POWER_MODEL, 
                                      alignment_type=mpp.ALIGNMENTTYPE.TIMESHIFT, label="Model", t_shift=1.8979)
    
    ppk2_profile_1 = mpp.PROFILE(filename="ppk-2-nanosleeper.csv", filetype=mpp.FILETYPE.PPK2_LOG, 
                                      alignment_type=mpp.ALIGNMENTTYPE.TIMESHIFT, label="PPK2", t_shift=-0.2705)

    
    profiles = [metashunt_profile_1, metashunt_profile_2, arc_profile_1, model_profile_1, ppk2_profile_1]

    mpp.plot_profiles(profiles)
