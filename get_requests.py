#!/usr/bin/env python3
# -*- coding:utf-8 -*-
'''
#==============================================================================
# THIS SCRIPT IS THE RESTful API BETWEEN SERVER AND PYTHON APPLICATION
#==============================================================================

Script to make the data GET request using a server URL and makes to python
quality control application. After performing QC tests makes a POST request
to a URL inserting into SiMCosta server.


@author: fncsobral
@date  : 27/jun/2017
#==============================================================================
'''

import requests, pickle
import numpy as np
from preprocessing import *


#==============================================================================
# Getting data parameters from URL (GET request)
#==============================================================================
def param_get_request(param_name, ID, buoyNM, tgr=False):
	'''

	@date  : 11/jul/2017
	@mod. 1: 12/set/2017 - FS
			- update, merging with timeseries classes, for the new version of
			  DQC.
	'''

	# URLS
	if param_name == 'atm':
		# First URL is for LOBO buoys and the second for AXYS.
		if ID >= 20:
			url = 'http://www.simcosta.furg.br:3000/api/met/serie/' + str(ID)
		else:
			url = 'http://www.simcosta.furg.br:3000/api/message_01/serie/' + str(ID)
			
	elif param_name == 'wave':
		url = 'http://www.simcosta.furg.br:3000/api/message_03/serie/' + str(ID)
		
	elif param_name == 'current':
		url = 'http://www.simcosta.furg.br:3000/api/message_04/serie/' + str(ID)
		
	elif param_name == 'wqmx':
		url = 'http://www.simcosta.furg.br:3000/api/wqmx/serie/' + str(ID)

	elif param_name == 'satph':
		url = 'http://www.simcosta.furg.br:3000/api/satph/serie/' + str(ID)

	elif param_name == 'suna':
		url = 'http://www.simcosta.furg.br:3000/api/suna/serie/' + str(ID)


	try:
		req = requests.get(url)     
		JSON = req.json()


		# keys to NOT transform into float
		k_atm_axys   = ['MessageID', 'timestamp']
		k_atm_lobo   = ['HEADER', 'ID_SIMA', 'DATA_TRANSMISSAO', 'DATA_COLETA']
		k_wave       = ['DateTimeStamp', 'MessageID']
		k_adcp       = ['DataTimeStamp', 'Resultant_String', 'ADCP_Description_String', 
				       # 'Average_Conductivity_Siemens_m', 
				       'Average_Nitrate_Concentration_mg', 
				       'Average_Nitrate_Concentration_um', 'Average_Temperature_deg_C']		
		k_wqmx_satph = ['DATEDAT', 'DATETAG', 'DATETIME', 'SOURCE', 'TIMETAG2']
		k_suna       = ['DATETIME', 'SUNA_UV', 'DATETAG', 'TIMETAG2', 'DATEDAT']

		# Concatenating without repeated strings
		k_all = list(np.concatenate(np.unique([k_atm_axys  , 
			                                   k_atm_lobo  , 
			                                   k_wave      , 
			                                   k_adcp      , 
			                                   k_wqmx_satph, 
			                                   k_suna])))

		_param = dict()
		for ii in range(len(JSON)):

			_dict = JSON[ii]

			# Getting values from dictionary with parameters.
			for kk in _dict.keys(): 

				# Verifying if value exists.
				val = _dict[kk]

				if val == None or val=='NULL':
					vv = np.nan

				else:
					# Transforming into float when possible.
					if kk == 'Longitude' or kk == 'Latitude':
						vv = float(_dict[kk][:-1])
					# Verifying if value is in the list of keys to NOT transform into float.
					elif [True for kkall in k_all if kk == kkall]:
						vv = _dict[kk]
					else:
						# Adding a try exception, due to possibility of values
						# like 'Error 7', when some error occured.
						try:
							vv = float(_dict[kk])

						except:
							vv = np.nan


				# Ajeitando o append na lista a ser inserida no dicionario, de acordo com o indice.
				if ii == 0:
						_param[kk] = vv
				elif ii == 1:
					# Selecionando o valor já armazenado para a keys determinada.
					tp1 = [_param[kk]]

					# Acrescentando o proximo valor
					tp1.append(vv)

					# Inserindo lista acrescentada no dicionario
					_param[kk] = tp1

				elif ii > 1:
					tp2 = _param[kk]
					tp2.append(vv)
					_param[kk] = tp2



		# Preprocessing - standardizing parameters name format.
		if (param_name    == 'atm' 
			or param_name == 'wave' 
			or param_name == 'current'
			or param_name == 'satph'):

			param_reorganized = preprocessing_atm_wave_current_satph(_param, ID, buoyNM, param_name, tgr=tgr)

		elif param_name  == 'wqmx' or param_name == 'suna':

			param_reorganized = preprocessing_wqmx_suna(_param, buoyNM, param_name, tgr=tgr)


		return(param_reorganized)

	except:
		return(False)


#==============================================================================
# END!
#==============================================================================


# # Descomentar quando quiser verificar saidas rapidamente FS - [02/oct/2017]
# param_name = 'suna'
# ID = 22
# buoyNM = 'SP1'
# # json = param_get_request(param_name, ID, buoyNM)
# param_organized = param_get_request(param_name, ID, buoyNM)
# # with open('TESTE.pkl', 'wb+') as fl:
# # 	pickle.dump(param_organized, fl)