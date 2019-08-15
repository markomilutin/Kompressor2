function contextData = searchForContext(data)
  contextSize = 2;  
  dataLength = size(data)(2);
  maxContextSize = 4;

  contextsCount = {};
  contexts = {};
 
  while(contextSize < maxContextSize)
    contextCountForThisContextSize = {};
    contextsForThisContextSize = {};
    nextContextEntry = 1;
    
    for i = contextSize:(dataLength-contextSize)             
      curContext = data((i-contextSize+1):i);
      curContextIndex = nextContextEntry;
      
      %Check to see if we have a copy of this context
      for index = 1:curContextIndex
        len = size(contextsForThisContextSize)(2);
        if(len >= index)
          value = contextsForThisContextSize{index};
          len = size(value)(2);
          if len != 0
            if curContext == value
              curContextIndex = index;
              break;
            endif
          endif
        endif
      endfor                 
      
      for j = (i+1):(dataLength-contextSize-1)
          compareData = data(j:(j+contextSize-1));
          if(curContext == compareData)  
            currentCount = 0;
            
            if(size(contextCountForThisContextSize)(2) >= curContextIndex)
              currentCount = contextCountForThisContextSize{curContextIndex};
            endif
            
            currentCount += 1;
            
            contextsForThisContextSize{curContextIndex} = curContext;
            contextCountForThisContextSize{curContextIndex} = currentCount;
            
            if curContextIndex == nextContextEntry
              nextContextEntry += 1;
            endif
            
          endif
      endfor            
    endfor
  
    contextsCount{contextSize} = contextCountForThisContextSize;
    contexts{contextSize} = contextsForThisContextSize;
    contextSize += 1;
  endwhile 
endfunction