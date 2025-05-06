'''
Functions for executing local and external algorithm runs.
'''
import os
from datetime import datetime
from time import sleep
import tempfile
import json
import re
from .cleanup import remove_oldresults_db, remove_oldinputs_db, remove_oldresults_fs, remove_oldinputs_fs

from django.shortcuts import get_object_or_404
from django.core.files.uploadedfile import InMemoryUploadedFile

from Stemweb.algorithms.tasks import external_algorithm_run_error
from Stemweb.algorithms.tasks import external_algorithm_run_finished

from .settings import ALGORITHM_MEDIA_ROOT as algo_root
from Stemweb.algorithms.models import InputFile, Algorithm, AlgorithmRun
from . import utils
from . import settings
from celery import shared_task, Task
from celery import signature
from inspect import signature as signat
from .reformat import re_format
from copy import deepcopy
from pathlib import Path

def validate_nexusmatrix(matrix_block):

    rows = matrix_block.strip().split("\n")  # Split into lines
    sequence_length = None
    row_pattern = re.compile(r"^\s*(\S+)\s+([a-z?]+)\s*$", re.IGNORECASE)  # for taxon and sequence

    for row in enumerate(rows):
        match = row_pattern.match(row[1])
        if not match:
            errmsg = f"Invalid row structure: {row[1]}"
            #print(errmsg)
            return errmsg

        _taxon, sequence = match.groups()

        # Check sequence length consistency
        if sequence_length is None:
            sequence_length = len(sequence)  # Set the first sequence length
            first_row = row
        elif len(sequence) != sequence_length:
            errmsg = f"Input data error: different sequence lengths in row 1 ({first_row[1]}) and in row {row[0] + 1} ({row[1]})" ### +1 because user starts counting with 1, not with 0
            #print(errmsg)
            return errmsg

        # Check for invalid characters in sequence
        if not re.match(r"^[a-z?]+$", sequence, re.IGNORECASE):
            errmsg = f"Invalid characters in sequence: {sequence}"
            #print(errmsg)
            return errmsg

    # All checks passed; Matrix block is well-formed
    return True

def local(form, algo_id, request):
	''' Make a local (=GUI based) algorithm run.
	    Returns AlgorithmRun id.
	'''
	algorithm = get_object_or_404(Algorithm, pk = algo_id)

	# remove outdated results in database and in file system compared with value in settings.KEEP_RESULTS_DAYS
	remove_oldresults_db()
	remove_oldresults_fs()
	# remove outdated inputs in file system and in database compared with value in settings.KEEP_INPUTS_DAYS
	remove_oldinputs_db()
	remove_oldinputs_fs()

	run_args = utils.build_local_args(form, algorithm_name = algorithm.name, request = request)
	input_file = InputFile.objects.get(id = run_args['file_id'])
	format_error = None
	# =====================
	if algo_id == '2': 		# RHM: algo_id = '2' ;   algorithm.file_extension = 'csv'
		infile_path = run_args['infolder']			
		with open(infile_path, 'r',  encoding = 'utf8') as f:
			file_data = f.read()
		if isinstance(file_data, dict):		##### with e.g. such a format:   {'Aq': 'das', 'B': 'ist ', 'Di': 'jetzt', 'Ge': 'nur', 'Id': 'mal', 'J': 'ein', 'Ju': 'ganz', 'Ki': 'simpler', 'Ory': 'und', 'Oy': 'sehr', 'U': 'kurzer', 'Vo': 'Text'}
			pass
		else:		#### old input data format
			file_data = re_format(file_data)	### needed later to iterate over and write the files
			if not isinstance(file_data, dict):	### in case of a format error in the input data re_format returns the error msg in a string 
				match = re.search("^format error:", file_data)		# check if re_format returned a format error message instead of a valid result
				if match:
					format_error = file_data

		file_dir = os.path.dirname(infile_path)	                    ### '/home/stemweb/Stemweb/media/datasets'
		stamped_dir =  datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + utils.id_generator()	### e.g.: '20220125-213519-5JRTPJMI'
		multi_file_dir = os.path.join(file_dir, stamped_dir)    	### '/home/stemweb/Stemweb/media/datasets/20220125-213519-5JRTPJMI'
		#print('########## exec_algo.py: RHM input path / multi_file_dir = ', multi_file_dir, '++++++++++++')
		os.mkdir(multi_file_dir)
		os.chdir(multi_file_dir)

		if format_error == None:
		### file_data contains content of unaligned files; write it into separate files
		### This input format is expected  by binarysankoff_linux.c (=new rhm.c by Teemu Roos 2018)
			try:
				for key, value in file_data.items():
					with open(key, mode = 'w', encoding = 'utf8') as fp:
						json.dump(value, fp)
			except:
				print ("\n######### could not write input file:", key, " +++++++++++++++++++\n")
				#pass

		input_file_key = ''
		for arg in algorithm.args.all():
			if arg.value == 'input_file':
				input_file_key = arg.key
		run_args[input_file_key] = multi_file_dir

	current_run = AlgorithmRun.objects.create(input_file = input_file,
						algorithm = Algorithm.objects.get(id = algo_id),                                         	
											folder = os.path.join(algo_root, run_args['folder_url'])) # output folder
											
	current_run.save()	# Save to ensure that id generation is not delayed.
	rid = current_run.id
	kwargs = {'run_args': run_args, 'algorithm_run': rid}
	inherited_AlgorithmTask = algorithm.get_callable(kwargs)

	if format_error == None:
		inherited_AlgorithmTask.apply_async(kwargs = kwargs)
		#inherited_AlgorithmTask.apply(kwargs = kwargs)    # synchronous call for dev and test purpose
		return current_run.id
	else:	### knowing that RHM input data have a format error, we don't call the calculation of the RHM algorithm, but do this:
		current_run.error_msg = format_error
		current_run.status = settings.STATUS_CODES['failure']
		current_run.save()
		external_algorithm_run_error(None, format_error, run_id=rid, return_host=return_host, return_path=return_path)
		return current_run.id


