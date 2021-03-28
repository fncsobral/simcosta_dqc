#!/usr/bin/env python3
# -*-coding:utf-8 -*-
"""
#==============================================================================
 
rotina que baixa os dados simcosta via URL.
faz o processamento do CQD.
organiza para salvar em matlab.
salva em matlab.
salva em pickle.


@author: fncssobral
@date  : 21/set/2017
#==============================================================================
"""


# from flask            import Flask, request, jsonify
import pickle, mat4py, calendar
from dqc import call_dqc_processing



# #==============================================================================
# # RESTful
# #==============================================================================
# app = Flask(__name__)



'''
=================================================================================
'''

def epoch2num(epoch):
	'''
	Datenum considera frações de um dia em segundos.
	@author: fncsobral
	@date  : 23/set/2017

	'''
	# get reference time: Datenum para 1970-01-01 00:00:00
	# que é a referencia para o epoch.
	unixEpoch = 719529;

	# how much later than reference time is input?
	offset = epoch / (24*3600);

	# add and return
	dnum = unixEpoch + offset;

	return(dnum)


# ======================== GET REQUEST AND DQC ================================
FLAGS, FLAGSrt = call_dqc_processing()

#SAVING PICKLE
with open('FLAGS.pickle', 'wb+') as fl:
	pickle.dump(FLAGS, fl)

with open('FLAGSrt.pickle', 'wb+') as fl:
	pickle.dump(FLAGSrt, fl)



# ======================================= SAVING ==============================
with open('FLAGS.pickle', 'rb') as fl:
	dict_str = pickle.load(fl)


# Padronizando formato dos valores para float, ndarray não é aceito para salvar
# em formato mat.
for buoy in dict_str.keys():
	for sensor in dict_str[buoy].keys():
		if sensor == 'adcp':
			try:
				for parameter in dict_str[buoy][sensor].keys():

					timestamp = dict_str[buoy][sensor][parameter].pop('timestamp')
					ref_time  = dict_str[buoy][sensor][parameter].pop('reference_utc_time')

					# Convertendo datetime para EPOCH. (acho que mat4py não aceita datetime)
					epoch = [calendar.timegm(dd.timetuple()) for dd in timestamp]

					# Convertendo para float
					if parameter == 'current':				
						for fld_param in dict_str[buoy][sensor][parameter].keys():
							profile_str = list()
							# vv = list()
							for profile in dict_str[buoy][sensor][parameter][fld_param]:
								profile_str.append([float(bins) for bins in profile])
								# print(vv)
								# import time; time.sleep(5)
							# profile_str.append(vv)


							# Reinserting into dictionary
							dict_str[buoy][sensor][parameter][fld_param] = profile_str

					else:
						for fld_param in dict_str[buoy][sensor][parameter].keys():

							# loop nos dados
							vv = list()
							for val in dict_str[buoy][sensor][parameter][fld_param]:
								vv.append(float(val))

							dict_str[buoy][sensor][parameter][fld_param] = vv


					# Reinserting into dictionary
					dict_str[buoy][sensor][parameter]['timestamp']          = epoch
					dict_str[buoy][sensor][parameter]['reference_utc_time'] = ref_time

			except:
				pass
 
		else:
			try:
				for parameter in dict_str[buoy][sensor].keys():

					timestamp = dict_str[buoy][sensor][parameter].pop('timestamp')
					ref_time  = dict_str[buoy][sensor][parameter].pop('reference_utc_time')

					# Convertendo datetime para EPOCH. (acho que mat4py não aceita datetime)
					epoch = [calendar.timegm(dd.timetuple()) for dd in timestamp]

					# Inserindo timestamp como epoch
					dict_str[buoy][sensor][parameter]['timestamp'] = epoch


					for fld_param in dict_str[buoy][sensor][parameter].keys():

						# loop nos dados
						vv = list()
						for val in dict_str[buoy][sensor][parameter][fld_param]:
							vv.append(float(val))

						dict_str[buoy][sensor][parameter][fld_param] = vv


					# Reinserindo UTC time, porque nao eh posivel torna-lo float
					dict_str[buoy][sensor][parameter]['reference_utc_time'] = ref_time

			except:
				pass



