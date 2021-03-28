#!/usr/bin/env python3
# -*- coding:utf-8 -*-
'''
#==============================================================================
# DQC CURRENT - DATA QUALITY CONTROL FOR CURRENTS
#==============================================================================

This tests are for current profiles (velocity and direction)

@author:fncsobral
@date  : 29/aug/2017
#==============================================================================
'''

# from clss_dqc_aux import DQC_aux
import numpy as np

#==============================================================================
#
#==============================================================================
class DQC_Current(object):

	def __init__(self, new_velocity, new_direction,
					   u_velocity  , v_velocity,
					   dqc_aux):
		'''
		INPUT:
			NEW_VELOCITY : 
			NEW_DIRECTION:
			U_VELOCITY   :
			V_VELOCITY   :
		'''

		self.new_velocity  = new_velocity
		self.new_direction = new_direction
		self.u             = u_velocity
		self.v             = v_velocity
		self.dqcaux        = dqc_aux
		
		self.name_vel      = 'velocity'
		self.name_dir      = 'direction'
		self.name_u        = 'u_component'
		self.name_v        = 'v_component'


	#==========================================================================
	# 
	#==========================================================================
	def current_speed(self, SPDMAX=1.20):
		"""
		Current speed is typically provided as a positive value. This test checks 
		for unrealistically high current speed values and is applied to each depth 
		bin (i). The maximum current speed should be set based on the environment 
		in which the instrument will be deployed, as well as for all reasonable 
		high-speed anomalies.


		Fail    = 4 :  If the current speed [CSPD(i)] exceeds a reasonable maximum
				       value (SPDMAX), the measurement fails.

				                 IF CSPD(i) > SPDMAX
		Suspect = 3 : N/A
		Pass    = 1 : If the current speed [CSPD(i)] is less than or equal to a 
					  reasonable maximum value (SPDMAX), the measurement passes.
								 IF CSPD(i) ≤ SPDMAX
		"""

		# SPDMAX=Based on the maximum from all depths along all the time available, 
		# does not pass through 0.4. But maybe the double of this value 
		# can be possible: FS 15/may/2017


		profiles = list()

		# Loop into profiles (can be called time as well)
		for prof in self.new_velocity:
			# _bin are the cells of velocity from the profile.
			bins     = list()

			# Each depth cell
			for _bin in prof: 
				if str(_bin) == 'nan':
					bins.append(9)
				elif _bin > SPDMAX:
					bins.append(4)
				elif _bin <= SPDMAX:
					bins.append(1)

			# Appending for each profile (time data sample)
			profiles.append(np.array(bins))

		FLAGS = {
				 'current': profiles
		}

		
		return(FLAGS)


	#==========================================================================
	# 
	#==========================================================================
	def current_direction(self):
		"""
		This test ensures that the current direction values fall between 0 and 360 
		degrees, inclusive. In most	systems, 0 is reported as the absence of any 
		current and 360 degrees indicates a current to the north. This test is 
		applied to each depth bin (i).

		Fail = 4 : If current direction [CDIR(i)] is less than 0.00 degrees or 
		           greater than 360 degrees, the measurement is invalid.
					
						IF CDIR(i) < 0.00 OR CDIR(i) > 360.00
		Suspect = 3 : N/A
		Pass = 1 : If current direction [CDIR(i)] is greater than 0.00 degrees and 
		           less than or equal to 360 degrees, the measurement is valid.   

		           		IF CDIR(i) ≥ 0.00 AND CDIR(i) ≤ 360.00


		ATENÇAO: PARA NOSSO AQUADOPP ACREDITO QUE VALORES ACIMA DE 360 SEJAM
		POSSIVEIS, VERIFICAR, AQUADOPP 
		"""	

		profiles = list()

		# Loop into profiles (can be called time as well)
		for prof in self.new_direction:
			# _bin are the cells of velocity from the profile.
			bins     = list()

			# Each depth cell
			for _bin in prof: 
				if str(_bin) == 'nan':
					bins.append(9)
				elif _bin < 0.00:  #or _bin > 360.00:
					bins.append(4)
				elif _bin >= 0.00 or _bin <= 360.00:
					bins.append(1)

			# Appending for each profile (time data sample)
			profiles.append(np.array(bins))

		FLAGS = {
				 'current': profiles
		}

		
		return(FLAGS)

	#==========================================================================
	# 
	#==========================================================================
	def horizontal_velocity(self, HVELMAXX=1, HVELMAXY=1):
		"""
		Horizontal velocities u(i) and v(i) may be represented as components 
		(East-West and North-South; Alongshore and Cross-Shore: Along-shelf and 
		Cross-Shelf, Along-Isobath and Cross-Isobath, etc.) of the current speed 
		and direction. This test ensures that speeds in the respective horizontal 
		directions (HVELMAXX and HVELMAXY) are valid. Maximum allowed values may 
		differ in the orthogonal directions. This test is applied to each depth 
		bin (i).

		Fail = 4 : Horizontal velocities exceed expected maximum values in the 
		           two horizontal directions.

	       			IF ABS[u(i)] > HVELMAXX OR IF ABS[v(i)] > HVELMAXY, flag = 4

		Suspect = 3 : N/A
		Pass = 1 : Horizontal velocities fall within the expected range of values

			   		IF ABS[u(j)] ≤ HVELMAXX AND ABS[v(j)] ≤ HVELMAXY

		"""
		
		profile = list()
		for profu, profv in zip(self.u, self.v):
			bins    = list()		
			
			for _binu, _binv in zip(profu, profv):
				if str(_binu) == 'nan' and str(_binv) == 'nan':
					bins.append(9)

				elif np.abs(_binu) > HVELMAXX or np.abs(_binv) > HVELMAXY:
					bins.append(4)

				elif np.abs(_binu) <= HVELMAXX and np.abs(_binv) <= HVELMAXY:
					bins.append(1)

			# Storing in time
			profile.append(np.array(bins))


		# Storing
		FLAGS = {
				 'current':profile
		}

		return(FLAGS)


	#==========================================================================
	# 
	#==========================================================================
	def flat_line(self, sf, EPS=0.005):
		"""
		When some sensors and/or data collection platforms (DCPs) fail, the result 
		can be a continuously repeated observation of the same value. This test 
		compares the present observation (POn) to a number (REP_CNT_FAIL or 
		REP_CNT_SUSPECT) of previous observations. POn is flagged if it has the 
		same value as previous observations within a tolerance value EPS to allow 
		for numerical round-off error. This test may apply to sensor outputs as 
		well as derived values. Note that historical flags are not changed.

		FAIL = 4 : When the five most recent observations are equal, POn 
		           is flagged fail.
		           			For i=1,REP_CNT_FAIL POn - POn-i < EPS
		SUSPECT = 3 : It is possible but unlikely that the present observation and 
					  the two previous observations would be equal. When the three 
					  most recent observations are equal, POn is flagged suspect.
					  		For i=1,REP_CNT_SUSPECT POn - POn-i < EPS
		PASS = 1 : Applies for test pass condition.
		"""

		# PARA A VELOCIDADE VOU FAZER PARA AS COMPONENTES, POIS A RESULTANTE
		# PODE TER UM VALOR IGUAL ORIGINADO DE U E V DIFERENTES, OCASIONANDO
		# EM UM FALSO ALARME. 16/MAY/2017
		# 31/aug/2017: caso quisesse utilizar a resultante da velocidade e
		# direção, acredito que o resultado seria satisfatório. (realizar testes
		# e comparações)
		# APENAS REALIZADO HORIZONTALMENTE.


		groupU, wdw = self.dqcaux.grouping(self.u, sf, 'flatline')
		groupV, wdw = self.dqcaux.grouping(self.v, sf, 'flatline')


		sh = np.shape(self.u)

		# Creating one default guide list with number of depth cells, and then
		# pilling up them to form rows of lists (to perform time).
		# Array format is to allow slicing rows using lists.
		flag_guideU = np.array([[2] * sh[1]] * sh[0])
		flag_guideV = np.array([[2] * sh[1]] * sh[0])


		# Storing all flags
		flags = list()


		# Loop into groups
		for ii, (GGu, GGv) in enumerate(zip(groupU, groupV)):

			# Getting group values, group index and tn index.
			ggu     = np.array(GGu[0])
			ggv     = np.array(GGv[0])
			Tnu     = GGu[2]
			Tnv     = GGv[2]			
			idx_ggu = GGu[1][0]
			idx_ggv = GGv[1][0]
			idx_tnu = GGu[1][1]
			idx_tnv = GGv[1][1]


			if ii > 0:
				# Selecting the flag's group within the main flag_guide
				flag_ggu = flag_guideU[idx_ggu]
				flag_ggv = flag_guideV[idx_ggv]

				# When having flag 4, insert nan in group values. They are smart
				# enougth to find and replace 4 in any position of flag_gg?.
				ggu[flag_ggu==4] = np.nan
				ggv[flag_ggv==4] = np.nan


			# Transforming gg group into list, because it must be LIST due 
			# to merging with Tn code below
			ggu = list(ggu)
			ggv = list(ggv)


			# -Putting Tn and group values together. Tn will be at the last 
			# position of the array. [tgr = together]
			# -Also putting together the group and Tn indexes
			# -Sorting indexes.			
			tgr_valu    = np.array(ggu + [Tnu])
			tgr_valv    = np.array(ggv + [Tnv])

			tgr_indexu  = idx_ggu + [idx_tnu]
			tgr_indexv  = idx_ggv + [idx_tnv]

			stgr_indexu = np.argsort(tgr_indexu)
			stgr_indexv = np.argsort(tgr_indexv)


			# Sorting values, and this is will be the GRP5 already. GRP5 is 
			# independent of position, because is using all values. GRP3 should 
			# have a Tn position verification.
			grp5u = tgr_valu[stgr_indexu]
			grp5v = tgr_valv[stgr_indexv]


			# Selecting the GPR3 values
			# idx_tnu and idx_tnv are the same, just using one of them.
			if idx_tnu <= 2:
				grp3u = grp5u[:3]
				grp3v = grp5v[:3]
			else:
				grp3u = grp5u[-3:]
				grp3v = grp5v[-3:]


			# Getting the difference within groups. Axis=0 is necessary, to 
			# perform the difference by rows, preserving the depths.
			df5u = abs(np.diff(grp5u, axis=0))
			df5v = abs(np.diff(grp5v, axis=0))

			df3u = abs(np.diff(grp3u, axis=0))
			df3v = abs(np.diff(grp3v, axis=0))


			# ---------------------------- FLAG CONDITIONALS ------------------
			# If Tn [evaluated value] does not exist
			# Or group values NaN, not possible to analyze.

			# All values NaN in Tn?. Tnu and Tnv are supposedly to have the same
			# behaviour when all NAN. So, just verifying in Tnu... 
			if all(np.isnan(Tnu)):
				# This sintax insert 9 in all idx_tn? flag_guide? array.
				flag_guideU[idx_tnu] = 9
				flag_guideV[idx_tnv] = 9
				flags.append([9] * sh[1])

			# If there is any NAN value within profile, what I guess is an awkward
			# behavior. Print warning to verify deeper.
			elif any(np.isnan(Tnu)) or any(np.isnan(Tnv)):
				print('SOMETHING WRONG in FLAT LINE CURRENT...')
				# If not all values NaN something strange happens. Inserting 9
				# just to provide a flag value.
				flag_guideU[idx_tnu] = 9
				flag_guideV[idx_tnv] = 9
				flags.append([9] * sh[1])
			
			# If NaN not present in Tn?
			else:
				# Verifying NaN by depths in df5? (group values + Tn value)

				# Storing flag list by depth
				_binflags = list()


				# -----------------------------------------------Loop in DEPTH. 
				# SH is for all U timeseries, but depth is 
				# immutable, and so I can use here.
				for dd in range(sh[1]):
					
					# ------- FOR DF5U
					# Loop in time (rows) in group differences to stores a list
					# for a DD depth.
					sameDepth_intime5u = list()
					sameDepth_intime5v = list()
					
					for rr in range(0, 4):
						sameDepth_intime5u.append(df5u[rr][dd])
						sameDepth_intime5v.append(df5v[rr][dd])


					# -------- FOR DF3U
					# Loop in time (rows) in group differences to stores a list
					# for a DD depth.
					sameDepth_intime3u = list()
					sameDepth_intime3v = list()
					for rr in range(0, 2):
						sameDepth_intime3u.append(df3u[rr][dd])
						sameDepth_intime3v.append(df3v[rr][dd])

					# Transforming into array
					sameDepth_intime5u = np.array(sameDepth_intime5u)
					sameDepth_intime5v = np.array(sameDepth_intime5v)
					sameDepth_intime3u = np.array(sameDepth_intime3u)
					sameDepth_intime3v = np.array(sameDepth_intime3v)

					# Verifying if any of time (rows) is NaN for a specific DD
					# depth. FLAG 2 if so. Just one flag, because here, an 
					# depth specific evaluation is being performed.
					if any(np.isnan(sameDepth_intime5u)) and any(np.isnan(sameDepth_intime5v)):
						_binflags.append(2)

					# If NO NAN in group at this depth.
					else: 
						# If all difference values for U and V components were
						# less than EPS threshold.
						if all(sameDepth_intime5u < EPS) and all(sameDepth_intime5v < EPS):
							_binflags.append(4)
							# Inserting the flag in the Tn? index but at the DD 
							# depth.
							flag_guideU[idx_tnu][dd] = 4
							flag_guideV[idx_tnv][dd] = 4
						else:
							if all(sameDepth_intime3u < EPS) and all(sameDepth_intime3v < EPS):
								_binflags.append(3)
								# Inserting the flag in the Tn? index but at the DD 
								# depth.
								flag_guideU[idx_tnu][dd] = 3
								flag_guideV[idx_tnv][dd] = 3
							else:
								_binflags.append(1)
								flag_guideU[idx_tnu][dd] = 1
								flag_guideV[idx_tnv][dd] = 1

				flags.append(_binflags)

		FLAGS = {
				 'current': flags
		}
		
		return(FLAGS)

	#==========================================================================
	# 
	#==========================================================================
	def uv_rate_change(self, RC_VEL_FAIL=1.5, RC_VEL_SUSPECT=1):
		"""
		The difference between the most recent u, v velocity components (n) are 
		compared to the previous u, v observations (n-1). If the change exceeds 
		the specified thresholds, data are flagged fail or suspect. This test
		is applied to each depth bin (i). Some operators may wish to implement 
		the rate of change test on pitch/roll/heading outputs of fixed mounted 
		ADCPs to test for unexpected platform motion caused, for example, by a 
		ship anchor strike.

		Fail = 4 : If the absolute value of the difference u(i,n) – u(i,n-1) or
				   v(i,n) – v(i,n-1) exceeds the fail threshold RC_VEL_FAIL, the
	               velocity/direction measurements at that depth fails.

	               IF ABS[u(i,n) – u(i,n-1)] 
	               OR ABS[v(i,n) – v(i,n-1)] ≥ 	RC_VEL_FAIL 

	    Suspect = 3 : If the absolute value of the difference u(i,n) – u(i,n-1) or
					  v(i,n) – v(i,n-1) exceeds the suspect threshold
	                  (RC_VEL_SUSPECT), the velocity/direction measurements
	  				  at that depth are flagged as suspect.

	  				  IF ABS[u(i,n) – u(i,n-1)] OR 
	  				  ABS[v(i,n) – v(i,n-1)] ≥ RC_VEL_SUSPECT AND < RC_VEL_FAIL

		Pass = 1 : If the absolute value of the difference u(i,n) – u(i,n-1) and
	 			   v(i,n) – v(i,n-1) are less than the suspect threshold
				   RC_VEL_SUSPECT, the  velocity/direction measurements
				   at that depth pass.

				   IF ABS[u(i,n) – u(i,n-1)] AND 
				   ABS[v(i,n) – v(i,n-1)] < RC_VEL_SUSPECT
		"""

		# Rate of Change for CURRENT is intended just for Tn and Tn0, so the 
		# use of function GROUPING is not necessary.
		sh = np.shape(self.u)
		rng0 = range(0, sh[0]-1)
		rng1 = range(1, sh[0])
		

		# Creating one default guide list with number of depth cells, and then
		# pilling up them to form rows of lists (to perform time).
		# Array format is to allow slicing rows using lists.
		# As components U and V will be always evaluated together in flag
		# conditionals, it is not necessary to have two flag_guides for each
		# one. If one of them is bad, them the both will be bad (take a look at
		# flag conditionals, we are always using OR).
		flag_guide = np.array([[2] * sh[1]] * sh[0])


		# List to stores all flags. As the first time will not be evaluated, 
		# because we must a previous value to do it, the list starts with
		# a profile with FLAGS 2 (not evaluated).
		flags = [[2] * sh[1]]


		# Loop into groups
		# Loop in Tn and Tn0 for all timeserie long.
		for N0, N in zip(rng0, rng1):

			# Getting Tn and Tn0 values.
			Tn0u = self.u[N0]
			Tnu  = self.u[N]
			Tn0v = self.v[N0]
			Tnv  = self.v[N]

			# To store bins
			bins = list()

			# loop into bins depth
			for ii, (u0, u, v0, v) in enumerate(zip(Tn0u, Tnu, Tn0v, Tnv)):

				if N0 > 0:
					# Getting flags for Tn0. N0 is time index. ii is the time
					# index.
					# For u and v components.
					flag_tn0 = flag_guide[N0][ii]					

					if flag_tn0 == 4:
						u0 = np.nan
						v0 = np.nan


				# -------------------------- FLAG CONDITIONALS ----------------
				# If Tn? is NAN
				if str(u) == 'nan' or str(v) == 'nan':
					bins.append(9) 
					flag_guide[N][ii] = 9

				# If Tn is not NAN
				else:
					# If Tn0? were Nan, naturally (data does not exist) or
					# bad data (FLAG 4).
					if str(u0) == 'nan' or str(v0) == 'nan':
						bins.append(2)
						flag_guide[N][ii] = 2

					# If Tn and Tn0 are OK.
					else:
						if abs(u - u0) >= RC_VEL_FAIL or abs(v - v0) >= RC_VEL_FAIL:
							bins.append(4)
							flag_guide[N][ii] = 4

						elif ((abs(u - u0) >= RC_VEL_SUSPECT or abs(v - v0) >= RC_VEL_SUSPECT) 
							and  (abs(u - u0) <  RC_VEL_FAIL or abs(v - v0) <  RC_VEL_FAIL)):
							bins.append(3)
							flag_guide[N][ii] = 3

						elif abs(u - u0) < RC_VEL_SUSPECT and abs(v - v0) < RC_VEL_SUSPECT:
							bins.append(1)
							flag_guide[N][ii] = 1
			
			flags.append(bins)


		# Storing
		FLAGS = {
				 'current': flags
		}

		return(FLAGS)


	#==========================================================================
	# 
	#==========================================================================
	def uv_spike(self, sf):
		"""
		This check is for single-value spikes, specifically the u, v values at 
		point n-1. Spikes consisting of more than one data point are difficult to 
		capture, but their onset may be flagged by the rate of change test. 
		This test is applied to each depth bin (i). The spike test consists of two 
		operator-selected thresholds, uv_SPIKE_FAIL and uv_SPIKE_SUSPECT. Adjacent 
		data points u(n -2 and n 0 ) are averaged to form a spike reference 
		(u_SPK_REF), and adjacent data points v(n-2 and n) are averaged to form a 
		spike reference (v_SPK_REF). Only adjacent data points that have
		been flagged pass should be used to form the spike reference. When absent, 
		earlier observations may need to be employed. The absolute value of the 
		spike is tested to capture positive and negative spikes. Large
		spikes are easier to identify as outliers and flag as failures. Smaller 
		spikes may be real and are only flagged suspect. The thresholds may be 
		fixed values or dynamically established (for example, a multiple of the
		standard deviation over an operator-selected period). They may also be 
		expressed as a function of time (e.g., d(u)/dt) to accommodate varying 
		time increments. An alternative spike test may use a third difference 
		test, for example defined as Diff n = u(n-3) - 3* u(n-2) + 3* u(n-1) – 
		u(n).

		Fail = 4 : If the absolute value of the difference u(i,n-1) – u_SPK_REF or
				   v(i,n-1) – v_SPK_REF exceeds the fail threshold uv_SPIKE_FAIL, 
				   the velocity/direction measurements at that depth fails.

					IF ABS[u(i,n-1) – u_SPK_REF] OR ABS[v(i,n-1) –
							v_SPK_REF] ≥ uv_SPIKE_FAIL

		Suspect = 3 : If the absolute value of the difference u(i,n-1) – u_SPK_REF 
					  or v(i,n-1) – v_SPK_REF exceeds the Suspect threshold 
					  uv_SPIKE_SUSPECT, the velocity/direction measurements at
					  that depth are flagged as suspect.

					IF ABS[u(i,n-1) – u_SPK_REF] OR ABS[v(i,n-1) –
							v_SPK_REF] ≥ uv_SPIKE_SUSPECT AND <
							uv_SPIKE_FAIL

		Pass = 1 : If the absolute value of the difference u(i,n-1) – u_SPK_REF 
				   and v(i,n-1) – v_SPK_REF are less than the Suspect threshold
				   uv_SPIKE_SUSPECT, the velocity/direction measurements at
				   that depth pass

				   IF ABS[u(i,n-1) – u_SPK_REF] AND ABS[v(i,n-1)
				   – v_SPK_REF] < uv_SPIKE_SUSPECT

		"""


		groupU, wd = self.dqcaux.grouping(self.u, sf, 'spike')
		groupV, wd = self.dqcaux.grouping(self.v, sf, 'spike')
		

		# Flags storing list
		flags = list()

		# Loop into groups.
		for grpU, grpV in zip(groupU, groupV):

			ggu = grpU[0]
			ggv = grpV[0]

			Tnu = grpU[2] 
			Tnv = grpV[2]

			Tn0u = grpU[3][0]
			Tn1u = grpU[3][1]	

			Tn0v = grpV[3][0]
			Tn1v = grpV[3][1]


			# If U is NAN, the usual is to V be as well.
			if any(np.isnan(Tnu)):
				bins = [9] * np.shape(ggu)[1]
			
			# If Tn? is not NAN
			else:
				# Checking the auxiliaries for flag conditionals, SPK_REF AND 
				# SD. If any of them possess NAN then FLAG 2 will be given.
				
				# Getting STD? values 
				STD_u, _ = self.dqcaux.nan_watcher(ggu)
				STD_v, _ = self.dqcaux.nan_watcher(ggv)

				# Verifying if any of the auxiiaries are NAN. 
				if (np.isnan(STD_u).any()   or np.isnan(STD_v).any()
					or np.isnan(Tn0u).any() or np.isnan(Tn0v).any()
					or np.isnan(Tn1u).any() or np.isnan(Tn1v).any()):
					bins = [2] * np.shape(ggu)[1]
				# If none of the auxiliaries are NAN
				else:
					# Calculating SPK_REF
					SPK_REFu = np.mean([Tn0u, Tn1u], axis=0)
					SPK_REFv = np.mean([Tn0v, Tn1v], axis=0)

					# Getting threshold for FAIL.
					uv_SPIKE_FAIL = np.mean([STD_u, STD_v], axis=0) * 3

					# Getting threshold for SUSPECT.
					uv_SPIKE_SUSPECT = np.mean([STD_u, STD_v], axis=0) * 1.5


					# Conditionals
					# Loop into bins (depths)
					bins  = list()
					for tnu, tnv, refu, refv, uvsuspect, uvfail in zip(Tnu, Tnv, SPK_REFu, SPK_REFv, uv_SPIKE_SUSPECT, uv_SPIKE_FAIL):
						if np.abs(tnu - refu) >= uvfail or np.abs(tnv - refv) >= uvfail:
							bins.append(4)
						elif ((np.abs(tnu - refu) >= uvsuspect or np.abs(tnv - refv) >= uvsuspect) 
							   and (np.abs(tnu - refu) <  uvfail    or np.abs(tnv - refv)  < uvfail)):
							bins.append(3)
						elif np.abs(tnu - refu) < uvsuspect and np.abs(tnv - refv) < uvsuspect:
							bins.append(1)


			# Appending bins flags
			flags.append(bins)

		# As spike does not verify the last data, inserting flag 2
		bins = [2] * np.shape(ggu)[1]
		flags.append(bins)

		# Storing
		FLAGS = {
				 'current': flags
		}

		return(FLAGS)


	#==========================================================================
	# 
	#==========================================================================
	def current_gradient(self, CSPDDIF=0.8, CDRTDIF=400):
		"""
		Current speed is expected to change at a gradual rate with depth. A 
		current difference with depth (CSPDDIF), to be determined locally, should 
		be established and the rate of current speed difference with depth between 
		two bins determined. The same test can be run with current direction.

		Fail = 4 : If current speed at bin i, CSPD(i) exceeds current speed at bin 
		           i-1, CSPD(i-1) by a prescribed amount, CSPDDIF, the data are 
		           not valid.

								IF ABS[CSPD(i)-CSPD(i-1)] > CSPDDIF

		Suspect = 3 : N/A 
						[FS created one condition to verify velocity and direction
							together]
		Pass = 1 : If current speed at bin i, CSPD(i) change from the current 
		           speed at bin(i-1), CSPD(i-1), is less than or equal to a 
		           prescribed amount, CURDIF, the data are valid.

								IF ABS[CSPD(i)-CSPD(i-1)] ≤ CSPDDIF 
		"""
	
		# Storing List
		flags = list()

		for vel_prof, dir_prof in zip(self.new_velocity, self.new_direction):
			# Depth Velocity and Direction difference
			df_vel = np.diff(vel_prof)
			df_dir = np.diff(dir_prof)

			# Creating bins list
			bins  = list()

			# Loop into bins (depth)
			for CSPD, CDRT in zip(df_vel, df_dir):
				aCSPD = np.abs(CSPD)
				aCDRT = np.abs(CDRT)
			
				# FLAG 9
				if np.isnan(aCSPD) or np.isnan(aCDRT):
					bins.append(9)

				else:
					# FLAG 4
					if aCSPD > CSPDDIF or aCDRT > CDRTDIF:
						bins.append(4)

					# FLAG 1
					elif aCSPD <= CSPDDIF and aCDRT <= CDRTDIF:
						bins.append(1)

			# For now, the last depth (the deeper) will be flagged with 2, due to 
			# impossibility to evaluate. But in the future, I can do the gradient going
			# up and going down, with two evaluations, and all the depths with real flags. 14/jul/2017
			if bins[0] != 9:
				bins.append(2)
			else:
				bins.append(9)

			# Storing profile flags
			flags.append(bins)


		FLAGS = {
				 'current': flags
		}

		return(FLAGS)



#==========================================================================
# 
#==========================================================================


"""
### MELHORAMENTOS: 29/aug/2017
1. não sei se está tudo bem inserir apenas um nan quando nao existir um perfil,
   onde teoricamente existiriam entre 20-25 dados (dependendo do local), até 
   o momento, não está dando problemas...

2. quando tiver a série de dados completa preciso verificar se existe
   a possibilidade de ocorrer erros de não coletar alguma profundidade (bin)...
   não sei como eu saberia qual é a prof que não foi coletada...não sei se
   um NAN é inserido automaticamente já na saida do sensor... 
"""