def external(json_data, algo_id, request):
	''' Make external (= via REST-API) algorithm run for request.
	First create the InputFile object of the request.POST's json's data and save it. 
	Then execute the actual run.
	Returns AlgorithmRun id.
	
	TODO: Refactor me   #  PF: to be refactored in which way? -- intended by previous SW-developer of this module!
	'''

	#print('################# all handed over args in external()####################')
	#for i in signat(external).parameters.items():
	#	print(i)
	#print('========================================')
	#print (json_data)
	#print (algo_id)
	#print (request)
	#print('++++++++++++++++++++++++++++++++++++++++')	

	algoid_shortname_dict = {'2': 'rhm', '3': 'nj', '4': 'nnet'}

	# remove outdated results in database and in file system compared with value in settings.KEEP_RESULTS_DAYS
	remove_oldresults_db()
	remove_oldresults_fs()
	# remove outdated inputs in database and in file system compared with value in settings.KEEP_INPUTS_DAYS
	remove_oldinputs_db()
	remove_oldinputs_fs()

	return_host = json_data['return_host']
	return_path = json_data['return_path']

	from Stemweb.files.models import InputFile
	algorithm = get_object_or_404(Algorithm, pk = algo_id)
	csv_file = tempfile.NamedTemporaryFile(mode = 'w', delete = False)
	ext = ""

	structured_data = None
	format_error = None
	if algo_id == '2':	# RHM: algo_id = '2' ;   algorithm.file_extension = 'csv'
		file_data = json_data.pop('data')	
		orig_inputdata = deepcopy(file_data)
		if isinstance(file_data, dict):		##### e.g.:   {'Aq': 'das', 'B': 'ist ', 'Di': 'jetzt', 'Ge': 'nur', 'Id': 'mal', 'J': 'ein', 'Ju': 'ganz', 'Ki': 'simpler', 'Ory': 'und', 'Oy': 'sehr', 'U': 'kurzer', 'Vo': 'Text'}
			structured_data = json.dumps(file_data)    ### later f.write() needs string instead of dict
		else:		#### old input data format as a single string including line feeds and (tabs as field separators)
			file_data = re_format(file_data)	### needed later to iterate over and write the files
			if not isinstance(file_data, dict):	### in case of a format error in the input data re_format returns the error msg in a string
				match = re.search("^format error:", file_data)		# check if re_format returned a format error message instead of a valid result
				if match:
					format_error = file_data
					#raise Exception(file_data)
			structured_data = json.dumps(file_data)
		ext = ".csv"
	elif algorithm.file_extension == 'nex':  	# Neighbour Joining or Neighbour Net
		from .csvtonexus import csv2nex
		orig_inputdata = json_data.pop('data')
		structured_data = csv2nex(orig_inputdata)
		ext = ".nex"

	with open(csv_file.name, mode = 'w', encoding = 'utf8') as f:
		f.write(structured_data)

    ### PF: do we really need this mock-file?! Why does it need to be used? 
	### just to involve a timestamp and a unique id via utils.id_generator() ?  

	# Construct a mock up InMemoryUploadedFile from it for the InputFile
	mock_file = None
	input_file_id = None
	unique_id = utils.id_generator()
	unique_name =  datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + unique_id
	with open(csv_file.name, "r") as f:
		name =  unique_name + ext
		mock_file = InMemoryUploadedFile(file = f, field_name = 'file', name = name, \
									content_type = 'utf8', size = os.path.getsize(csv_file.name), charset = 'utf-8')	
			
		input_file = InputFile(name = name, file = mock_file)  
		input_file.extension = ext
		input_file.save() # Save to be sure input_file.id is created 
		input_file_id = input_file.id
	
	input_file = InputFile.objects.get(pk = input_file_id)

	originputdata_dir = Path("/home/stemweb/Stemweb/media/files/originalInputData/")
	originputdata_dir.mkdir(parents=True, exist_ok=True)
	orig_inputdata_file = os.path.join(originputdata_dir, unique_name + '_' + algoid_shortname_dict[algo_id])
	with open(orig_inputdata_file, mode = 'w', encoding = 'utf8') as fp:
			json.dump(orig_inputdata, fp)

	if (algo_id == '2' and format_error == None):	# ONLY for RHM: split content to multiple input files (new input format for new RHM.c version 2018 of Teem Roos))
		file_path = os.path.join(algo_root, input_file.file.path)	### '/home/stemweb/Stemweb/media/files/csv/20210908-075706-BSQQ3HII.csv'
		file_dir = os.path.dirname(file_path)	                    ### '/home/stemweb/Stemweb/media/files/csv'
		name_without_ext = os.path.splitext(os.path.basename(file_path))[0]	### '20210908-075706-BSQQ3HII'
		multi_file_dir = os.path.join(file_dir, name_without_ext)	### '/home/stemweb/Stemweb/media/files/csv/20210908-075706-BSQQ3HII'
		#print('########## RHM input path / multi_file_dir = ', multi_file_dir, '++++++++++++++++++++++++++')
		os.mkdir(multi_file_dir)
		os.chdir(multi_file_dir)

		### file_data contains content of unaligned files; write it into separate files
		### This input format is expected  by binarysankoff_linux.c (=new rhm.c by Teemu Roos)
		try:
			for key, value in file_data.items():
				with open(key, mode = 'w', encoding = 'utf8') as fp:
					json.dump(value, fp)
		except:
			#print ("\n######### could not write input file:", key, " +++++++++++++++++++\n")
			format_error = f"Could not write input file {key}"

	elif (algo_id == '3' or algo_id == '4'):   ### check input data format for NJ and NN:
		with open(input_file.file.path, "r") as file:
			content = file.read()
		# matrix_match = re.search(r"MATRIX\s+(.*?);\s+END;", content, re.DOTALL | re.IGNORECASE)  ### for multi-line content
		matrix_match = re.search(r"MATRIX\n(.*?);", content, re.DOTALL | re.IGNORECASE)  ### for single line content
		if matrix_match:
			matrix = matrix_match.group(1)
			#print(f"Extracted Matrix Block:\n {matrix}")
			validate_res = validate_nexusmatrix(matrix)
			if validate_res != True:
				#print(validate_res)
				format_error = validate_res
		else:
			format_error ="Input data format error: MATRIX block not found"
			#print(format_error)

	parameters = json_data['parameters']

	#print (input_file)
		
	input_file_key = ''
	for arg in algorithm.args.all():
		if arg.value == 'input_file':
			input_file_key = arg.key
		
	run_args = utils.build_external_args(parameters, input_file_key, input_file,
			algorithm_name = algorithm.name, unique_id = unique_id)



	current_run = AlgorithmRun.objects.create(input_file = input_file,
											algorithm = algorithm, 
											folder = os.path.join(algo_root, run_args['folder_url']),
											external = True)
		
	current_run.extras = json.dumps(json_data)
	current_run.save()	# Save to ensure that id generation is not delayed.
	rid = current_run.id

	kwargs = {'run_args': run_args, 'algorithm_run': rid}

	
	inherited_AlgorithmTask = algorithm.get_callable(kwargs)	### inherited: class NJ(AlgorithmTask) or class NN(AlgorithmTask) or class RHM(AlgorithmTask)
		
	#  the celery signature is used to concatenate tasks and to call the errorback;  see:
	#  https://docs.celeryproject.org/en/master/userguide/calling.html
	#  https://docs.celeryproject.org/en/master/userguide/calling.html#linking-callbacks-errbacks
	#  Callbacks can be added to any task using the link argument to apply_async
	#  The callback (->link) will only be applied if the task exited successfully, and it should be applied with the 
	#  return value of the parent task as argument.
	#  If the tasks fails then the errorback (using the link_error argument) is called
	#  Any arguments you add to a signature, will be prepended to the arguments specified by the signature itself!

	if format_error == None:
		inherited_AlgorithmTask.apply_async(kwargs = kwargs,
				link = external_algorithm_run_finished.signature(kwargs = {'run_id': rid, 'return_host': return_host , 'return_path': return_path}, options={}),
				link_error = external_algorithm_run_error.signature(kwargs = {'run_id': rid, 'return_host': return_host , 'return_path': return_path}, options={}))

		#inherited_AlgorithmTask.apply(kwargs = kwargs, link = external_algorithm_run_finished.s(rid, return_host, return_path))  ### use synchronous task for DEBUGGING purpose
	else:	### knowing that RHM input data have a format error, we don't call the calculation of the RHM algorithm, but do this:
		current_run.error_msg = format_error
		current_run.status = settings.STATUS_CODES['failure']
		current_run.save()
		external_algorithm_run_error(None, format_error, run_id=rid, return_host=return_host, return_path=return_path)


	sleep(0.3)	### needed for correct setting of task status ; seems to be a timing problem
	return current_run.id

	

