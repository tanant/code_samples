# basically, hunt for the direction flag/keyword
# if you find it, we assume you set it so we don't touch
# otherwise, we just flip the defaults.
proc tde4_ldp_classic_3de_mixed {arg} { 
    set distortflag 0
    set labelflag 0
    set newdefault { direction undistort}
    set comment "(auto-migrated from TDE4/Weta node\ntde4_ldp_classic_3de_mixed)"
    
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
    LD_3DE_Classic_LD_Model $newargs
    }