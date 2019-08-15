function [data, uniquesymbols, accumulatedatapercent] = loadBinaryFileAndProfile(name)
  file = fopen(name, "r");
  data = fread(file, Inf, "uchar");

  data = data';

  [uniquesymbols, ~, symbolcounts] = unique (testdata);
  accumulatedata = accumarray(symbolcounts', 1);

  accumulatedatapercent = accumulatedata/size(testdata,2);
  
  fclose(testfile);

  plot(uniquesymbols, accumulatedatapercent);
endfunction