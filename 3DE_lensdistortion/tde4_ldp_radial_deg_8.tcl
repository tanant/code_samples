# anthony.tan@greenworm.net for FuryFX
# 18/12/2013
#
# translates old-style tde4 nodes into new-style LDPK 1.7 LD nodes
# Comment/setting preserving 
# note: direction default is opposite to old TDE4 node!

proc tde4_ldp_radial_deg_8 {arg} { 
    set distortflag 0
    set labelflag 0
    set newdefault { direction undistort}
    set comment "(auto-migrated from TDE4/Weta node\ntde4_ldp_radial_deg_8)"
    
    foreach {key value} $arg {
        # inline arg translation. 
        # this is just brutal, but triple underscores are pretty rare
        set newkey [regsub -all ___ $key _]

        switch $newkey {
            label {
                set value $value"\n\n"$comment
                set labelflag 1
                }
                
            direction {
                set distortflag 1
                }
            }
        #puts [list $newkey $value]
        append newargs { } 
        append newargs [list $newkey $value]
    }
    
    if {$distortflag == 0} {
        append newargs { } 
        append newargs $newdefault
        }
    
    if {$labelflag == 0} {
        append newargs { } 
        append newargs [list label $comment]
        }     

    puts $newargs
    LD_3DE4_Radial_Fisheye_Degree_8 $newargs
    }

    