# anthony.tan@greenworm.net for FuryFX
# 18/12/2013
#
# translates old-style tde4 nodes into new-style LDPK 1.7 LD nodes
# Comment/setting preserving 
# note: direction default is opposite to old TDE4 node!

proc tde4_ldp_anamorphic_deg_6 {arg} { 
    set distortflag 0
    set labelflag 0
    set newdefault { direction undistort}
    set comment "(auto-migrated from TDE4/Weta node\ntde4_ldp_anamorphic_deg_6)"
    
    foreach {key value} $arg {
        # in-line arg translation. 
        set newkey [regsub -all ___ $key _]
        
        switch $newkey {
            label {
                set labelflag 1
                set value $value"\n\n"$comment
                puts $value
                }
                
            direction {
                set distortflag 1
                }
            }
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
    LD_3DE4_Anamorphic_Degree_6 $newargs
    }

    