# ----------------------------- SALVANDO SEPARADO PARA NÃO DAR PAU-------------
for buoy in dict_str.keys():
	print(buoy)
	for sensor in dict_str[buoy].keys():
		print(sensor)
		# if sensor == 'adcp':
		# 	if str(dict_str[buoy][sensor]) == 'nan':
		# 		print('NAN!!', buoy, sensor)
		# 	else:		
		# 		curr = dict_str[buoy][sensor]

		# 		# Transformando epoch into datenum
		# 		datenum = [epoch2num(epc) for epc in curr['timestamp']]
		# 		curr['datenum'] = datenum

		# 		# Separando a boia RS5 - dados privados.
		# 		if buoy == 'RS5':
		# 			# Matlab
		# 			mat4py.savemat('/home/fncsobral/Dropbox/1.simcosta/data_to_ftp/RS5/' + 
		# 				            buoy + '_' + sensor + '.mat', curr)

		# 			# Python
		# 			with open('/home/fncsobral/Dropbox/1.simcosta/data_to_ftp/RS5/' + 
		# 				       buoy + '_' + sensor + '.pkl', 'wb+') as fl:
		# 				pickle.dump(curr, fl)
		# 		else:
		# 			# Matlab
		# 			mat4py.savemat('/home/fncsobral/Dropbox/1.simcosta/data_to_ftp/' + 
		# 				            buoy + '_' + sensor + '.mat', curr)

		# 			# Python
		# 			with open('/home/fncsobral/Dropbox/1.simcosta/data_to_ftp/' + 
		# 				       buoy + '_' + sensor + '.pkl', 'wb+') as fl:
		# 				pickle.dump(curr, fl)

		# else:
		if str(dict_str[buoy][sensor]) == 'nan':
			print('NAN!!', buoy, sensor)
		else:
			for param in dict_str[buoy][sensor].keys():
				print(param.upper()+'!!!')
				
				values = dict_str[buoy][sensor][param] #['values']

				if not values or str(values) == 'nan':
					pass
				else:
					# Transformando epoch into datenum
					datenum = [epoch2num(epc) for epc in values['timestamp']]
					values['datenum'] = datenum
					
					# Separando a boia RS5 - dados privados.
					if buoy == 'RS5':
						# Matlab
						mat4py.savemat( 
							            buoy + '_' + sensor + '_' + param + '.mat', values)

						# Python
						with open( 
							       buoy + '_' + sensor + '_' + param + '.pkl', 'wb+') as fl:
							pickle.dump(values, fl)

					else:
						# Matlab
						mat4py.savemat( 
							            buoy + '_' + sensor + '_' + param + '.mat', values)

						# Python
						with open( 
							       buoy + '_' + sensor + '_' + param + '.pkl', 'wb+') as fl:
							pickle.dump(values, fl)



# --------- Salvando serie completa para pasta RS5
with open('simcosta_rs5.pkl', 'wb+') as fl:
	pickle.dump(dict_str, fl)


# Retirando RS5 de FLAGS e salvando como pickle.
try:
	dict_str.pop('RS5')
except:
	pass

with open('simcosta.pkl', 'wb+') as fl:
	pickle.dump(dict_str, fl)



# #==============================================================================
# # 
# #==============================================================================
# # Sending data to localhost URL with final flag.
# @app.route('/simcosta/', methods=['GET', 'POST'])
# def post_request():
# 	# flags, flagsrt = call_dqc_processing()
# 	return jsonify({'ATM RJ4'    : FLAGSrt['RJ4']['atm'    ],
# 				    'WAVE RJ4'   : FLAGSrt['RJ4']['wave'   ],
# 				    'SUNA RJ4'   : FLAGSrt['RJ4']['suna'   ],
# 				    'SATPH RJ4'  : FLAGSrt['RJ4']['satph'  ],
# 				    'CURRENT RJ4': FLAGSrt['RJ4']['current'],
# 					'WQMX RJ4'   : FLAGSrt['RJ4']['wqmx'   ],

# 					'ATM RS5'    : FLAGSrt['RS5']['atm'    ],
# 				    'WAVE RS5'   : FLAGSrt['RS5']['wave'   ],
# 				    'SUNA RS5'   : FLAGSrt['RS5']['suna'   ],
# 				    'SATPH RS5'  : FLAGSrt['RS5']['satph'  ],
# 				    'CURRENT RS5': FLAGSrt['RS5']['current'],
# 					'WQMX RS5'   : FLAGSrt['RS5']['wqmx'   ],

# 					'ATM SC1'    : FLAGSrt['SC1']['atm'    ],
# 				    'WAVE SC1'   : FLAGSrt['SC1']['wave'   ],
# 				    'SUNA SC1'   : FLAGSrt['SC1']['suna'   ],
# 				    'SATPH SC1'  : FLAGSrt['SC1']['satph'  ],
# 				    'CURRENT SC1': FLAGSrt['SC1']['current'],
# 					'WQMX SC1'   : FLAGSrt['SC1']['wqmx'   ],

# 					'ATM SP1'    : FLAGSrt['SP1']['atm'    ],
# 				    'WAVE SP1'   : FLAGSrt['SP1']['wave'   ],
# 				    'SUNA SP1'   : FLAGSrt['SP1']['suna'   ],
# 				    'SATPH SP1'  : FLAGSrt['SP1']['satph'  ],
# 				    'CURRENT SP1': FLAGSrt['SP1']['current'],
# 					'WQMX SP1'   : FLAGSrt['SP1']['wqmx'   ]
# 				    }), 201


# #============================================================================
# # Refreshing local server
# #============================================================================
# if __name__ == '__main__':
# 	app.run(debug=True)


#==============================================================================
# END!
#==============================================================================
