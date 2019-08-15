function [data, uniquesymbols, accumulatedatapercent] = loadBinaryFileAndProfile(name)
  file = fopen(name, "r");
  data = fread(file, Inf, "uchar");

  data = data';

  [uniquesymbols, ~, symbolcounts] = unique (data);
  accumulatedata = accumarray(symbolcounts', 1);

  accumulatedatapercent = accumulatedata/size(data,2);
  
  fclose(file);

  plot(uniquesymbols, accumulatedatapercent);
endfunction