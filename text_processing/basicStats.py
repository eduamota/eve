# -*- coding: utf-8 -*-
"""
Created on Tue Aug 29 16:19:42 2017

@author: emota
"""

import numpy as np 
from scipy import stats 
 
data = np.array([4,5,1,2,7,2,6,9,3]) 
 
# Calculate Mean 
dt_mean = np.mean(data) ; print ("Mean :",round(dt_mean,2)) 
 
# Calculate Median 
dt_median = np.median(data) ; print ("Median :",dt_median)          
 
# Calculate Mode 
dt_mode =  stats.mode(data); print ("Mode :",dt_mode[0][0])


game_points = np.array([35,56,43,59,63,79,35,41,64,43,93,60,77,24,82]) 
 
# Calculate Variance 
dt_var = np.var(game_points) ; print ("Sample variance:", round(dt_var,2)) 
 
# Calculate Standard Deviation 
dt_std = np.std(game_points) ; print ("Sample std.dev:", round(dt_std,2)) 
                
# Calculate Range 
dt_rng = np.max(game_points,axis=0) - np.min(game_points,axis=0) ; print ("Range:",dt_rng) 
 
#Calculate percentiles 
print ("Quantiles:") 
for val in [20,80,100]: 
     dt_qntls = np.percentile(game_points,val)  
     print (str(val)+"%" ,dt_qntls) 
                                 
# Calculate IQR                             
q75, q25 = np.percentile(game_points, [75 ,25]); print ("Inter quartile range:",q75-q25)

from scipy import stats  
xbar = 990; mu0 = 1000; s = 12.5; n = 30 
 
# Test Statistic 
t_smple  = (xbar-mu0)/(s/np.sqrt(float(n))); print ("Test Statistic:",round(t_smple,2)) 
 
# Critical value from t-table 
alpha = 0.05 
t_alpha = stats.t.ppf(alpha,n-1); print ("Critical value from t-table:",round(t_alpha,3))           
 
#Lower tail p-value from t-table                          
p_val = stats.t.sf(np.abs(t_smple), n-1); print ("Lower tail p-value from t-table", p_val) 

xbar = 67; mu0 = 52; s = 16.3 
 
# Calculating z-score 
z = (67-52)/16.3  
 
# Calculating probability under the curve     
p_val = 1- stats.norm.cdf(z) 
print ("Prob. to score more than 67 is ",round(p_val*100,2),"%")