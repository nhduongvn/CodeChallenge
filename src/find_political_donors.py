#!/usr/bin/env python2.7
import os, sys, re
import copy

def pause():
   rep = ''
   while not rep in [ 'q', 'Q' ]:
     rep = raw_input( 'enter "q" to quit: ' )
     if len(rep) > 1:
       rep = rep[0]

def Extract_info(rec): 
  "Return an array with [CMT_ID,ZIP_CODE,TRANSACTION_DT,TRANSACTION_AMT] = 0, 10, 13, 14"
  #remove all space
  rec = rec.replace(' ','')
  rec_spl = rec.split('|')
  
  #Skip non-empty OTHER_ID or emtpy transaction amount
  if rec_spl[15] != '' or rec_spl[14] == '':
    return []
  #Skip negative or zero transaction amount
  if float(rec_spl[14]) <= 0:
    return []

  zip_code_match = re.match(r"\w{5}",rec_spl[10])
  zip_code = ''
  if zip_code_match != None:
      zip_code = zip_code_match.group(0)
  return [rec_spl[0],zip_code,rec_spl[13],float(rec_spl[14])] #CMT_ID,ZIP_CODE,TRANSACTION_DT,TRANSACTION_AMT

def Get_median(entry_line):
  "Get median from a text line containing all seen entries"
  entry_line_spl = entry_line.split(',')
  entries = [float(entry_line_spl[i]) for i in range(len(entry_line_spl))]
  sorted_entries = sorted(entries)
  length = len(sorted_entries)
  if not length % 2: #even
      return round((sorted_entries[length / 2] + sorted_entries[length / 2 - 1]) / 2.0)
  return round(sorted_entries[length / 2])

def Make_key_for_dict(k1, k2):
  "Unify how to make key for dictionary"
  return k1 + delimiter_dict_key + k2

def Update_dict_vals(input_dict, a_rec_extr, rec_type='zip'): #zip or date
  "Update an extracted record to the dictionary of total number of contribution, total amount of contributions, median of contribution and all contribution amount seen"
  k_tmp = Make_key_for_dict(a_rec_extr[0], a_rec_extr[1])
  if rec_type == 'date':
    k_tmp = Make_key_for_dict(a_rec_extr[0], a_rec_extr[2])
  try:
      input_dict[k_tmp][0] += 1 #total number of contribution
      input_dict[k_tmp][1] += a_rec_extr[3] #total amount of contribution
      input_dict[k_tmp][3] = input_dict[k_tmp][3] + ',' + str(a_rec_extr[3]) #all contribution seen so far
      input_dict[k_tmp][2] = Get_median(input_dict[k_tmp][3])
  except KeyError: 
      input_dict[k_tmp] = [1,a_rec_extr[3],a_rec_extr[3],str(a_rec_extr[3])]

def Write_to_file(fName, records,write_mode = 'w'):
  "Write records to file"
  with open(fName,write_mode) as f:
    for rec in records: 
      line = rec[0]
      for i in range(1, len(rec)):
        line = line + '|' + str(rec[i])
      line = line + '\n'
      f.write(line)

def Update_records_and_write(n_chunk, records, fOut_zip_name_prefix):
  "Update records in a chunk with information from previous streaming records stored in files"
  #loop in reversed order of the chunks to get the latest running values (count and total). Repeat untill all records are updated     
  if len(records) == 0: return
  indexes_leftOver = [x for x in range(len(records))] # index of records do not find in previous chunks
  for iChunk in reversed(range(1,n_chunk)):
    pre_vals = {} #dict of previous 
    with open(fOut_zip_name_prefix + '_' + str(iChunk) + '.txt', 'r') as f:
      for line in f:
        line = line.replace('\n','')
        line_spl = line.split('|')
        k = Make_key_for_dict(line_spl[0],line_spl[1])
        pre_vals[k] = [line_spl[2],line_spl[3],line_spl[5]] #total number of contribution, total amount of countribution, all contribution seen until this point
    
    #update the records
    iL = 0
    while iL < len(indexes_leftOver):
      ind = indexes_leftOver[iL]
      k = Make_key_for_dict(records[ind][0],records[ind][1])
      
      try:

        #found record in previous chunk, update record
        new_n_contri = int(pre_vals[k][0]) + int(records[ind][2])
        new_sum_contri = float(pre_vals[k][1]) + float(records[ind][3])
        all_contribution_str = pre_vals[k][2] + ',' + records[ind][5]
        new_median = Get_median(all_contribution_str) 
        records[ind][2] = new_n_contri
        records[ind][3] = new_sum_contri
        records[ind][4] = new_median
        records[ind][5] = all_contribution_str

        #remove updated record
        del indexes_leftOver[iL]
      
      except KeyError:
        iL += 1

  Write_to_file(fOut_zip_name_prefix + '_' + str(n_chunk) + '.txt', records) 

