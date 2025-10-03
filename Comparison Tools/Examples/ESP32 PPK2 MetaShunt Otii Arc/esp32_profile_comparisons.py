
import sys

sys.path.append('../../')

import metashunt_profile_processing as mpp

if __name__ == "__main__":
    metashunt_profile = mpp.PROFILE(filename="esp32_metashunt_v2.csv", filetype=mpp.FILETYPE.METASHUNT_LOG, 
                            alignment_type=mpp.ALIGNMENTTYPE.TIMESHIFT, label="MetaShunt V2", t_shift=0.0)
    
    arc_profile = mpp.PROFILE(filename="esp32_otii_arc.csv", filetype=mpp.FILETYPE.OTII_LOG, 
                            alignment_type=mpp.ALIGNMENTTYPE.CROSSCORRELATE, alignment_profile=metashunt_profile,
                            label="Otii Arc")
    
    ppk2_profile = mpp.PROFILE(filename="esp32_ppk2.csv", filetype=mpp.FILETYPE.PPK2_LOG, 
                            alignment_type=mpp.ALIGNMENTTYPE.CROSSCORRELATE, alignment_profile=metashunt_profile,
                            label="PPK2")

    
    profiles = [metashunt_profile, arc_profile, ppk2_profile]

    mpp.plot_profiles(profiles, t_lim=(0,40), log_plots=False)
