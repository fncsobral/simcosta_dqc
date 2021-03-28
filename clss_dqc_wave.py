#!/usr/bin/env python3
# -*- coding:utf-8 -*-
'''
#==============================================================================
# DQC WAVE - DATA QUALITY CONTROL FOR WAVES
#==============================================================================

This tests are for the following wave parameters:
	Hs
	Hmax
	Tp
	Dp

Spreading needs to be done here...16/09

@author:fncsobral
@date  : 14/aug/2017
#==============================================================================
'''


import numpy as np


#==============================================================================
# 
#==============================================================================
class DQC_Wave(object):

	def __init__(self, new_parameter1     , parameter_name1, dqc_aux, 
		               new_parameter2=None, parameter_name2=None,
		               whtanl=None):
		'''
		INPUT:     (new_parameter1      , 
		            parameter_name1     , 
		            dqc_aux             , 
		            new_parameter2=None , 
		            parameter_name2=None,
		            whtanl=None)

			NEW_PARAMETER1: you can choose to analyzed just a parameter from
			                bulk wave parameter. But not all tests will be applyed
			                depending what parameters was choosed, because, 
			                some test use Hs as controler, limiting the 
			                analyze of the others parameters. So if you choose
			                Hs, thats ok, all tests will be applyed, but if
			                the parameter choosed is different than Hs, so you
			                probably will face this "controlling" situation.
            PARAMETER_NAME1: name of parameter1
            				 hs, tp, dp, hmax (for a while)
			NEW_PARAMETER2: same as 1, for analysis of bulk wave parameters
			PARAMETER_NAME2: same as 1, for analysis of bulk wave parameters
			WHTANL: 1 for test the first parameter and 2 to test the second
			        parameter for all the tests.
		'''

		self.new_param1 = new_parameter1
		self.name1      = parameter_name1
		self.dqcaux     = dqc_aux
		self.new_param2 = new_parameter2
		self.name2      = parameter_name2
		self.whtanl     = whtanl


	#==========================================================================
	#
	#==========================================================================
	def flat_line(self, sf):	
		'''
		QARTOD DESCRIPTION
		When some sensors and/or data collection platforms fail, the result can be 
		a continuously repeated observation of the same value. This test example 
		compares the present observation (POn) to a number (REP_CNT_FAIL or REP_CNT_SUSPECT) 
		of previous observations. POn is flagged if it has the same value as previous 
		observations within a tolerance value, EPS, to allow for numerical round-off 
		error. The value chosen for EPS should be selected carefully after 
		considering the resolution of the sensor, the effects of any data processing, 
		and the performance of the test. Similar tests evaluating first differences 
		or variance among the recent observations may be implemented. 
		Note that historical flags are not changed.

		Fail = 4 : When the five most recent observations are equal, POn is flagged
		fail.
						POn ≠ 0 AND For I = 1,REP_CNT_FAIL POn - POn-i < EPS

		Suspect = 3 : It is possible but unlikely that the present observation and 
					  the two previous observations would be equal. When the three 
					  most recent observations are equal, POn is flagged suspect.
					  For I = 1,REP_CNT_SUSPECT POn - POn-I < EPS

		Pass = 1 : Applies for test pass condition.
		'''


		EPS = {
				'hs'  : 0.01,
				'tp'  : 0.1 , 
				'dp'  : 1   ,
				'hmax': 0.1
		}


		# Verifiying which test is to be analyzed as principal
		if self.whtanl == 2:
			name      = self.name2
			new_param = self.new_param2
		else:
			name      = self.name1
			new_param = self.new_param1


		# Getting EPS value according with self.name
		eps_got = EPS[name]

		# Number of repetitions to evaluate.
		REP_CNT_FAIL    = 5
		REP_CNT_SUSPECT = 3

		# Grouping data
		group, wdw = self.dqcaux.grouping(new_param, sf, 'flatline')


		# This will be the history of flags and will be the responsible for 
		# removing values from  gg when it has flag 4, to not use then to
		# calculate the difference between time sample. Here, if a NaN is
		# present at the gg group values, flag 2 will be added.
		flag_guide = np.array([2] * len(new_param))


		# Storing list
		flags = list()


		# Loop into groups
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

			FLAGS = {name: flags}

		return(FLAGS)


	#==========================================================================
	# 
	#==========================================================================	
	def bulk_wave_param_mxmn(self):
		'''
		The operator should establish maximum and minimum values for the bulk 
		wave parameters: wave height (WVHGT), period (WVPD), direction (WVDIR), 
		and spreading (WVSP) (if provided). If the wave height fails this test, 
		then no bulk wave parameters should be released. Otherwise, suspect 
		flags are set. Operator supplies minimum wave height (MINWH), maximum 
		wave height (MAXWH), minimum wave period (MINWP), maximum wave period 
		(MAXWP), minimum spreading value (MINSV), and maximum spreading value 
		(MAXSV).

		Fail = 4 : Wave height fails range test.
					If WVHGT < MINWH or WVHGT > MAXWH, flag = 4 for
					all parameters.


		Suspect = 3 :  Wave period, wave direction, or spreading value fails range
					   test.

					   If WVPD < MINWP or WVPD > MAXWP, flag = 3.
					   If WVDIR < 0.0 or WVDIR > 360, flag = 3.
					   If WVSP < MINSV or WVSP > MAXSV, flag = 3.

	   	Pass = 1 :  Bulk parameters pass tests.
						If WVHGT ≥ MINWH and WVHGT ≤ MAXWH, and
						If WVPD ≥ MINWP and WVPD ≤ MAXWP, and
						If WVDIR ≥ 0.0 and WVDIR ≤ 360, and
						IF WVSP ≥ MINSV and WVSP ≤ MAXWV, flag = 1


		'NOTICE: UNTIL NOW, SPREADING IS NOT DONE'

		'''

		# Is exists PARAM2
		# PARAM1 MUST be Hs. If not Error.
		if self.new_param2:			
			if self.name1 != 'hs':
				raise ValueError('\n'
					'............................................. \n'
					'PARAM1 must be Hs, please correct your input! \n'
					'.............................................')

		# For this test to be performed. If just one parameter exist, this must 
		# be Hs.
		else:
			if self.name1 != 'hs':
				raise ValueError('\n'
					'In Bulk Wave Param Test, if just one parameter to be analyzed,'
					' this one MUST be Hs.')


		# As Hs is a CONTROLER for the analysis' continuity.
		# Tp limits (no idea if the values are coherent)
		# For Dp, the values are inserted directly into if statement.
		# Hs limits
		MAXWH  = 4
		MINWH  = 0 #(30 cm wave height)
		# Tp limits
		MAXWP  = 25
		MINWP  = 3

		# If there ins't a second parameter (just Hs). This test does not need
		# a guide for flags, the conditionals is just for an independent data.
		if not self.new_param2:
			hs_flags  = list()
			scd_flags = list()
			# Getting PARAM1 values and creating a nan list with the same size 
			# of param1 for PARAM2, due to loop with two variables.
			param1 = self.new_param1
			param2 = [np.nan] * len(self.new_param1)
		
		# If the second parameters exist.
		else:
			hs_flags  = list()
			scd_flags = list() 

			param1 = self.new_param1
			param2 = self.new_param2


		# LOOP in data time series.
		for frst, scd in zip(param1, param2):
			# If Hs == nan is not possible to evaluate tp and dir, flag 2.
			# If Hs is not between the acceptable limits, all BWP will receive 
			# FLAG 4.
			
			# If just PARAM1 (Hs) 
			if not self.new_param2:
				if str(frst)  == 'nan':
					hs_flags.append(9)				
				elif frst < MINWH or frst > MAXWH:
					hs_flags.append(4)
				elif frst >= MINWH and frst <= MAXWH:
					hs_flags.append(1)

			# If PARAM1 and PARAM2
			else:
				# Hs - Significant Height
				if str(frst) == 'nan':
					hs_flags.append(9)
					
					if str(scd) == 'nan':
						scd_flags.append(9)

				elif frst >= MINWH and frst <= MAXWH:
					hs_flags.append(1)
				
					# Tp - Wave Peak Period
					if self.name2 == 'tp':						
						if str(scd) == 'nan':
							scd_flags.append(9)
							
						elif scd < MINWP or scd > MAXWP:			
							scd_flags.append(3)
							
						elif scd >= MINWP and scd <= MAXWP:
							scd_flags.append(1)
							
					
					# Dir - Peak Direction
					elif self.name2 == 'dp':
						if str(scd) == 'nan':
							scd_flags.append(9)
						elif scd < 0 or scd > 360:
							scd_flags.append(3)
						elif scd >= 0 and scd <= 360:
							scd_flags.append(1)

				else:
					scd_flags.append(4)


		FLAGS = {
				 self.name1 : hs_flags,
				 self.name2 : scd_flags
				 }


		return(FLAGS)


	#==========================================================================
	#
	#==========================================================================
	def rate_change(self, MAXHSDIFF=1):
		'''
		This test is applied only to WAVE HEIGHTS, AVERAGE wave periods, and 
		parameters that are a result of expected changes due to winds and 
		constitute an integration of the whole or relevant portions of the 
		spectrum (e.g., wind waves). The test described here uses significant 
		wave height as an example. The operator selects a threshold value, 
		MAXHSDIFF, and the two most recent data points Hs(n) and Hs(n-1) are 
		checked to see if the rate of change is exceeded.

		TEST EXCEPTION: Does NOT apply to discrete parameters such as PEAK
		PERIOD or PEAK DIRECTION that may change abruptly. Some operators 
		disable this test during known extreme storms, when many wave 
		characteristics might change quickly.

		Fail = 4 : Rate of change exceeds threshold.
						|Hs(n) - Hs(n - 1)| > MAXHSDIFF,

		Suspect = 3 : N/A
						N/A

		Pass = 1 :  Test passed.
						|Hs(n) - Hs(n - 1)| ≤ MAXHSDIFF
		
		'''


		# ???? Hs, Tp e Dp são os que podem ser analizados aqui??? 28/ago

		# Verifiying which test is to be analyzed as principal
		if self.whtanl == 2:
			name      = self.name2
			new_param = self.new_param2
		else:
			name      = self.name1
			new_param = self.new_param1


		# Rate of Change for WAVE is intended just for Tn and Tn0, so the use
		# of function GROUPING is not necessary.
		lg = len(new_param)
		rng0 = range(0, lg-1)
		rng1 = range(1, lg)

		# Flag guide starts with a default value of 2.
		flag_guide = np.array([2] * lg)
		
		# Starting with FLAG 2, 'cause the first Tn is not evaluated.
		flags = [2]

		# Loop in Tn and Tn0 for all timeserie long.
		for N0, N in zip(rng0, rng1):

			Tn0 = new_param[N0]
			Tn  = new_param[N]


			# ----------------------- FLAG CONDITIONALS -----------------------
			if str(Tn) == 'nan':
				flags.append(9)
				flag_guide[N] = 9 

			elif str(Tn0) == 'nan' or flag_guide[N - 1] == 4 or flag_guide[N - 1] == 2:
				flags.append(2)

			elif np.abs(Tn - Tn0) > MAXHSDIFF:
				flags.append(4)
				flag_guide[N] = 4

			else:
				flags.append(1)
				flag_guide[N] = 1

		# Storing
		FLAGS = {name: flags}

		return(FLAGS)


	#==========================================================================
	#
	#==========================================================================
	def mean_std(self, sf):
		'''
		Check that TSVAL value is within limits defined by the operator. Operator 
		defines the period over which the mean and standard deviation are 
		calculated and the number of allowable standard deviations (N).
		
		Fail = 4 : N/A

		Suspect = 3 : TSVAL is outside operator-supplied MEAN plus/minus N * SD.
					  If TSVAL < (MEAN - N * SD) or TSVAL > (MEAN + N * SD)

		Pass = 1 : TSVAL passes test.
						If TSVAL ≥ (MEAN – N * SD) and TSVAL ≤ (MEAN + N * SD)
		'''


		# Verifiying which test is to be analyzed as principal
		if self.whtanl == 2:
			name      = self.name2
			new_param = self.new_param2
		else:
			name      = self.name1
			new_param = self.new_param1



		# Defining N, the number of SD that will be allowed.
		N = 4

		# Grouping data
		group, wdw = self.dqcaux.grouping(new_param, sf, 'meanstd')

		# This will be the history of flags and will be the responsible for 
		# removing values from  gg when it has flag 4, to not use then to
		# calculate the difference between time sample.
		flag_guide = np.array([2] * len(new_param))

		# Storing list
		flags = list()

		for ii, GG in enumerate(group):
			# Extracting from GG
			Tn  = GG[2]
			# idx_tn = GG[1][1]
			idx_gg = GG[1][0]
			gg = np.array(GG[0])


			# Statement for flags evaluation. Flag 4 values, must be 
			# desconsidered from the analysis. 
			# In the first loop, none flag exist.
			if ii == 0:
				SD, MEAN = self.dqcaux.nan_watcher(gg)
			else:
				# Selecting the flag's group within the main flag_guide
				flag_gg = flag_guide[idx_gg]

				# When having flag 4, insert nan in group values
				gg[flag_gg==4] = np.nan

				# Calculating SD
				SD, MEAN = self.dqcaux.nan_watcher(gg)


			# Conditionals.
			if str(Tn) == 'nan':
				flags.append(9)
			else:
				if str(MEAN) == 'nan' or str(SD) == 'nan':
					flags.append(2)
				else:
					if Tn < (MEAN - N * SD) or Tn > (MEAN + N * SD):		
						flags.append(3)
					elif Tn >= (MEAN - N * SD) or Tn <= (MEAN + N * SD):
						flags.append(1)

		FLAGS = {
				name :flags,
		}


		return(FLAGS)

#==============================================================================
# END!
#==============================================================================