#make a text line from a record
def Make_text_line(rec_or_dict, k = ''):
  if k == '':
    return rec_or_dict[0] + '|' + rec_or_dict[1] + '|' + str(rec_or_dict[2]) + '|' + str(rec_or_dict[3]) + '|'+ str(rec_or_dict[4]) + '|' + rec_or_dict[5] + '\n'
  else:
    return k.split(delimiter_dict_key)[0] + '|' + k.split(delimiter_dict_key)[1] + '|' + str(rec_or_dict[0]) + '|' + str(rec_or_dict[1]) + '|'+ str(rec_or_dict[2]) + '|' + rec_or_dict[3] + '\n'


def Update_date_records_write_to_file(n_chunk, date_data_dict, fOut_date_name_prefix):
  "Update an extracted record to the dictionary of total number of contribution, total amount of contributions, median of contribution and all contribution amount seen"
  
  chunk_size_read_line = 10000 #used to read previous file of previous data chunk. This is the amount of lines is read and processed each time
  
  #first chunk, write to file
  if n_chunk == 1:
    with open(fOut_date_name_prefix + '_' + str(n_chunk) + '.txt','w') as f:
      for k,v in date_data_dict.items():
        f.write(Make_text_line(v, k))

  else:
    open_file_mode = 'w'
    lines = [] 
    iLine = 0
    with open(fOut_date_name_prefix + '_' + str(n_chunk-1) + '.txt','r') as f:
      for line in f:
        iLine += 1
        line = line.replace('\n','')
        prev_record = line.split('|')
        k = Make_key_for_dict(prev_record[0],prev_record[1])
        #entry k found in previous record, update previous record by this entry k
        try:
          prev_record[2] = str(int(prev_record[2]) + date_data_dict[k][0]) #total contribution
          prev_record[3] = str(float(prev_record[3]) + date_data_dict[k][1]) #total amount of contributions
          prev_record[5] = prev_record[5] + ',' + date_data_dict[k][3] #all amount of contribution seen so far
          prev_record[4] = str(Get_median(prev_record[5]))
          lines.append(Make_text_line(prev_record))
          del date_data_dict[k]
        except KeyError:
          lines.append(Make_text_line(prev_record))
          continue
        
        #stop and write lines to file 
        if iLine % chunk_size_read_line == 0:
          with open(fOut_date_name_prefix + '_' + str(n_chunk) + '.txt',open_file_mode) as f1:
            for l in lines:
              f1.write(l)
          open_file_mode = 'a'
          lines = []
      
    #write remaining lines and remaining date_data_dict (no match found in previous chunk)
    #print lines
    with open(fOut_date_name_prefix + '_' + str(n_chunk) + '.txt', open_file_mode) as f1:
      for l in lines:
        f1.write(l)
      for k,v in date_data_dict.items():
        f1.write(Make_text_line(v,k))

def Merge_zip_data_write(n_chunk, fName_prefix_chunks, fName_prefix_all):
  with open(fName_prefix_all + '.txt','w') as f:
    for iChunk in range(1,n_chunk+1):
      with open(fName_prefix_chunks + '_' + str(iChunk) + '.txt', 'r') as f1:
        for line in f1:
          line = line.split('|')
          line = line[0] + '|' + line[1] + '|%d|%d|%d\n' % (float(line[4]),float(line[2]),float(line[3]))
          f.write(line)

def Merge_date_data_write(n_chunk, fName_prefix_chunks, fName_prefix_all):
  dict_date = {}
  try:
    with open(fName_prefix_chunks + '_' + str(n_chunk) + '.txt', 'r') as f1:
      for line in f1:
        line_spl = line.split('|')
        a_line = '%d|%d|%d\n' % (float(line_spl[4]),float(line_spl[2]),float(line_spl[3]))
        dict_date[Make_key_for_dict(line_spl[0], line_spl[1])] = a_line 
  except:
    print('Error while trying to merge data. Your data might be too large to fit in the memory! External merge sort needed!')
    exit()
  with open(fName_prefix_all + '.txt','w') as f:
    for k in sorted(dict_date.keys()):  
      a_line = k.split(delimiter_dict_key)[0] + '|' + k.split(delimiter_dict_key)[1] + '|' + dict_date[k]
      f.write(a_line)


