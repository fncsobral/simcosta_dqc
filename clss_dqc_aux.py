#!/usr/bin/env python3
# -*- coding:utf-8 -*-
'''
#==============================================================================
# CLASS AUXILIARY FOR DQC CLASS
#==============================================================================



@author:fncsobral
@date  : 07/aug/2017
@mod.1 : 29/aug/2017 - FS
         __init__: inserted1 input current_direction field.
#==============================================================================
'''


from datetime import datetime as dtm
import calendar, gsw
from statistics import mean
import numpy as np


#==============================================================================
#	
#==============================================================================
class DQC_aux(object):
	

	#==========================================================================
	#
	#==========================================================================
	def __init__(self                 ,  
		         parameter            ,   
		         date=None            , 
		         reference_time = None,
		         sensor_name=None     , 
		         parameter_name=None  , 
		         cur_dir=None         , 
		         tests=None):

		'''
		INPUT: (parameter, parameter_name, date, cur_dir=None, tests=None)
				
				PARAMETER: a list with same parameter data
				PARAMETER_NAME: string with parameter name, 
				                write in one of the following options:
								
								** temperature, salinity, do, nitraten, ph
								** chla, turbidity, cdom	
								** avg_press, avg_temp, avg_humidity, avg_wnd_spd
								** avg_wnd_dir, avg_radiation,	avg_dew_point
								** current
								** wave

				DATE: timeseries time in datetime (from datetime) format
				REFERENCE_TIME: time in UTC as string.
				CURRENT_DIRECTION: as current data has speed and direction,
				                   this input is just for this parameter.			               
				TESTS: None is the default option, and means that all the 
				       possible tests will be performed (required, strongly
				       recommended, suggested). 
				       To perform JUST the REQUIRED tests, use number 1.
				       To perform BOTH REQUIRED and STRONG RECOM, use number 2.
				
				MANY_PARAM: are the parameters that has (at least for now) all
				            the same tests to be performed. If other kind of 
				            data arrived, as the specific ones for the opticals,
				            some modification will be necessary.

		'''
		self.parameter  = parameter
		self.date       = date
		self.reftime    = reference_time
		self.sensorNM   = sensor_name
		self.name       = parameter_name
		self.curdir     = cur_dir
		self.tests      = tests
		self.many_param = ['cdom'        , 'temperature', 'salinity'    , 'chla'    ,
		                  'nitrate'      , 'do'         , 'turbidity'   , 'pressure',
						  'ph'           ,
						  'avg_press'    , 'avg_temp'   , 'avg_humidity' , 
						  'avg_wnd_spd'  , 'avg_wnd_dir', 'avg_radiation',
						  'precipitation', 'atm_co2'
						]

	#==========================================================================
	#
	#==========================================================================
	def time_data_organizing(self):
		'''
		Script to verify time, inserting NaN when data does not exist.
		NaN is inserted both in time and data parameter.

		INPUT: (time, parameter)
			   TIME: timeseries time in datetime
			   PARAMETER: a list of your parameter

		OUTPUT:
				NEW_PARAM: the parameter from input but now with nans.
				VEC_GUIDE: the time with nan inserted where does not exist values.
						
		@date : 01/aug/2017
		@mod.1: 14/aug/2017 - FS
				- isinstance() statement to verify the type of date inserted.
		@mod.2: 15/aug/2017 - FS
				- added verification for SF. If zero, means repeated hours. A
				time conditional will flag this sampled hour as wrong [but for
				now, can be a server mistake...]
		'''


		# Verifying time type
		dd = self.date
		if not isinstance(dd[0], dtm):
			raise ValueError('Time is not in DateTime format. Please modify it '
				             'to be able to use this function properly. Thanks!')

		# Rounding time for 1:30 kind of data.
		# For 25m and 55m kind of data, we cant round minutes.
		time2 = list()
		if self.date[0].minute == 1:
			for tt in self.date:
				time2.append(dtm(tt.year, tt.month, tt.day, tt.hour))
		else:	
			for tt in self.date:
				time2.append(dtm(tt.year, tt.month, tt.day, tt.hour, tt.minute))


		# Organizing in ascending order
		sort_time = np.sort(time2)
		idx       = np.argsort(time2)

		
		# Finding out what is the Sampling Frequency (there are two SF)
		df = list()
		tt_df = np.diff(sort_time)

		for tt in tt_df:
			df.append(tt.seconds)


		# Selecting unique difference values
		uu = np.unique(df)


		# Counting the repeated time differences.
		cc = list()
		for u in uu:
			# Count value
			c = 0
			for dd in df:
				if dd == u:
					c += 1
			# Storing count values
			cc.append(c)


		# Sorting ascending the number of repeated values. The last is the major
		# and then it is what will be used.
		ii = np.argsort(cc)

		
		# Sampling frequency
		sf = uu[ii[-1]]


		# If sampling frequency is zero, then something is wrong with sampling.
		if sf == 0:
			print('!!!!!!!!!!!!!!!!!! WARNING !!!!!!!!!!!!!!!!')
			print('Sampling Frenquency ZERO something wrong...')
			print('Choosing the next Sampling Frequency of the list.')
			print('Frequency choosed: ', uu[ii[-2]])
			print('Function is question is def time_data_organizing [clss_dqc_aux]')
			print('###########################################')
			print('\n')
			sf = uu[ii[-2]]


		# Creating datetime equidistant in time for the period to be analyzed.
		epoch1 = calendar.timegm(time2[0].timetuple())
		epoch2 = calendar.timegm(time2[-1].timetuple())

		equidistant_time = [dtm.utcfromtimestamp(x) for x in range(epoch1, epoch2 + sf, sf)]
		

		# Finding indexes to insert NaN
		new_param = list()
		param = self.parameter



		# Getting shape of parameter array (rows, columns)
		sh = np.shape(param)

		# counter of nan numbers
		nan_nb = 0

		# Reference time to filling gaps
		new_reftime = list()

		for en, vv in enumerate(equidistant_time):
			if vv not in time2:

				# To facilitate in time to verify current list shape, is easier
				# to fill the list with a list of nan in the same size of the 
				# depth.
				if self.name == 'current':
					new_param.append(np.array([np.nan] * sh[1]))
					new_reftime.append('NaN')					
					nan_nb += 1
				else:
					new_param.append(np.nan)
					new_reftime.append('NaN')
					nan_nb += 1

			else:
				# Finding index ii to get respective parameter value 
				tmp = [ii for ii, vv2 in enumerate(time2) if vv2 == vv]

				# tmp[0] is necessary to take off the value from the list, even
				# just one value is within it.
				new_param.append(self.parameter[tmp[0]])
				new_reftime.append(self.reftime[tmp[0]])


		print('This timeseries has ' + str(nan_nb) + ' Not a Number values.')
		


		return(new_param, equidistant_time, new_reftime, sf)


	#==========================================================================
	#
	#==========================================================================
	def grouping(self, new_param, sf, whichtest):
		'''		
		spike as 'spike': window of 5 numbers plus Tn.
		rate of change as 'ratechange': window of 25 hour period. This does not 
										necessarily implies that window size 
										will be 25, some time it will be 50 size,
		                				depending on the rate of sampling.
		flat line as 'flatline': this test will use a window of 4, and Tn must 
								 have inserted together, in the right order
								 extracted from time series.

		@date : 02/aug/2017
		@mod.1: 08/aug/2017 - FS:
				- inserting scheme to flat line
		'''

		group = list()

		#----------------------- Defining WINDOW SIZE and loop range ----------
		if whichtest == 'spike':
			# Is this test, the window size try to sample 5 sample elements,
			# not hours. So, no SAMPLING FREQUENCY test must be applyed.
			wdw = 5

			#Spike depends of the Tn1, after Tn to verify SPK_REF.
			rnglimit = len(new_param) - 1

		elif whichtest == 'ratechange':
			# Rate of Change needs 25 HOURS, not elements, so the Sampling
			# Frequency is important to define the window size.
			if sf == 3600:
				wdw = 25
			elif sf == 1800:
				wdw = 50
			else:
				print('Different SAMPLING FREQUENCY found! Need verification' 
					  'or adjustment.')

			#The last element can be Tn
			rnglimit = len(new_param)

		elif whichtest == 'flatline':
			wdw = 4
			rnglimit = len(new_param)

		elif whichtest == 'attenuatedsignal' or whichtest == 'meanstd':
			# Attenuated Signal needs 12 HOURS, not elements, so the Sampling
			# Frequency is important to define the window size.
			if sf == 3600:
				wdw = 12
			elif sf == 1800:
				wdw = 24
			else:
				print('Different SAMPLING FREQUENCY found! Need verification' 
					  'or adjustment.')

			#The last element can be Tn
			rnglimit = len(new_param)



		#--------------------------- Loop into parameter array ----------------
		for ii in range(rnglimit):

			if ii == 0:
				# Spike needs value before and after Tn (Tn0 and Tn1 respectively).
				if whichtest == 'spike':
					gg     = new_param[ii+1:wdw+1]

					# Index (idx) includes also Tn index, but in the SECOND column
					idx    = [list(range(ii+1, wdw+1)), ii] 
					# STD    = np.nan									
					tn0tn1 = [np.nan, new_param[ii+1]]
				
				# This test needs just Tn0
				elif whichtest == 'ratechange':
					gg  = new_param[ii+1:wdw+1]
					# Index (idx) includes also Tn index, but in the SECOND column
					idx = [list(range(ii+1, wdw+1)), ii]
					tn0 = np.nan
					# STD = np.nan

				# This test just need the value itself.
				elif whichtest == 'flatline' or whichtest == 'attenuatedsignal' or whichtest == 'meanstd':
					gg  = new_param[ii+1:wdw+1]
					# Index (idx) includes also Tn index, but in the SECOND column
					idx = [list(range(ii+1, wdw+1)), ii]

			else:
				if ii > 0 and ii < wdw:
					gg  = np.concatenate([new_param[:ii], new_param[ii+1: wdw+1]])
					
					# Index (idx) includes also Tn index, but in the SECOND column
					idx = [list(range(ii)) + list(range(ii+1, wdw + 1)), ii] 

				elif ii >= wdw:
					gg  = new_param[ii-wdw:ii]					
					idx = [list(range(ii-wdw, ii)), ii] 


				# # Calculating std  commented on 07/aug/2017
				# STD = self.nan_watcher(gg)

			if whichtest == 'spike':			
				if ii != 0:
					tn0 = new_param[ii-1] 
					tn1 = new_param[ii+1]
					tn0tn1 = [tn0, tn1]

				# List of tuples, where each tuple stores: Group, group index, 
				# Tn and values to find SPK_REF, Tn neighbors.
				group.append((gg, idx, new_param[ii], tn0tn1))
	
			elif whichtest == 'ratechange':
				if ii != 0:
					tn0 = new_param[ii - 1]

				group.append((gg, idx, new_param[ii], tn0))

			elif whichtest == 'flatline' or whichtest == 'attenuatedsignal' or whichtest =='meanstd':
				group.append((gg, idx, new_param[ii]))


		return(group, wdw)


	#==========================================================================
	#
	#==========================================================================
	def nan_watcher(self, gg):
		'''
		This script evaluates the NaN behavior around Tn value.
		
		@date : 02/aug/2017
		@mod.1: 28/aug/2017 - FS
				- Added the calculation of MEAN, following the same condition
				  to calculate STD.
		'''

		# Nan distribution based on index position
		nan_dist = [ii for ii, val in enumerate(gg) if str(val) == 'nan']


		# "not nan_dist==True", means a empty list.
		# Empty list means mo NaN values, so a std calculation can be
		# performed.
		if not nan_dist:
			# print('No NaN!')
			# If GG is a single list.
			if len(np.shape(gg)) == 1:
				STD  = np.std(gg, ddof=1)
				MEAN = mean(gg)

			# If GG is a append of lists (or something similar, as for current)
			else:
				STD  = np.std(gg , axis=0, ddof=1)
				MEAN = np.mean(gg, axis=0)

		# If NAN is present.
		else:

			# Calculating percentage of NaNs
			percentage = len(nan_dist) * 100/len(gg)

			# # If len gg is SHORT, just the total amount of NaNs will be taken into 
			# # account. If longer, then a NaN distribution analysis will be 
			# # performed, with the aim to utilize the group extracted.
			if len(gg) <= 5:
				# If the NaNs percentage is equal or more than 40%.
				if percentage >= 40:
					# print('Std group are: ', gg)
					# print('NaN % is ', percentage)
					STD  = np.nan
					MEAN = np.nan
			
				# If Nans percentage is less than 40%
				else:
					# print('Std group are: ', gg)
					# print('NaN % is ', percentage)
					# If GG is a single list.
					if len(np.shape(gg)) == 1:
						STD  = np.nanstd(gg, ddof=1)
						MEAN = np.nanmean(gg)

					# If GG is a append of lists (or something similar, as for current)
					else:
						STD  = np.nanstd(gg , axis=0, ddof=1)
						MEAN = np.nanmean(gg, axis=0) 			

			# This part is to analyze more deeply the presence of nan in LONGER
			# groups.
			else:
				# print('More than 5 elements')
				# More than 60% of NaN, STD is not calculated.
				if percentage >= 60:
					# print('Std group are: ', gg)
					# print('NaN % is ', percentage)
					STD  = np.nan
					MEAN = np.nan

				else:
					# print('Less than 60% of Nan')
					# Verifying the sequence of nan. 1 means nans neighbors
					# If >= 3 Nan in sequence, in diff means two numbers 1,
					# STD is not calculated.
					nan_diff = np.diff(nan_dist)

					# Counting numbers 1 present
					count_ones = [nn for nn in nan_diff if nn == 1]
					
					# Several Nan, but verifying the real position of nan
					if len(count_ones) >= 2:
						# print('NaN neighbors present')
						diff_zeros = np.diff(nan_diff)
						count_zeros = [nn for nn in diff_zeros if nn == 0]

						# One zero means 3 Nan in sequence, and then no STD is 
						# calculated.
						if len(count_zeros) >= 1:
							# print('At least 3 NaN in sequence.')
							STD  = np.nan
							MEAN = np.nan

						else:
							# If GG is a single list.
							if len(np.shape(gg)) == 1:
								STD  = np.nanstd(gg, ddof=1)
								MEAN = np.nanmean(gg)

							# If GG is a append of lists (or something similar, as for current)
							else:
								STD  = np.nanstd(gg , axis=0, ddof=1)
								MEAN = np.nanmean(gg, axis=0)
					else:
						# print('Less than 2 ones present')
						STD  = np.nanstd(gg, ddof=1)
						MEAN = np.nanmean(gg)

		return(STD, MEAN)

	#==========================================================================
	#
	#==========================================================================
	def selecting_tests(self):	
		'''
		Script to verify what parameter is being analyzed and what kind of tests
		will be applyed, take into account what the importance of each test
		for each parameter.

		@author: fncsobral
		@date  : 31/jul/2017
		'''
		# print(self.many_param)


		if any([True for pp in self.many_param if self.name == pp]):
			# Tests name
			required     = ['Gross Range']
			strong_recom = ['Spike', 'Rate Change', 'Flat Line']
			suggested    = ['Attenuated Signal']

		# Tests and their hierarchy for WAVE
		elif self.name == 'wave':
			required     = ['Flat Line', 'Bulk Wave Param MxMn', 'Rate Change']
			strong_recom = ['Mean Std']

		# Tests and their hierarchy for CURRENT
		elif self.name == 'current':
			required     = ['Current Speed', 'Current Direction', 'Horizontal Velocity', 'Flat Line']
			strong_recom = ['UV Rate Change', 'UV Spike', 'Current Gradient'] 


		# Grouping the tests to be performed. 
		# Wave and Current for a while does not have suggested tests.
		# !! I dont remember what is for "tst" list...
		if (not self.tests and self.name != 'wave') and (not self.tests and self.name != 'current'):
			tst = ['Required', 'Strongly Recommended', 'Suggested']  # ??? what is for???
			tst_hierarchy = required + strong_recom + suggested

		elif (not self.tests and self.name == 'wave') or (not self.tests and self.name == 'current'):
			tst = ['Required', 'Strongly Recommended']
			tst_hierarchy = required + strong_recom

		elif self.tests == 1:
			tst = ['Required']
			# This does not share changes between both
			tst_hierarchy = required

		elif self.tests == 2:
			tst = ['Required', 'Strongly Recommended']

			# This does not share changes between both
			tst_hierarchy = required + strong_recom


		return(tst_hierarchy)


	#==========================================================================
	#
	#==========================================================================
	def bursts_eval(self):
		'''	
		This script [for a while] just perform the mean over the 20 seconds
		of sampling data from WQMX and SUNA.

		'''

		### DEVO INTRODUZIR A SERIE TEMPORAL BRUTA DO PARAMETRO E SEU DATETIME.
		### ESSE PROCESSAMENTO DEVE VIR ANTES DO QUE O time_data_organizing
		### PARA OS PARAMETROS DO WQMX E SUNA.



		# Verifying wqmx/suna bursts difference time
		dff = np.diff(self.date)


		# Getting the start time for each bursts. Choosed 20 sec as limit to verify
		# just values from different hours [for WQMX].,
		# For SUNA, the maximum bursts can be 32/hour.
		if self.sensorNM == 'wqmx':
			fd_st = [idx + 1 for idx, nn in enumerate(dff) if nn > 20]
			fd_st = np.concatenate([[0], fd_st])
		elif self.sensorNM == 'suna':
			fd_st = [idx + 1 for idx, nn in enumerate(dff) if nn > 32]
			fd_st = np.concatenate([[0], fd_st])


		# Ending list, excluding the first element, its value is zero and cannot subtract
		# it.
		fd_nd = list(np.array(fd_st[1:]))
		fd_nd = np.concatenate([fd_nd, [len(self.date)-1]])

		# messages(2, tgr=tgr)

		# Verifying the number of samples
		nbs = list()
		for ss, nn in zip(fd_st, fd_nd):
			nbs.append(len(range(ss, nn)) + 1)

		# Verifying index for time sampling with less than 10 (half of measurements
		# estipulated)
		idx_amount_sampling = [idx for idx, vv in enumerate(nbs) if vv < 10]

		# Eliminating the indexes from range with less than the estipulated sampling
		try:
			# In case with more than one index
			if len(idx_amount_sampling) > 1:
				for ii in idx_amount_sampling:
					fd_st.pop(ii)
					fd_nd.pop(ii)
			# Just one index
			else:
				fd_st.pop(idx_amount_sampling)
				fd_nd.pop(idx_amount_sampling)
		except:
			pass


		# Creating range list
		ranges = list()
		for ss, nn in zip(fd_st, fd_nd):
			ranges.append(range(ss, nn))

		# Performing the mean value for each hour, without any previous treatment 
		# (for a while)
		mean_params = dict()
		for kk in self.parameter.keys():

			pp = np.array(self.parameter[kk])
			_mean = list()

			# loop into range ranges
			# Appending mean values	and selecting the round timestamp
			for ii, rr in enumerate(ranges):
				
				# Getting selecting parameter range values.
				rng = pp[rr]		
		
				if kk == 'timestamp':
					# Getting datetime
					ddtm = dtm.fromtimestamp(rng[0])
					
					# Recreating epoch with a round hour and appending.
					_mean.append(calendar.timegm(dtm(ddtm.year, ddtm.month, ddtm.day, ddtm.hour).timetuple()))


				elif kk == 'reference_utc_time':
					# Selecting just the first time (in string format type)
					ref_time = rng[0]

					# Appending 
					_mean.append(ref_time)

				else:
					_mean.append(np.mean(rng))

					
			# Storing into dictionary
			mean_params[kk] = _mean


		return(mean_params)


	#==========================================================================	
	# FOR GROSS RANGE
	#==========================================================================
	def grss_rng_hdw_env_limits(self):
		"""

		"""
		# ============================ HARDWARE THRESHOLDS ====================
		
		# WQMX
		# Temperature
		# font: http://wetlabs.com/wqm
		hdw_temperature = (-5, 35)


		# ------------------------------ Obtaining Salinity -----------------------
		# The function also needs temperature and pressure (surface pressure (1 atm 
		# == 10.1325 dbar)).
		# 0 conductivity == 0 PSU    

		# Limits for conductivity (values giving in conductivity in manual)
		Con_min_hdw = 0
		Con_max_hdw = 90

		temp  = [hdw_temperature[0], hdw_temperature[1]]
		press = 10.1325

		sal1 = gsw.SP_from_C(90, -5, press)
		sal2 = gsw.SP_from_C(90, 35, press)

		# Verifying the which are the maximum value.
		# The lower the temperature the higher the conductivity.
		sal_max = np.max([sal1, sal2])

		hdw_salinity= (0, sal_max)


		# ???? DO: there is no range for this measurement
		# Using another sensor as reference: that stands for 0-450 micromol/kg
		# Acconding to my conversion, the value for mg/l is 14349,5 mg/l [need revision]
		hdw_do = (0, 14349.5)

		# Chlorophyl
		# Units: microgram/L [source: http://wetlabs.com/eco-triplet]
		hdw_chla = (0, 50)

		# Turbidity
		# Values found in WQM manual, pg 4 as Turbidity. File ".dat" with raw data,
		# has tips that what I am treating here is turbidity (NTU)
		hdw_turbidity = (0, 25)

		# Cdom
		# Units in manual are in ppb. [another source: http://wetlabs.com/eco-triplet]
		hdw_cdom = (0, 375)

		# SUNA
		# ????
		hdw_nitrate = (0, 3000)

		# SATPH
		# pH: http://satlantic.com/seafet
		hdw_ph = (6.5, 9)

		# ATM
		# https://goo.gl/gH4zXi
		# measurement unit: mb
		hdw_press    = (800, 1060)
		
		# https://goo.gl/E0YaNl (as reference, dont know the manufacturer from ours) 	
		hdw_temp     = (-40,  60)
		hdw_humidity = (0  , 100)
		
		# https://goo.gl/RhwUam
		# measurement unit: speed - m/s; dir - degrees
		hdw_wnd_spd  = (0, 100)
		hdw_wnd_dir  = (0, 360)

		# https://goo.gl/pXuGlz
		# measurement unit: Wm2
		hdw_rad      = (0, 1500)

		# https://goo.gl/SrC3MY
		# measurement unit: ppm
		hdw_co2 = (0, 5000)

		# https://goo.gl/3R8c4p
		# meansurement: mm
		hdw_precip = (0, 50)


		# =========================== ENVIRONMENTAL THRESHOLDS ================
		env_temperature = ( 10,   35)
		env_salinity    = (  0,  100)
		
		# [???] Without reference
		# Value obtained by mean(Turb)+-(2*std(Turb))
		# WHY TURB?? I DONT REMEMBER.....FS 06/AGO/2016 ???? 06/04/2017
		env_do = (0, 15)


		# [***] means: Based on: Ecossistema costeiro subtropical: 
		# nutrientes dissolvidos, fitopl?ncton e cloroflla-a 
		# e suas relacoes com as condicoes oceanograficas na regiao  
		# de Ubatuba, SP (Aidar, E., 1993) [***]
		env_chla = (0, 7)


		# [???] Without reference
		# Value obtained by mean(Turb)+(3*std(Turb)) [apprx. to next up value] 
		env_turbidity = (0, 13)

		# Rough analysis, by eye for SSB timeseries (in ppb)
		env_cdom =(0, 10)

		# SUNA
		# [***]
		env_nitrate = (0, 10)

		# SATPH
		# By visual and simple estimupulation over data
		env_ph = (7.75, 8.25)

		# ATM
		env_press    = (980, 1030)
		env_temp     = ( 10,   35)
		env_humidity = (  0,  100)
		env_wnd_spd  = (  0,   25) 
		env_wnd_dir  = (  0,  360)	
		env_rad      = (  0, 1200)
		env_co2      = (300,  500)
		env_precip   = (  0,   50)


		# =========================================================================
		# Storing into dictionary
		grss_rng = {
					'hardware' : {
								  # wqmx
								  'temperature'  : hdw_temperature,
								  'salinity'     : hdw_salinity   ,
	  							  'do'           : hdw_do         ,	  							  	  							 
	  							  'chla'         : hdw_chla       ,
	  							  'turbidity'    : hdw_turbidity  ,
								  'cdom'         : hdw_cdom		  ,
								  # suna
								  'nitrate'      : hdw_nitrate    ,
								  # satph
								  'ph'           : hdw_ph         ,
	  							  # atm
	  							  'avg_press'    : hdw_press      ,
								  'avg_temp'     : hdw_temp       ,
								  'avg_humidity' : hdw_humidity   ,
								  'avg_wnd_spd'  : hdw_wnd_spd    ,
								  'avg_wnd_dir'  : hdw_wnd_dir    ,
								  'avg_radiation': hdw_rad        ,
								  'atm_co2'      : hdw_co2        ,
								  'precipitation': hdw_precip        
								  },
					'environment':{
								   # wqmx
								   'temperature'  : env_temperature,
								   'salinity'     : env_salinity   ,
								   'do'           : env_do         ,								   								   
								   'chla'         : env_chla       ,
	   							   'turbidity'    : env_turbidity  ,
								   'cdom'         : env_cdom       ,
								   # suna
								   'nitrate'      : env_nitrate    ,
								   # satph
								   'ph'           : env_ph         ,
								   # atm
	   							   'avg_press'    : env_press      ,
								   'avg_temp'     : env_temp       ,
								   'avg_humidity' : env_humidity   ,
								   'avg_wnd_spd'  : env_wnd_spd    ,
								   'avg_wnd_dir'  : env_wnd_dir    ,
								   'avg_radiation': env_rad        ,
								   'atm_co2'      : env_co2        ,
								   'precipitation': env_precip         
								  }
				    }


		return(grss_rng)


	#==========================================================================
	# FOR CURRENT DATA
	#==========================================================================
	def current_decomposition(self):
		"""
		This script maintains North as 0 degrees, and angles growing
		clockwise.

		_dir and _vel are arrays appended 
			** rows   : time
			** columns: depth 

		"""

		# Getting dimensions.
		sh = np.shape(self.curdir)

		# Loop on time (rows)
		ii = 0


		U = list()
		V = list()


		for tt in range(0, sh[0]):

			# Extracting one time
			d1 = self.curdir[tt]
			v1 = self.parameter[tt]


			# If direction and velocity not nan.
			if str(d1) != 'nan' and str(v1) != 'nan':
				# Decomposition!
				u = [vv1 * np.cos(np.radians(dd1)) for dd1, vv1 in zip(d1, v1)]
				v = [vv1 * np.sin(np.radians(dd1)) for dd1, vv1 in zip(d1, v1)]
			# If velocity and direction NAN
			else:
				u = [np.nan] * sh[1]				
				v = u


			# Appending [rows: time, columns: depth] 
			U.append(np.array(u))
			V.append(np.array(v))

		return(U, V)


	#==========================================================================
	#
	#==========================================================================
	def final_flag(dict_merged, current=False):
		'''
		Evaluation of flags hierarchy given a final flag and its timestamp, to 
		ensure the time to be analyzed.

		@date: 05/jul/2017
		'''

		FLAGS = dict()
		
		# Reorganizing flags by parameter and non by test.
		orgz_dic = invert_dic_org(dict_merged)
		

		# Removing timestamp from loop and storing in FLAGs final dictionary.
		FLAGS['timestamp'] = orgz_dic.pop('timestamp')

		# Loop by parameters [kk] and tests [qc].
		# Evaluating flags hierarchy
		for kk in orgz_dic.keys():
			param = orgz_dic[kk]
			
			# Current differentiate from the other parameters due to profile
			# where each depth has to be evaluated for final flag.
			if not current:
				flags = list()

				for qc in param.keys():
					flag_qc = param[qc]

					# Storing			
					flags.append(flag_qc)

				aflags = np.array(flags)
				# Evaluating Hierarchy
				if np.any(aflags == 9):
					FLAGS[kk] = 9
				elif np.any(aflags == 4):
					FLAGS[kk] = 4
				elif np.any(aflags == 3):
					FLAGS[kk] = 3
				elif np.any(aflags == 2):
					FLAGS[kk] = 2
				else:
					FLAGS[kk] = 1
			else:
				# Currents has flags for all bins. The bins are being placed in coluns
				# So coluns = depth and rows = time
				for ii, qc in enumerate(param.keys()):
					# Flags per depth
					if ii == 0:
						flag_qc = [param[qc]]
					else:
						flag_qc = np.append(flag_qc, [param[qc]], axis=0)


				# Evaluating Hierarchy per depth
				flags = list()
				for dd in range(np.shape(flag_qc)[1]):
					each_depth = flag_qc[:, dd]

					if np.any(each_depth == 9):
						flags.append(9)
					elif np.any(each_depth == 4):
						flags.append(4)
					elif np.any(each_depth == 3):
						flags.append(3)
					elif np.any(each_depth == 2):
						flags.append(2)
					else:
						flags.append(1)

				#Storing
				FLAGS[kk] = flags


		return(FLAGS)

#==============================================================================
# END!
#==============================================================================