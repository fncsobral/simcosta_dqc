#!/usr/bin/env python3
# -*- coding:utf-8 -*-
'''
#==============================================================================
# SCRIPT TO GET REQUEST DATA AND APPLY DQC
#==============================================================================




@author: fncsobral
@date  : 27/jun/2017
@mod.1 : 21/set/2017 - fncsobral
         - adaptation to just download data and apply dqc, to later
           transform into mat and pickle files
         - removed the POST request
#==============================================================================
'''

from get_requests     import *
from datetime         import datetime as dtm
from clss_dqc         import DQC
from clss_dqc_aux     import DQC_aux
from clss_dqc_wave 	  import DQC_Wave
from clss_dqc_current import DQC_Current

import warnings

# Ignoring warnings, mainly from about slicing a nan list.
warnings.filterwarnings('ignore')


#==============================================================================
# 
#==============================================================================
# Calling Python applications for QC tests.
def call_dqc_processing(tgr=False):
	'''	

	'''


	# Here are only buoys in OPERATION
	id_AXYS = [    1,     2,     3,    12,    4,    11,     6,    10]
	nm_AXYS = ['RJ1', 'RJ2', 'RJ3', 'RJ4','PR1', 'PR2', 'RS2', 'RS5']

	id_LOBO = [20   ,    21,    22]
	nm_LOBO = ['SC1', 'RS1', 'SP1']

	# Essa separacao ja nao esta fazendo muito sentido!! FS - 18/out/2017
	sensors_AXYS = ['atm', 'wave', 'current']
	sensors_LOBO = ['wqmx', 'satph', 'suna']

	id_BUOYS      = np.concatenate([id_AXYS, id_LOBO])
	nm_BUOYS      = np.concatenate([nm_AXYS, nm_LOBO])
	sensors_BUOYS = np.concatenate([sensors_AXYS, sensors_LOBO])


	# ======================================================================= #
	# ============================ REQUEST DATA VIA URL ======================
	# ======================================================================= #
	# Loop over buoys ID
	for jj, (_id, buoyNM) in enumerate(zip(id_BUOYS, nm_BUOYS)):

		# Loop over sensors
		for ii, ss in enumerate(sensors_BUOYS):	
			if ii == 0:			
				tmp = {ss: param_get_request(ss, _id, buoyNM, tgr=tgr)}
			else:
				tmp[ss] = param_get_request(ss, _id, buoyNM, tgr=tgr)

		if jj == 0:
			param_reorganized = {buoyNM:tmp}
		else:
			param_reorganized[buoyNM] = tmp


	# ======================================================================= #	
	# =================================== DQC =================================
	# ======================================================================= #
	for ii, (bnm, _id) in enumerate(zip(nm_BUOYS, id_BUOYS)):
		print('\n', bnm)
		
		if ii == 0:
			FLAGS   = {bnm:None}
			FLAGSrt = {bnm:None}
		else:
			FLAGS[bnm]   = None
			FLAGSrt[bnm] = None

		for jj, ss in enumerate(sensors_BUOYS):
			print(ss)
			if jj == 0:
				if ss == 'current':
					FLAGS[bnm]   = {'adcp':None}
					FLAGSrt[bnm] = {'adcp':None}	
				else:
					FLAGS[bnm]   = {ss:None}
					FLAGSrt[bnm] = {ss:None}
			else:
				if ss == 'current':
					FLAGS[bnm]['adcp']   = None
					FLAGSrt[bnm]['adcp'] = None
				else:
					FLAGS[bnm][ss]   = None
					FLAGSrt[bnm][ss] = None


			# Getting data. Data can be the parameters of: WQMX, SUNA, ATM, WAVE, CURRENT.
			data = param_reorganized[bnm][ss]
		

			if not data:
				param_flags  = np.nan

				if ss == 'current':
					FLAGS[bnm]['adcp']   = param_flags
					FLAGSrt[bnm]['adcp'] = param_flags
				else:
					FLAGS[bnm][ss]   = param_flags
					FLAGSrt[bnm][ss] = param_flags


			else:
				# =========================================================== #
				# -------------------------- MÉDIA SUNA/WQMX ------------------
				# =========================================================== #
				if ss == 'wqmx' or ss == 'suna':
					# Com o dado sem media
					# Retirando repetidos do tempo de referencia, nao pode entrar no 
					# DQC_aux

					# ref_time = np.unique(data.pop('reference_utc_time'))
					
					# Obtendo variavel epoch
					epoch = data['timestamp']


					dqc_aux = DQC_aux(data,  date=epoch, sensor_name=ss)

					# Realizando a media. Usando o mesmo nome de variavel DATA.
					del(data)
					data = dqc_aux.bursts_eval()



				# =========================================================== #
				# ------------------- PARA TODOS OS PARAMETEROS ---------------
				# =========================================================== #
				# Retirando timestamp do loop e inserindo em uma variavel
				epoch = data.pop('timestamp')

				# Retirando tempo de referencia para nao ir no loop
				ref_time = data.pop('reference_utc_time')

				# Convertendo epoch para datetime
				timestamp = [dtm.fromtimestamp(tt) for tt in epoch]

				
				# =========================================================== #
				# ---------------------------- DQC ----------------------------
				# =========================================================== #
				if ss == 'atm' or ss == 'wqmx' or ss == 'suna' or ss == 'satph':						
					# ATENÇÃO: 13/set/2017
					# Retirando gusts, avg_dew_pnt, não sei porque não inseri em dqc_aux
					# Estes que estou retirando aqui, devem ser analizados melhor depois!!
					if ss == 'atm' and _id < 20:
						data.pop('gusts')
						data.pop('avg_dew_pnt')
					elif ss == 'wqmx':
						data.pop('pressure')
					elif ss == 'satph':
						data.pop('ph_ext')
						data.pop('temperature')
					elif ss == 'suna':
						data.pop('nitrate_um')

					# Loop nos parametros dos sensores acima
					for ll, kk in enumerate(data.keys()):
						print(kk)

						if ll == 0:
							FLAGS[bnm][ss] = {kk:None}
							FLAGSrt[bnm][ss] = {kk:None}
						else:
							FLAGS[bnm][ss][kk] = None
							FLAGSrt[bnm][ss][kk] = None

						# Getting parameter value.
						values = data[kk]


						dqc_aux = DQC_aux(values, parameter_name=kk, date=timestamp, reference_time=ref_time)

						# Filling gaps and organizing data format.
						new_param, new_time, new_reftime, sf = dqc_aux.time_data_organizing()

						
						# O parametro é inserido na classe DQC_aux
						tst_hierarchy = dqc_aux.selecting_tests()


						# Carregando DQC
						dqc = DQC(new_param, kk, dqc_aux)


						# Loop nos testes de acordo com a hierarquia
						for tt in tst_hierarchy:
							if tt == 'Gross Range':
								grossrange = dqc.gross_range()
							
							elif tt == 'Spike':
								spike = dqc.spike(sf)

							elif tt == 'Rate Change':
								ratechange  = dqc.rate_change(sf)

							elif tt == 'Flat Line':
								flatline = dqc.flat_line(sf)

							elif tt == 'Attenuated Signal':
								attenuatedsignal = dqc.attenuated_signal(sf, whichtest= kk)


						grss = grossrange[kk]
						spk  = spike[kk]
						rtch = ratechange[kk]
						flln = flatline[kk]
						attn = attenuatedsignal[kk]

						# Variable with just flag 1, 1 and 2 and 1, 2 and 3 
						# data respectively.
						filter_good    = list()
						filter_noteval = list()
						filter_warn    = list()
						final_flags    = list()
						for PARAM, GRSS, SPK, RTCH, FLLN, ATTN in zip(new_param, grss, spk, rtch, flln, attn):

							flags = np.array([GRSS, SPK, RTCH, FLLN, ATTN])
							if any(flags == 9):
								final_flags.append(9        )
								filter_good.append(np.nan   )
								filter_noteval.append(np.nan)
								filter_warn.append(np.nan   )
							elif any(flags == 4):
								final_flags.append(4)
								filter_good.append(np.nan   )
								filter_noteval.append(np.nan)
								filter_warn.append(np.nan   )
							elif any(flags == 3):
								final_flags.append(3)
								filter_good.append(np.nan   )
								filter_noteval.append(np.nan)
								filter_warn.append(PARAM    )
							elif any(flags == 2):
								final_flags.append(2)
								filter_good.append(np.nan   )
								filter_noteval.append(PARAM )
								filter_warn.append(PARAM    )
							elif any(flags == 1):
								final_flags.append(1)
								filter_good.append(PARAM    )
								filter_noteval.append(PARAM )
								filter_warn.append(PARAM    )



						# Storing all the series and also Real Time data.
						FLAGS[bnm][ss][kk]   =  {'final_flags'       : final_flags   , 
						                         'timestamp'         : new_time      , 
						                         'values'            : new_param     ,
						                         'values_good'       : filter_good   ,
						                         'values_noteval'    : filter_noteval,
						                         'values_warn'       : filter_warn   ,
						                         'reference_utc_time': new_reftime
	                 	}

						FLAGSrt[bnm][ss][kk] =  {'final_flags'       : final_flags[-2], 
						                         'timestamp'         : new_time[-2   ], 
						                         'rt_value'          : new_param[-2  ],
						                         'reference_utc_time': new_reftime[-2]   
	                    }

	          		
				# ---------------------------- WAVE ---------------------------
				elif ss == 'wave':
					# Por enquanto espalhamento não entra no controle.
					data.pop('spreading')
					data.pop('hmax')


					for ll, kk in enumerate(data.keys()):

						if ll == 0:
							FLAGS[bnm][ss]   = {kk:None}
							FLAGSrt[bnm][ss] = {kk:None}
						else:
							FLAGS[bnm][ss][kk]   = None
							FLAGSrt[bnm][ss][kk] = None


						# Hs will be always necessary.
						values_hs = data['hs']
						dqc_aux = DQC_aux(values_hs, parameter_name='wave', date=timestamp, reference_time=ref_time)

						# Filling gaps and organizing data format.
						new_param1, new_time, new_reftime, sf = dqc_aux.time_data_organizing()					

						# A hierarquia verifica apenas a entrada parameter_name 
						# em DQC_aux, ou seja, pode ser utilizada em todos os
						# parametros.
						tst_hierarchy = dqc_aux.selecting_tests()


		   				# Tp e Dir precisam de Hs como controle no teste do bulk
						if kk == 'tp' or kk == 'dp':
							values = data[kk]

							dqc_aux = DQC_aux(values, parameter_name='wave', date=timestamp, reference_time=ref_time)

							# Filling gaps and organizing data format.
							new_param2, new_time, new_reftime, sf = dqc_aux.time_data_organizing()

							# # Carregando DQC para analise de TP/DP como primeiro parametro
							# dqc1 = DQC_Wave(new_param2, kk, dqc_aux, whtanl=2)

							# Carregando DQC para TP/DP na analise que precisa de Hs.
							dqc = DQC_Wave(new_param1, 
								           'hs'      , 
								           dqc_aux   ,
								           new_parameter2=new_param2, 
								           parameter_name2=kk       , 
								           whtanl=2)


						elif kk == 'hs':
							dqc = DQC_Wave(new_param1, kk, dqc_aux)


						# Applying tests.
						for tt in tst_hierarchy:
							if tt == 'Flat Line':
								flatline = dqc.flat_line(sf)

							elif tt == 'Rate Change':
								ratechange = dqc.rate_change()

							elif tt == 'Bulk Wave Param MxMn':
								blkwave = dqc.bulk_wave_param_mxmn()

							elif tt == 'Mean Std':
								meanstd = dqc.mean_std(sf)

						flln  = flatline[kk]						
						rtch  = ratechange[kk]
						blkwv = blkwave[kk]
						mnstd = meanstd[kk]


						# Variable with just flag 1, 1 and 2 and 1, 2 and 3 
						# data respectively.
						filter_good    = list()
						filter_noteval = list()
						filter_warn    = list()
						final_flags = list()

						if kk == 'hs':
							new_param = new_param1
						else:
							new_param = new_param2

						for PARAM, FLLN, RTCH, BLKWV, MNSTD in zip(new_param, flln, rtch, blkwv, mnstd):

							flags = np.array([FLLN, RTCH, BLKWV, MNSTD])
							if any(flags == 9):
								final_flags.append(9)							
								filter_good.append(np.nan   )
								filter_noteval.append(np.nan)
								filter_warn.append(np.nan   )

							elif any(flags == 4):
								final_flags.append(4)
								filter_good.append(np.nan   )
								filter_noteval.append(np.nan)
								filter_warn.append(np.nan   )

							elif any(flags == 3):
								final_flags.append(3)
								filter_good.append(np.nan   )
								filter_noteval.append(np.nan)
								filter_warn.append(PARAM    )

							elif any(flags == 2):
								final_flags.append(2)
								filter_good.append(np.nan   )
								filter_noteval.append(PARAM )
								filter_warn.append(PARAM    )

							elif any(flags == 1):
								final_flags.append(1)
								filter_good.append(PARAM    )
								filter_noteval.append(PARAM )
								filter_warn.append(PARAM    )


						if kk == 'hs':
							FLAGS[bnm][ss][kk]   =  {'final_flags'       : final_flags   , 
													 'timestamp'         : new_time      ,
													 'values'            : new_param1    ,
	 						                         'values_good'       : filter_good   ,
				      			                     'values_noteval'    : filter_noteval,
						        	                 'values_warn'       : filter_warn   ,
						        	                 'reference_utc_time': new_reftime
							}
							FLAGSrt[bnm][ss][kk] =  {'final_flags'       : final_flags[-2], 
													 'timestamp'         : new_time[-2   ],
													 'rt_value'          : new_param1[-2 ],
													 'reference_utc_time': new_reftime[-2]
							}
						else:
							FLAGS[bnm][ss][kk]   =  {'final_flags'       : final_flags   , 
													 'timestamp'         : new_time      ,
													 'values'            : new_param2    ,
	 						                         'values_good'       : filter_good   ,
						                             'values_noteval'    : filter_noteval,
						                             'values_warn'       : filter_warn   ,
						                             'reference_utc_time': new_reftime
							}
							FLAGSrt[bnm][ss][kk] =  {'final_flags'       : final_flags[-2], 
													 'timestamp'         : new_time[-2   ],
													 'rt_value'          : new_param2[-2 ],
													 'reference_utc_time': new_reftime[-2]
							}


				# ----------------------------- CURRENT ---------------------------
				elif ss == 'current':

					
					FLAGS[bnm]['adcp']   = {'temperature': None, 'salinity': None, 'current': None}
					FLAGSrt[bnm]['adcp'] = {'temperature': None, 'salinity': None, 'current': None}

					prov = ['temperature', 'salinity']
					for ll, pp in enumerate(prov):

						# Getting parameter value.
						values = data[pp]

						dqc_aux = DQC_aux(values, parameter_name=pp, date=timestamp, reference_time=ref_time)

						# Filling gaps and organizing data format.
						new_param, new_time, new_reftime, sf = dqc_aux.time_data_organizing()
						
						# O parametro é inserido na classe DQC_aux
						tst_hierarchy = dqc_aux.selecting_tests()

						# Carregando DQC
						dqc = DQC(new_param, pp, dqc_aux)


						# Loop nos testes de acordo com a hierarquia
						for tt in tst_hierarchy:
							if tt == 'Gross Range':
								grossrange = dqc.gross_range()
							
							elif tt == 'Spike':
								spike = dqc.spike(sf)

							elif tt == 'Rate Change':
								ratechange  = dqc.rate_change(sf)

							elif tt == 'Flat Line':
								flatline = dqc.flat_line(sf)

							elif tt == 'Attenuated Signal':
								attenuatedsignal = dqc.attenuated_signal(sf, whichtest= pp)


						grss = grossrange[pp]
						spk  = spike[pp]
						rtch = ratechange[pp]
						flln = flatline[pp]
						attn = attenuatedsignal[pp]

						# Variable with just flag 1, 1 and 2 and 1, 2 and 3 
						# data respectively.
						filter_good    = list()
						filter_noteval = list()
						filter_warn    = list()
						final_flags    = list()
						for PARAM, GRSS, SPK, RTCH, FLLN, ATTN in zip(new_param, grss, spk, rtch, flln, attn):

							flags = np.array([GRSS, SPK, RTCH, FLLN, ATTN])
							if any(flags == 9):
								final_flags.append(9        )
								filter_good.append(np.nan   )
								filter_noteval.append(np.nan)
								filter_warn.append(np.nan   )
							elif any(flags == 4):
								final_flags.append(4)
								filter_good.append(np.nan   )
								filter_noteval.append(np.nan)
								filter_warn.append(np.nan   )
							elif any(flags == 3):
								final_flags.append(3)
								filter_good.append(np.nan   )
								filter_noteval.append(np.nan)
								filter_warn.append(PARAM    )
							elif any(flags == 2):
								final_flags.append(2)
								filter_good.append(np.nan   )
								filter_noteval.append(PARAM )
								filter_warn.append(PARAM    )
							elif any(flags == 1):
								final_flags.append(1)
								filter_good.append(PARAM    )
								filter_noteval.append(PARAM )
								filter_warn.append(PARAM    )

	
                        # Armazenando em dicionario
						FLAGS[bnm]['adcp'][pp]   =  {'final_flags'       : final_flags   ,
													 'timestamp'         : new_time      ,
													 'values'            : new_param     ,
													 'values_good'       : filter_good   ,
													 'values_noteval'    : filter_noteval,
													 'values_warn'       : filter_warn   ,
													 'reference_utc_time': new_reftime 
						}


						FLAGSrt[bnm]['adcp'][pp] =  {'final_flags'       : final_flags[  -2],
							                         'timestamp'         : new_time[     -2],
							                         'values'            : new_param[    -2],
							                         'reference_utc_time': new_reftime[-2]             
						}


					#===============================================================================
					velocity  = data['velocity']
					direction = data['direction'] 

					# inserindo velocidade
					dqc_aux1 = DQC_aux(velocity, date=timestamp, reference_time=ref_time, parameter_name='current')
					new_vel, new_time, new_reftime, sf = dqc_aux1.time_data_organizing()


					# inserindo apenas direção
					dqc_aux2 = DQC_aux(direction, date=timestamp, reference_time=ref_time, parameter_name='current')
					new_dir, new_time, new_reftime, sf = dqc_aux2.time_data_organizing()


					# Inserindo ambos velocidade e direção
					dqc_aux3 = DQC_aux(new_vel, date=timestamp, reference_time=ref_time, parameter_name='current', cur_dir=new_dir)
					u, v = dqc_aux3.current_decomposition()

					# O parametro é inserido na classe DQC_aux
					tst_hierarchy = dqc_aux3.selecting_tests()

					# Calling class for current tests
					dqc = DQC_Current(new_vel, new_dir, u, v, dqc_aux3)


					for tt in tst_hierarchy:

						if tt == 'Current Speed':
							curspd = dqc.current_speed()

						elif tt == 'Current Direction':
							curdir = dqc.current_direction()

						elif tt == 'Horizontal Velocity':
							horvel = dqc.horizontal_velocity()

						elif tt == 'Flat Line':
							flatline = dqc.flat_line(sf)

						elif tt == 'UV Rate Change':
							uvratechange = dqc.uv_rate_change()
							
						elif tt == 'UV Spike':
							uvspike = dqc.uv_spike(sf)

						elif tt == 'Current Gradient':
							curgrad = dqc.current_gradient()

					crspd  = curspd['current'      ]
					crdr   = curdir['current'      ]
					hrvl   = horvel['current'      ]
					flln   = flatline['current'    ]
					uvrtch = uvratechange['current']
					uvspk  = uvspike['current'     ]
					crgrd  = curgrad['current'     ]


					profile_vel_good    = list()
					profile_vel_noteval = list()
					profile_vel_warn    = list()
					profile_dir_good    = list()
					profile_dir_noteval = list()
					profile_dir_warn    = list()

					final_flags = list()
					for yy, (prof_vel, prof_dir, CRSPD, CRDR, HRVL, FLLN, UVRTCH, UVSPK, CRGRD) in enumerate(zip(new_vel, new_dir, crspd, crdr, hrvl, flln, uvrtch, uvspk, crgrd)):

						# Juntando todos os resultados dos testes acima para o perfil
						# do tempo Tn0.
						profile = list()

						profile.append(list(CRSPD ))
						profile.append(list(CRDR  ))
						profile.append(list(HRVL  ))
						profile.append(list(FLLN  ))
						profile.append(list(UVRTCH))
						profile.append(list(UVSPK ))
						profile.append(list(CRGRD ))

						# Convertendo profile em array para poder fazer slice a cada
						# profundidade.
						profile = np.array(profile)

						# Shape profile, para ter o numero de celulas (depths)
						sh = np.shape(profile)

						vel_good    = list()
						vel_noteval = list()
						vel_warn    = list()
						dir_good    = list()
						dir_noteval = list()
						dir_warn    = list()

						flags = list()
						# loop por celulas
						for bin_vel, bin_dir, cel in zip(prof_vel, prof_dir, range(sh[1])):
							if any(profile[:, cel] == 9):
								flags.append(9           )
								vel_good.append(np.nan   )
								vel_noteval.append(np.nan)
								vel_warn.append(np.nan   )
								dir_good.append(np.nan   )
								dir_noteval.append(np.nan)
								dir_warn.append(np.nan   )								

							elif any(profile[:, cel] == 4):
								flags.append(4           )
								vel_good.append(np.nan   )
								vel_noteval.append(np.nan)
								vel_warn.append(np.nan   )
								dir_good.append(np.nan   )
								dir_noteval.append(np.nan)
								dir_warn.append(np.nan   )

							elif any(profile[:, cel] == 3):
								flags.append(3           )
								vel_good.append(np.nan   )
								vel_noteval.append(np.nan)
								vel_warn.append(bin_vel  )
								dir_good.append(np.nan   )
								dir_noteval.append(np.nan)
								dir_warn.append(bin_dir  )

							elif any(profile[:, cel] == 2):
								flags.append(2            )
								vel_good.append(np.nan    )
								vel_noteval.append(bin_vel)
								vel_warn.append(bin_vel   )
								dir_good.append(np.nan    )
								dir_noteval.append(bin_dir)
								dir_warn.append(bin_dir   )

							elif any(profile[:, cel] == 1):
								flags.append(1            )
								vel_good.append(bin_vel   )
								vel_noteval.append(bin_vel)
								vel_warn.append(bin_vel   )
								dir_good.append(bin_dir   )
								dir_noteval.append(bin_dir)
								dir_warn.append(bin_dir   )


						# Armazenando flags para o perfil de Tn0
						final_flags.append(flags              )
						profile_vel_good.append(vel_good      )   
						profile_vel_noteval.append(vel_noteval)
						profile_vel_warn.append(vel_warn      )
						profile_dir_good.append(dir_good      )  
						profile_dir_noteval.append(dir_noteval)
						profile_dir_warn.append(dir_warn      )



					# Armazenando em dicionario
					FLAGS[bnm]['adcp']['current']   =  {'final_flags'       : final_flags        , 
					                                    'timestamp'         : new_time           ,
					                                    'velocity'          : new_vel            ,
					                                    'velocity_good'     : profile_vel_good   ,
					                                    'velocity_noteval'  : profile_vel_noteval,
					                                    'velocity_warn'     : profile_vel_warn   ,
					                                    'direction'         : new_dir            ,
					                                    'direction_good'    : profile_dir_good   ,
					                                    'direction_noteval' : profile_dir_noteval,
					                                    'direction_warn'    : profile_dir_warn   ,
					                                    'reference_utc_time': new_reftime   
	             	}
					FLAGSrt[bnm]['adcp']['current'] =  {'final_flags'       : final_flags[-2], 
								                        'timestamp'         : new_time[   -2],
								                        'velocity'          : new_vel[    -2],
								                        'direction'         : new_dir[    -2],
								                        'reference_utc_time': new_reftime[-2]
	             	}


	# Utilizando esta rotina para salvar todos os dados que possuimos:
	return(FLAGS, FLAGSrt)

#==============================================================================
# END!
#==============================================================================
