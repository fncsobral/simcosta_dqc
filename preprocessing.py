#!/usr/bin/env python3
# -*- conding: utf-8 -*-
"""
#==============================================================================
# Script to prepare data for QC
#==============================================================================




@author: fncsobral
@date  : 11/jul/2017
#==============================================================================
"""

import calendar, copy, os, pickle
from glob import glob
import numpy as np
from datetime import datetime as dtm


#==============================================================================
# ATM/WAVE/CURRENT
#==============================================================================
def preprocessing_atm_wave_current_satph(_param, ID, buoyNM, param_name, tgr=False):
	'''
	Transforms timestamp date format got from simcosta server to epoch date,
	ordering all data ascending.

	Also, arrange latitude and longitude order.

	Also, standardize parameters name.

	Also, plot figures for the time period.


	OUTPUT
		-param_reorganized
	
	@date: 30/jun/2017
	@mod.1: 11/jul/2017 - FS:
			* Introduction of wave and current in the same funciton. The main
			script to use this function moved as well.
	'''


	messages(1, tgr=tgr)


	# Due to difference between variable names.
	if param_name == 'atm':
		if ID < 20: 
			timestamp = _param['timestamp']
		elif ID >= 20:
			timestamp = _param['DATA_COLETA']
	
	elif param_name == 'wave' or param_name == 'current':
		timestamp = _param['DataTimeStamp']
	
	elif param_name == 'satph':
		timestamp = _param['DATETIME']
	

	year     = list()
	month    = list()
	day      = list()
	hour     = list()
	_min     = list()

	for tt in timestamp:
		year.append(int(tt[0:4]))
		month.append(int(tt[5:7]))
		day.append(int(tt[8:10]))
		hour.append(int(tt[11:13]))
		_min.append(int(tt[14:16]))


	# Creating epoch dates
	epoch    = list()
	ref_time = list()
	for yy, mm, dd, HH, MM in zip(year, month, day, hour, _min):
		epc = calendar.timegm(dtm(yy, mm, dd, HH, MM).timetuple())
		epoch.append(epc)

		# NÃO SEI MAIS SE AQUI DEVE TER O UTCFROM...OU NÃO...09/OUT/2017
		rf_tm = dtm.fromtimestamp(epc).strftime("%d/%m/%Y %H:%M")
		ref_time.append(rf_tm)


	# Replacing original timestamp for epoch
	if param_name == 'atm':
		if ID < 20:
			_param['timestamp'] = epoch
		elif ID >= 20:
			_param['DATA_COLETA'] = epoch
	
	elif param_name == 'wave' or param_name == 'current': 
		_param['DataTimeStamp'] = epoch
	
	elif param_name == 'satph':
		_param['DATETIME'] = epoch


	# Sorting epoch date and getting its indexes
	sort_epoch = np.sort(epoch)
	idx = np.argsort(epoch)

	
	# Inserting a NEW KEY as referencing time, to create its space into dict.
	_param['reference_utc_time'] = ref_time


	# parameters will be used to stores the parameters of atm_param but
	# in ascending order.
	parameters = copy.deepcopy(_param)


	# Ordering all timeseries 
	for ii, IDX in enumerate(idx):
		for kk in _param.keys():
			if kk == 'Latitude' or kk == 'Longitude':
				data = -_param[kk][IDX]/100
			else:
				data     = _param[kk][IDX]

			# Replacing values by the ordering ones.
			parameters[kk][ii] = data

	# Reorganizing parameters name and selecting just the usable to QC.
	# Due to diference in keys name from the new dataset requested from the server
	# I need to recreate the keys with the same name as appears in grss_rng_hdw_env_limits, below.
	if param_name == 'atm':
		# Lobo and Axys Buoys have different keys field, so I must create one
		# for each.
		if ID < 20:
			param_reorganized = {
						   'avg_radiation'     : parameters['Solar_Radiation_Average_Reading'  ],
						   'timestamp'         : parameters['timestamp'                        ],
						   'reference_utc_time': parameters['reference_utc_time'               ],
						   'avg_wnd_dir'       : parameters['Average_wind_direction'           ],
						   'avg_wnd_spd'       : parameters['Average_wind_speed'               ],
						   'avg_humidity'      : parameters['Average_Humidity'                 ],
						   'avg_press'         : parameters['Average_Pressure'                 ],
						   'avg_temp'          : parameters['Average_Air_Temperature'          ],
						   'avg_dew_pnt'       : parameters['Average_Dew_Point'                ],
						   'gusts'             : parameters['Last_sampling_interval_gust_speed']
			}
		elif ID >= 20:
			param_reorganized = {
							'avg_radiation'     : parameters['RAD_INCID'         ],
							'timestamp'         : parameters['DATA_COLETA'       ],
							'reference_utc_time': parameters['reference_utc_time'],
							'avg_wnd_dir'       : parameters['DVT'               ],
							'avg_wnd_spd'       : parameters['IVT'               ],
							'avg_humidity'      : parameters['U_REL'             ],
							'avg_press'         : parameters['P_ATM'             ],
							'avg_temp'          : parameters['T_AR'              ],
							'precipitation'     : parameters['PRECIP'            ],
							'atm_co2'           : parameters['CO2_HIGH'          ]
				}


	elif param_name == 'wave':
		param_reorganized = {
			   	'dp'                : parameters['Mean_Wave_Direction_deg'       ],
			   	'timestamp'         : parameters['DataTimeStamp'                 ],
			   	'reference_utc_time': parameters['reference_utc_time'            ],
			   	'hmax'              : parameters['Hmax_Maximum_Wave_Height_m'    ],
			   	'spreading'         : parameters['Mean_Spread_deg'               ],
			   	'tp'                : parameters['TP_Peak_Period_seconds'        ],
			   	'hs'                : parameters['Hsig_Significant_Wave_Height_m']
		}

	elif param_name == 'current':

		# print('Salinity = ', parameters['Average_Conductivity_Siemens_m'])
		# import time
		# time.sleep(10)

		# Already extracting VELOCITY and DIRECTION from resultant string.
		# Dir/Vel [in this order] (turning in array)
		dir_vel = parameters['Resultant_String']

		# Getting number of cells
		nb_cells = int(np.unique(parameters['ADCP_Cells'])[0])


		# import time
		# print('tamanho do dir_vel: ', np.shape(dir_vel))
		# print('nb_cells: ', nb_cells)
		# print('type nb_cells: ', type(nb_cells), '\n'), time.sleep(5)
		# print('dir_vel: ', dir_vel, '\n')
		# time.sleep(.5)



		# Loop into colected data
		for ii, nn in enumerate(dir_vel):
			# print('Entrou no loop...')
			# print('nn = ', nn)
			# print('len nn = ', len(nn))
			# import time
			# time.sleep(.2)		


			if str(nn) == 'nan' or len(nn)/4 == nb_cells*2-1:
				# print('Entrou no NAN')
				# print('nb_cells: ', nb_cells)
				# print('Criando listas de NANs')
				_dir2 = [np.nan] * nb_cells
				# print('\n\n')
				_vel2 = [np.nan] * nb_cells
				# print('Saindo do Nan?')
				# print('ii = ', ii)
				#time.sleep(10)

			else:
				tmp = np.array(nn.split('@&2C'))
				# print('tmp: ', tmp, '\n')
				# print('len tmp = ', len(tmp))

				# Creating index vector for selecting dir and vel below.
				dd = list(range(1, len(tmp), 2))
				# print('dd: ', dd)		

				vv = list(range(0, len(tmp), 2))
				# print('vv: ', vv, '\n'), #time.sleep(.2)
				

				# Selecting dir and vel
				_dir = tmp[dd]
				# print('_dir: ', _dir)

				_vel = tmp[vv]
				# print('_vel: ', _vel, '\n'), #time.sleep(.2)

				# converting into integer and transforming in m/s the velocity
				_dir2 = [int(_d)      for _d in _dir]
				# print('_dir2: ', _dir2)

				_vel2 = [int(_v)/1000 for _v in _vel]
				# print('_vel2: ', _vel2, '\n'), #time.sleep(.2)
				# time.sleep(.2)


			#appending direction and velocity
			if ii == 0:
				# print('ii == 0')


				_dir3 = _dir2
				_vel3 = _vel2
				ii += 1

			elif ii == 1:			
				# print('ii == 1')


				_dir3 = np.append([_dir3], [_dir2], axis=0)
				_vel3 = np.append([_vel3], [_vel2], axis=0)				
				ii += 1

				# print('_dir3: ', _dir3)
				# print('_vel3: ', _vel3, '\n'), #time.sleep(.2)




			elif ii > 1:
				# print('ii > 1')
				_dir3 = np.append(_dir3, [_dir2], axis=0)
				_vel3 = np.append(_vel3, [_vel2], axis=0)


				# print('_dir3: ', _dir3)
				# print('_vel3: ', _vel3, '\n'), #time.sleep(.2)


		param_reorganized = {
				'temperature'       : parameters['Average_Temperature_C'],
				'salinity'          : parameters['Average_Conductivity_Siemens_m'],
				'direction'         : _dir3                              ,
				'velocity'          : _vel3                              ,
				'timestamp'         : parameters['DataTimeStamp'        ],
				'reference_utc_time': parameters['reference_utc_time'   ]
		}
	elif param_name == 'satph':
		param_reorganized = {
			   	'ph'                : parameters['PH_INT'            ],
			   	'ph_ext'            : parameters['PH_EXT'            ],
			   	'temperature'       : parameters['TEMP'              ],
				'timestamp'         : parameters['DATETIME'          ],
				'reference_utc_time': parameters['reference_utc_time']
		}

	

	# # Salvando para comparar as horas e verificar se estão corretas. FS [02/oct/2017]
	# with open('test_hour/' + buoyNM + param_name + '.pkl', 'wb+') as fl:
	# 	pickle.dump( parameters['reference_time_UTC'], fl)



	return(param_reorganized)



