#!/usr/bin/env python3
# -*- coding:utf-8 -*-
'''
#==============================================================================
# DQC - DATA QUALITY CONTROL
#==============================================================================

This tests are for the following parameters:
	ATM: wind speed
		 wind direction
		 humidity
		 temperature
		 gusts
		 pressure
		 radiation
		 dew point

	WQMX, SATPH, SUNA: temperature
		   			   salinity
		   			   turbidity
		   			   cdom
		   			   nitrate
		   			   chla
		   			   ph
		   			   do


@author:fncsobral
@date  : 31/jul/2017
#==============================================================================
'''

import numpy as np


#==============================================================================
#
#==============================================================================
class DQC(object):
	'''

	'''

	def __init__(self, new_param, parameter_name, dqc_aux):		
		self.new_param = new_param
		self.name      = parameter_name
		self.dqcaux    = dqc_aux


	#==========================================================================
	#
	#==========================================================================
	def gross_range(self):
		'''
		Fail = 4 : if WSn < SENSOR_MIN, or	
	 			      WSn > SENSOR_MAX,

		Suspect = 3 : If WSn < USER_MIN, or	
						 WSn > USER_MAX
		'''
		
		# Getting all the hardware and environmental limits.
		
		grss_rng = self.dqcaux.grss_rng_hdw_env_limits()

		# for kk in param_reorganized.keys():
		if self.name == 'avg_dew_pnt':
			pass
		
		elif self.name == 'gusts':
			# Gusts will use the wind thresholds, at the ELSE statement.
			# Using limits from wind speed.
			jj = 'avg_wnd_spd'
			SENSOR_MIN = grss_rng['hardware'][jj][0]
			SENSOR_MAX = grss_rng['hardware'][jj][1]
			USER_MIN   = grss_rng['environment'][jj][0]
			USER_MAX   = grss_rng['environment'][jj][1]

		else:
			# Getting hardware and environmental limits.
			SENSOR_MIN = grss_rng['hardware'][self.name][0]
			SENSOR_MAX = grss_rng['hardware'][self.name][1]
			USER_MIN   = grss_rng['environment'][self.name][0]
			USER_MAX   = grss_rng['environment'][self.name][1]
			
		
		# --------------------------- FLAG CONDITIONALS -----------------------
		# Loop over time.
		flags = list()
		for Tn in self.new_param:
			if str(Tn) == 'nan':
				flags.append(9)
			elif Tn < SENSOR_MIN or Tn > SENSOR_MAX:
				flags.append(4)
			elif Tn < USER_MIN or Tn > USER_MAX:
				flags.append(3)
			else:
				flags.append(1)

		# Inserting in dictionary
		FLAGS = {self.name: flags}

		return(FLAGS)


	#==========================================================================
	# 
	#==========================================================================
	def spike(self, sf, TIM_DEV=5):
		'''
		ATTENTION: This test is not for WAVE or CURRENT data. For the later
		use uv_spike instead. WAVE need the ST (short-term) data and, for now,
		I just have the LT (long-term) data, the wave bulk parameters (Hs, Tp, Dp).

		INPUT: (TIM_DEV=6)
				TIM_DEV: is the window size to get data and retrieve STD.

		@date: 04/aug/2017
		'''

		# Verifying if parameter choosed is for this test.
		if not any([True for nn in self.dqcaux.many_param if self.name == nn]):
			raise ValueError('This test does not apply for the parameter', 
							  'choosed. Please change the parameter or the', 
							  'test to be performed.')


		# List of tuples, where each tuple stores: Group, STD, Tn and values to 
		# find SPK_REF, Tn neighbors. Wdw is the size of the windows used.
		group, wdw = self.dqcaux.grouping(self.new_param, sf, 'spike')


		# This will be the history of flags and will be the responsible for 
		# removing values from  gg when it has flag 4, to avoid the SD calculation
		# with this wrong value.
		flag_guide = np.array([2] * len(self.new_param))

		# Storing flags list
		flags = list()	

		for ii, GG in enumerate(group):

			# Extracting values from GG						
			Tn     = GG[2]
			tn0tn1 = GG[3]
			idx_tn = GG[1][1]
			idx_gg = GG[1][0]						
			gg = np.array(GG[0])

			if ii == 0:
				SD, _ = self.dqcaux.nan_watcher(gg)
			else:
				# Selecting the flag's group within the main flag_guide
				flag_gg = flag_guide[idx_gg]

				# When having flag 4, insert nan in group values
				gg[flag_gg == 4] = np.nan

				# Calculating SD
				SD, _ = self.dqcaux.nan_watcher(gg)


			# ----------------------- FLAG CONDITIONALS -----------------------
			# SPK_REF: if exist, calculate MEAN, else, FLAG 2.
			if str(Tn) == 'nan':
				flags.append(9)				
				flag_guide[idx_tn] = 9

			elif str(tn0tn1)[0] == 'nan' or str(tn0tn1)[1] == 'nan':
				flags.append(2) 

			else:
				SPK_REF = np.mean(tn0tn1)

				# Defining limits and STD weights.
				THRSHLD_HIGH = SD * 2
				THRSHLD_LOW  = SD * 1.5

				if abs(Tn - SPK_REF) > THRSHLD_HIGH:
					flags.append(4)
					flag_guide[idx_tn] = 4

				elif abs(Tn - SPK_REF) > THRSHLD_LOW and abs(Tn - SPK_REF) <= THRSHLD_HIGH:
					flags.append(3)
					flag_guide[idx_tn] = 3

				else:
					flags.append(1)
					flag_guide[idx_tn] = 1


		# The last data, receiving flag 2, not possible to be analyzed.
		flags.append(2)
		
		# Storing
		FLAGS = {self.name: flags}

		return(FLAGS)

	#==========================================================================
	# 
	#==========================================================================
	def rate_change(self, sf, N_DEV=3, TIM_DEV=8):
		'''
		The rate of change between temperature Tn-1 and Tn must be less than three 
		standard deviations (3*SD). The SD of the T time series is computed over 
		the previous 25-hour period (operator-selected value) to accommodate 
		cyclical diurnal and tidal fluctuations. Both the number of SDs (N_DEV) 
		and the period over which the SDs (TIM_DEV) are calculated and determined 
		by the local operator.

		N_DEV   = multiplier of standard deviations (SD) 
		TIM_DEV = period over SD is calculated 

		@date: 03/aug/2017
		'''

		# Description of "group": [25 hours of data, STD for this period, Tn and Tn0]
		group, wdw = self.dqcaux.grouping(self.new_param, sf, 'ratechange')


		# This will be the history of flags and will be the responsible for 
		# removing values from  gg when it has flag 4, to avoid the SD calculation
		# with this wrong value.
		flag_guide = np.array([2] * len(self.new_param))

		# Storing list
		flags = list()

		for ii, GG in enumerate(group):

			# Extracting from GG
			Tn  = GG[2]
			Tn0 = GG[3]
			idx_tn = GG[1][1]
			idx_gg = GG[1][0]
			gg = np.array(GG[0])


			# Statement for flags evaluation. Flag 4 values, must be 
			# desconsidered from the analysis. 
			# In the first loop, none flag exist.
			if ii == 0:
				SD, _ = self.dqcaux.nan_watcher(gg)
			else:
				# Selecting the flag's group within the main flag_guide
				flag_gg = flag_guide[idx_gg]

				# When having flag 4, insert nan in group values
				gg[flag_gg==4] = np.nan

				# Calculating SD
				SD, _ = self.dqcaux.nan_watcher(gg)


			# ----------------------- FLAG CONDITIONALS -----------------------
			# If data evaluated does not exist.
			# If SD not available due to group NaN values.
			if str(Tn) == 'nan':
				flags.append(9)
				flag_guide[idx_tn] = 9

			elif str(SD) == 'nan' or str(Tn0) == 'nan':
				flags.append(2)

			else:
				if abs(Tn - Tn0) > N_DEV * SD:
					flags.append(3)
					flag_guide[idx_tn] = 3
				else:
					flags.append(1)
					flag_guide[idx_tn] = 1

		# Storing
		FLAGS = {self.name: flags}

		return(FLAGS)

	#==========================================================================
	# 
	#==========================================================================
	def flat_line(self, sf):
		'''
	   	INPUTS:
			EPS_PARAM: this input should be the name of the parameter analyzed
			as write in the list below:
				**ATM** avg_wnd_spd, avg_humidity, avg_temp, gusts, avg_press,
	                    avg_radiation, avg_dew_pnt, avg_wnd_dir


	  	@date: 07/aug/2017
		'''

		EPS = {
			  	'avg_wnd_spd'  : 0.5   ,
	            'avg_humidity' : 1     ,
	            'avg_temp'     : 0.1   ,
	            'gusts'        : 1     ,
	            'avg_press'    : 0.1   ,
	            'avg_radiation': 10    ,
	            'avg_dew_pnt'  : 0.05  ,
	            'avg_wnd_dir'  : 0     ,
	            'precipitation': 0     ,
	            'atm_co2'      : 10    , 
	            #-----
	            'do'           : 0.01  ,
	            'nitrate'      : 0.05  ,
	            'ph'           : 0.0001,          
	            'chla'         : 0.05  ,
	            'temperature'  : 0.01  ,
	            'salinity'     : 0.001 ,
	            'turbidity'    : 0.01  ,
	            'cdom'         : 0.02  
		    }


		# Getting EPS value according with self.name
		eps_got = EPS[self.name]

		# Number of repetitions to evaluate.
		REP_CNT_FAIL    = 5
		REP_CNT_SUSPECT = 3

		# Grouping data
		group, wdw = self.dqcaux.grouping(self.new_param, sf, 'flatline')


		# This will be the history of flags and will be the responsible for 
		# removing values from  gg when it has flag 4, to not use then to
		# calculate the difference between time sample. Here, if a NaN is
		# present at the gg group values, flag 2 will be added.
		flag_guide = np.array([2] * len(self.new_param))


		# Storing list
		flags = list()


		for ii, GG in enumerate(group):

			# Getting group values, group index and tn index.
			gg     = np.array(GG[0])
			Tn     = GG[2]
			idx_gg = GG[1][0]
			idx_tn = GG[1][1]

			if ii > 0:
				# Selecting the flag's group within the main flag_guide
				flag_gg = flag_guide[idx_gg]

				# When having flag 4, insert nan in group values
				gg[flag_gg==4] = np.nan


			# Transforming gg group into list, because it must be LIST due 
			# to merging with Tn code below
			gg = list(gg)


			# Putting Tn and group values together. Tn will be at the last position 
			# of the array. [tgr = together]
			# Also together and in the same way Tn and group indexes together.
			# Sorting indexes.			
			tgr_val    = np.array(gg + [Tn])
			tgr_index  = idx_gg + [idx_tn]
			stgr_index = np.argsort(tgr_index)


			# Sorting values, and this is will be the GRP5 already. GRP5 is 
			# independent of position, because is using all values. GRP3 should 
			# have a Tn position verification.
			grp5 = tgr_val[stgr_index]


			# Selecting the GPR3 values
			if idx_tn <= 2:
				grp3 = grp5[:3]
			else:
				grp3 = grp5[-3:]


			# Getting the difference within groups.
			df5 = abs(np.diff(grp5))
			df3 = abs(np.diff(grp3))



			# ---------------------------- FLAG CONDITIONALS ------------------
			# If Tn [evaluated value] does not exist
			# Or group values NaN, not possible to analyze.
			if str(Tn) == 'nan':
				flags.append(9)
				flag_guide[idx_tn] = 9

			# If any NAN is present, Flag 2 is given.
			elif (any([True for dd in df5 if str(dd) == 'nan']) 
				  or any([True for dd in df3 if str(dd) == 'nan'])):
				flags.append(2)
			else:					
				if all(df5 < eps_got):
					flags.append(4)
					flag_guide[idx_tn] = 4
				else:
					if all(df3 < eps_got):
						flags.append(3)
						flag_guide[idx_tn] = 3
					else:
						flags.append(1)
						flag_guide[idx_tn] = 1

			FLAGS = {self.name: flags}

		return(FLAGS)
	

	#==========================================================================
	# 
	#==========================================================================
	def attenuated_signal(self, sf, whichtest=None):
		"""
		A common sensor failure mode can provide a data series that is nearly but 
		not exactly a flat line (e.g., if the sensor head were to become wrapped in 
		debris)

		Group of 12 data HOURS.

		"""		
		if whichtest == 'salinity':
			MIN_VAR_FAIL = 0.001
			MIN_VAR_WARN = 0.005
		elif whichtest == 'temperature':
			MIN_VAR_FAIL = 0.02
			MIN_VAR_WARN = 0.04
		elif whichtest == 'turbidity':
			MIN_VAR_FAIL = 0.05
			MIN_VAR_WARN = 0.05
		elif whichtest == 'cdom':
			MIN_VAR_FAIL = 0.03
			MIN_VAR_WARN = 0.05
		elif whichtest == 'chla':
			MIN_VAR_FAIL = 0.05
			MIN_VAR_WARN = 0.07
		elif whichtest == 'do':
			MIN_VAR_FAIL = 0.005
			MIN_VAR_WARN = 0.01
		elif whichtest == 'nitrate':
			MIN_VAR_FAIL = 0.05
			MIN_VAR_WARN = 0.1
		else:
			# VALORES GENERICOS QUE DEVEM SER ATUALIZADOS!!!! - 11/AUG/2017
			print('Valores MIN_VAR_FAIL e MIN_VAR_WARN' 
				  'devem ser MELHORADOS!!!! [clss_dqc - attenuated_signal]')
			MIN_VAR_FAIL = 0.1
			MIN_VAR_WARN = 0.2


		# Grouping data
		group, wdw = self.dqcaux.grouping(self.new_param, sf, 'attenuatedsignal')


		# This will be the history of flags and will be the responsible for 
		# removing values from  gg when it has flag 4, to not use then to
		# calculate the difference between time sample. Here, if a NaN is
		# present at the gg group values, flag 2 will be added.
		flag_guide = np.array([2] * len(self.new_param))

		# Storing list
		flags = list()


		# Loop into groups.
		for ii, GG in enumerate(group):

			# Getting group values, group index and tn index.
			gg     = np.array(GG[0])
			Tn     = GG[2]
			idx_gg = GG[1][0]
			idx_tn = GG[1][1]

			# Getting analyzing group, Tn analyzed data, std and maxmin values
			if ii == 0:
				SD, _ = self.dqcaux.nan_watcher(gg)

				# Calculating MAX and MIN from group.
				max_min = np.nanmax(gg) - np.nanmin(gg)

			else:
				# Selecting the flag's group within the main flag_guide
				flag_gg = flag_guide[idx_gg]

				# When having flag 4, insert nan in group values
				gg[flag_gg==4] = np.nan

				# Calculating SD
				SD, _ = self.dqcaux.nan_watcher(gg)

				# Calculating MAX and MIN from group.
				max_min = np.nanmax(gg) - np.nanmin(gg)

			# If Tn does not exist, flag 9
			# If the group to give STD and max min has nan, flag 2
			if str(Tn) == 'nan':
				flags.append(9)
				flag_guide[idx_tn] = 9

			elif str(SD) == 'nan' or str(max_min) == 'nan':
				flags.append(2)

			elif SD < MIN_VAR_FAIL or max_min < MIN_VAR_FAIL:
				flags.append(4)
			elif SD < MIN_VAR_WARN or max_min < MIN_VAR_WARN:					
				flags.append(3)
			else:
				flags.append(1)

		# Storing
		FLAGS = {self.name: flags}

		return(FLAGS)


# Ainda melhorar::
# 1. O ultimo dado deve receber ao menos flag 2, pois não existe o 
# neighbor tn1 para o spk_ref dentro do teste spike para realizar
# o teste ----- 02/aug/2017
# 2. inserir a questão de análise da flag 4, para desconsiderar este dado na
# análise dos testes precedentes. [OK!]

#==========================================================================
# END!
#==========================================================================