#######################
#Main program
#######################

if len(sys.argv) < 4:
    print 'Improper inputs: require 1 input and 2 output. Will exit now!'
    exit()

print 'Current directory is: ', os.getcwd()

fIn_name = sys.argv[1]
fOut_zip_name = sys.argv[2]
fOut_date_name = sys.argv[3]
fOut_zip_name_prefix = fOut_zip_name.replace('.txt','')
fOut_date_name_prefix = fOut_date_name.replace('.txt','')

#TODO: remember to remove output files

#check opening file
try:
  f = open(fIn_name, mode='r')
  f.close()
except IOError:
  print 'Can not open file: ' + fIn_name + '. Will exit now!'
  exit()

delimiter_dict_key = '_' #use to make key for dictionary from CMTE_ID and zip code or CMTE_ID and day

chunk_record_zip = 50000 #number of records in a chunk, records will be written to files, each of them has chunk_records lines
n_chunk_zip = 0
fOut_zip_name_prefix_chunk = 'Tmp/zip_data_tmp'

chunk_record_date = 50000
n_chunk_date = 0
fOut_date_name_prefix_chunk = 'Tmp/date_data_tmp'

zip_records = []
zip_running_vals = {} 

date_running_vals = {}

countLine = 0
n_records_zip = 0
n_records_date = 0

with open(fIn_name) as fIn:

  for rec in fIn:
    
    countLine += 1
    
    rec_extr = Extract_info(rec)

    #skip OTHER_ID non-empty record
    if len(rec_extr) == 0: continue
    
    #found valid zip code data process it
    if rec_extr[1] != '':
      
      n_records_zip += 1

      Update_dict_vals(zip_running_vals, rec_extr)
  
      #append records to record list
      k_tmp = Make_key_for_dict(rec_extr[0],rec_extr[1])
      v = zip_running_vals[k_tmp]
      zip_records.append([rec_extr[0], rec_extr[1], v[0], v[1], v[2], v[3]]) #CMT, zip, total number of contri, total amount of contribution, running median, all contributioin amount seen so far
    
    #found valid date data process it
    if rec_extr[2] != '':

      n_records_date += 1

      Update_dict_vals(date_running_vals, rec_extr,'date')


###################################
#Dump data to file
###################################
    if n_records_zip%chunk_record_zip == 0:
      if len(zip_records) > 0:
        print 'Finishing to process %.0f records of zip code data' %(n_records_zip)
        print 'Writing records to file'
            
        n_chunk_zip += 1
        Update_records_and_write(n_chunk_zip, zip_records, fOut_zip_name_prefix_chunk)
        zip_records = []
        zip_running_vals = {}
    
    if n_records_date%chunk_record_date == 0:
      if len(date_running_vals) > 0:
        print 'Finishing to process %.0f records of date data' %(n_records_date)
        print 'Writing records to file'
        #print date_running_vals       
        n_chunk_date += 1
        Update_date_records_write_to_file(n_chunk_date, date_running_vals, fOut_date_name_prefix_chunk)
        #pause()
        date_running_vals = {}

####################################
#Dump remaining chunk of data to file
####################################
  if len(zip_records) > 0:
    print 'Finishing to process %.0f records of zip code data' %(n_records_zip)
    print 'Writing records to file'
    n_chunk_zip += 1
    Update_records_and_write(n_chunk_zip,zip_records,fOut_zip_name_prefix_chunk)
    zip_records = []
  
  if len(date_running_vals) > 0:
    print 'Finishing to process %.0f records of date data' %(n_records_date)
    print 'Writing records to file'
    n_chunk_date += 1
    Update_date_records_write_to_file(n_chunk_date, date_running_vals, fOut_date_name_prefix_chunk)
    date_running_vals = {}

##################
#Now merge and write 
##################
Merge_zip_data_write(n_chunk_zip, fOut_zip_name_prefix_chunk, fOut_zip_name_prefix)

Merge_date_data_write(n_chunk_date, fOut_date_name_prefix_chunk, fOut_date_name_prefix)


##################
#clean
###################
#os.system('rm Tmp/*')