#==============================================================================
# WQMX/SATPH
#==============================================================================
def preprocessing_wqmx_suna(data_param, buoyNM, param_name, tgr=False):
	'''
	Transforms timestamp date format got from simcosta server to epoch date,
	ordering all data ascending.

	Also, standardize parameters name.

	OUTPUT
		-param_reorganized
	
	@date: 10/jul/2017
	'''

	messages(1, tgr=tgr)


	# Obtaining the time that is the exactly burst time sampling.
	# TIMESTAMP is already in epoch value but does not contains the sampling 
	# bursts time, for each hour its value is the same.[ 18/jul/2017]
	# timestamp   = data_param['TIMESTAMP']
	bursts_timetag2 = data_param['TIMETAG2'] 
	bursts_datedat  = data_param['DATEDAT' ]

	# Transforming into EPOCH
	year   = list()
	month  = list()
	day    = list()
	hour   = list()
	minute = list()
	second = list()
	for dtdt, ttag2 in zip(bursts_datedat, bursts_timetag2):
		year.append(int(dtdt[:4    ]))
		month.append(int(dtdt[5:7  ]))
		day.append(int(dtdt[8:10   ]))
		hour.append(int(ttag2[:2   ]))
		minute.append(int(ttag2[3:5]))
		second.append(int(ttag2[6:8]))



	# Epoch
	epoch    = list()
	ref_time = list()
	for yy, mm, dd, HH, MM, SS in zip(year, month, day, hour, minute, second):
		epc = calendar.timegm(dtm(yy, mm, dd, HH, MM, SS).timetuple())
		epoch.append(epc)

		# Creating the referencing time
		rf_tm = dtm.fromtimestamp(epc).strftime("%d/%m/%Y %H:%M")
		ref_time.append(rf_tm)



	# Sorting epoch date and getting its indexes
	sort_timestamp = np.sort(epoch)
	idx            = np.argsort(epoch)



	# Creating key of reference time 
	data_param['reference_utc_time'] = ref_time


	# PARAMETERS will be used to stores the parameters of wave_param but
	# in ascending order.
	parameters = copy.deepcopy(data_param)


	# Ordering all timeseries 
	for ii, IDX in enumerate(idx):
		for kk in data_param.keys():
			data = data_param[kk][IDX]
			parameters[kk][ii] = data


	# Due to diference in keys name from the new dataset requested from the server
	# I need to recreate the keys with the same name as appears in grss_rng_hdw_env_limits,
	# as is below.
	if param_name == 'wqmx':
		param_reorganized = {
					   	'temperature'       : parameters['T_W'               ],
					   	'pressure'          : parameters['PRESS'             ],
					   	'salinity'          : parameters['SALINITY'          ],
					   	'turbidity'         : parameters['NTU_700'           ],
					   	'chla'              : parameters['FLUOR'             ],
					   	'cdom'              : parameters['CDOM'              ],
					   	'do'                : parameters['DO'                ],
					   	'timestamp'         : sort_timestamp                  ,
					   	'reference_utc_time': parameters['reference_utc_time'] 
					   	# 'timestamp'  : parameters['TIMESTAMP']
		}

	elif param_name == 'suna':
		param_reorganized = {
				'nitrate_um'        : parameters['NITRATE_UM'        ],
				'nitrate'           : parameters['NITRATE_MG'        ],
				'timestamp'         : sort_timestamp                  ,
				'reference_utc_time': parameters['reference_utc_time']
		}


	

	# # Salvando para comparar as horas e verificar se estão corretas. FS [02/oct/2017]
	# with open('test_hour/' + buoyNM + param_name + '.pkl', 'wb+') as fl:
	# 	pickle.dump(parameters['reference_time_UTC'], fl)


	return(param_reorganized)




#==============================================================================
# MESSAGES
#==============================================================================
def messages(msg_id, tgr=False):
	'''
	Messages to be displayed when requested. 
	This script is inteded for clean up the programming visual.

	@author: fncsobral
	@date  : 12/jul/2017
	'''

	if not tgr:
		pass
	else:
		if msg_id == 1:			
			print('')
			print('')
			print('')
			print('*************************** ATENÇÃO ************************')
			print('*********** SERVIDOR ESTA ADICIONANDO 3H SOBRE AS UTC ******')
			print('************** preprocessing.py (11/jul/2017) **************')
			print('')
			print('')
			print('')


		if msg_id == 2:
			print('')
			print('')
			print('')
			print('*************************** ATENÇÃO ************************')
			print(' ESTOU ELIMINANDO A ULTIMA HORA POIS ESTA NÃO É COMPLETA ***')
			print('******* bursts_qartod_preprocessing.py (18/jul/2017) *******')
			print('')
			print('')
			print('')			


#==============================================================================
# END!
#==============================================================================
