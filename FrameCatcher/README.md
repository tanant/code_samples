FrameCatcher
------------

For Post-viz, artists were given open slather access to pretty much any slate and any *thing* that could be found to help the shot which helped keep us fast. The down side, when trying to ship out packages to vendor, was that someone (me) had to work out exactly what slates and fragments were used.

For the initial part of the job, I simply cracked open the nukescript but this got silly, and pretty messy when frame ranges were required so I spent some time putting together this node - the theory is that if I was able to drop down a node post every read in the comp script, I could then intercept calls per frame as they roll up the node tree and dump the information somewhere.

Obviously, as soon as we talk about intercepting things in the comp tree, we're talking something slightly non-trivial.. I tried some approaches using in-stream metadata calls, but that was somewhat imperfect when it came to frame blending (which we used a heap of in the early days) and Nuke, bless it's cotton socks, would cache heavily so my logs were all broken anyway, hence this approach. 

