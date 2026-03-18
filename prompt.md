So this is what I want to do and what I have done till now.                                                               
                                                                                                                            
What I want to to:                                                                                                          
I want to build following lebrobot standards perfectly, best practices and build a environment with so-arm 101 for pick and 
 place task of colored items. you can find about it in my repo.                                                             
Bad thing is: it doesn't work atm, The Dockerfile is absolutely bloated atm, I feel like we need to use nvidias image       
directly and install on top maybe? - I am still not sure -                                                                  
https://isaac-sim.github.io/IsaacLab/main/source/deployment/docker.html                                                     
                                                                                                                            
Another mistake I made was deciding to use leisaac repo - they base themselves on lerobot but somehow installing their      
dependecies caused trouble. Maybe also lerobot might have similar issue, I guess Isaac sim might need some python version   
and lerobot might need something else not sure, please check them.                                                          
                                                                                                                            
What I need - I need clean implementation following lerobot standard and principles - Dont want to reinvent the wheel. I    
want a sim environment first where I can see our environment robot three bowls and different items colored - you can see    
the code. The idea is to later train a VLA for pick and place based on color. We can discuss about that in next step but    
for now I want a nice self contained docker container, which can run the simulation and show our environment in isaac sim   
using isaac lab I guess using lerobot standard - meaning creating like ENvhub style from them, packing and stuff. Please    
read about it all and get an holistic idea of what of I want.                                                               
                                                                                                                            
My overall vision: Create environment - do imitation learning in simulation - I dont have real robot - so we can collect    
samples for training later, - multiply the training data - using nvidia cosmos groot dreams or something I dont know but    
there is a technique to multiply it to many samples, then train VLA or groot N1.6 or something and then test our tarined    
policy in sim. SO I want entire sim only workflow. Now we want the first part, set up env and visualize it. but keep in     
mind overall vision that is important as well.                                                                              
                                                                                                                            
First plan for me how we can do this - Just the first part for now.                                                         
                                                                                                                            
But create a vision file where you write our overall vision so we keep track between different sessions as well. 