# 3D Spatial Privacy

# ABSTRACT
Augmented reality (AR) or mixed reality (MR) platforms require spatial understanding to detect objects or surfaces, often including their structural (i.e. spatial geometry) and photometric (e.g. color, and texture) attributes, to allow applications to place virtual or synthetic objects seemingly "anchored'' on to real world objects; in some cases, even allowing interactions between the physical and virtual objects. These functionalities requires AR/MR platforms to capture the 3D spatial information with high resolution and frequency; however, this poses unprecedented risks to user privacy. Aside from objects being detected, spatial information also reveals the location of the user with high specificity, e.g. in which part of the house the user is. In this work, we propose to leverage *spatial generalizations* coupled with *conservative releasing* to provide spatial privacy while maintaining data utility. We simulate user movement within spaces which reveals more of their space as they move around. Then, we designed an inference attacker to which the proposed spatial privacy approach can be evaluated against. Results show that revealing no more than 11 generalized planes--accumulated from revealed spaces with large enough radius, i.e. *r*≤1.0m--can make an adversary fail in identifying the spatial location of the user for at least half of the time. Furthermore, if the accumulated spaces are of smaller radius, i.e. *r*≤ 0.5m, we can release up to 29 generalized planes while enjoying both better data utility and privacy.

# SUMMARY
In light of this, first, we present an attacker that not only recognizes the general space, i.e. *inter-space*, but also infers the user’s location within the space, i.e. *intra-space*. To construct the attacker, we build up on existing place recognition methods that have been applied on 3D lidar data and modify it to the scale on which 3D data is captured by MR platforms. We demonstrate how easy it is to extend these 3D recognition methods to be used as an attacker in the MR scenario. Then, we present *spatial plane generalizations* with *conservative plane releasing* as a simple privacy approach.

# SAMPLE CODE
The notebook 3D-spatial-privacy-sample.ipynb contains a step-by-step replication of the work at a smaller scale. As one can inspect, we vary the following parameters on both Raw spaces and [RANSAC] generalized spaces: 
1. the size, i.e radius, of the revealed space
2. the number of successively released partial spaces
3. the number of *generalized* planes released
