This package extracts the individual contribution data from the Federal Election Commission repository (http://classic.fec.gov/finance/disclosure/ftpdet.shtml).

To run the package:
1. Python 2.7 is used 
2. ./run.sh

The source code is a Python script located at src/. How the code works:
1. Load the input data file line by line
2. Extract the relevant information from the line: CMTE_ID, ZIP_CODE, TRANSACTION_DT, TRANSACTION_AMT, OTHER_ID
3. Build two lists:
   3a. medianvals_by_zip.txt: contribution from individual by zip code together with running median and total contribution amount seen 
   3b. medianvals_by_date.txt: contribution received by recipient on a particular day

To address the large input data set issue, the input data are processed chunk by chunk. The results from each chunk are written to a temporary file. The temporary files also keep all the contribution amount seen to calculate the running median or overall median of the contribution amount of the data set. Note that for making medianvals_by_zip, we do not need to keep the all the entries when data are streaming but only the most updated entries. For example, if in the current data stream, we see an entry = CMTE_ID + TRANSACTION_DT which was also seen in previous data chunk, we should update this current entry with information of corresponding previous entry and write it to the file. We also need to write to the file other entries from previous chunk that are not seen in current chunk. In other word, for each chunk of data, we are writing a growing list of unique entries to the file. After all the data are processed, we just need to look at the latest file to build the medianvals_by_date.txt. In contrast, for building medianvals_by_zip.txt, all the temporary files of all data chunks are kept and used in the mearging step in the end.       

The code scales fairly well with large input data set. However there are some limitations which can be solved:
1. The median calculation of contribution amount received: currently, all the contribution amount seen (sequence of contribution amounts) is written together with the contribution entry. The median is calculated from this sequence. Therefore, if the number of contribution at a recipient at a particular day or at a particular zip code becomes large, this sequence can not be fitted into memory when median calculation is used (for example, all people in a dense population zip code contribute to the same recipient which is rare but could be). In this case, further breakdown of the contribution amount sequence in median calculation or approximation techniques for median calculation is needed.
2. The medianvals_by_date sorting is done by loading all entries into memory. This can be solved by external merge sort algorithm.
  
  

