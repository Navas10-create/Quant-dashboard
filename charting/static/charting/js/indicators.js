// lightweight indicator implementations (synchronous, simple)
const Indicators = (function(){
  function SMA(values, period){
    const out = [];
    let sum = 0;
    for(let i=0;i<values.length;i++){
      sum += values[i];
      if(i>=period) sum -= values[i-period];
      out.push(i>=period-1 ? sum/period : null);
    }
    return out;
  }

  function EMA(values, period){
    const out = [];
    const k = 2/(period+1);
    let prev = values[0];
    out.push(prev);
    for(let i=1;i<values.length;i++){
      prev = (values[i] * k) + (prev * (1-k));
      out.push(prev);
    }
    return out;
  }

  function RSI(values, period){
    const out = [];
    let gain=0, loss=0;
    for(let i=1;i<values.length;i++){
      const diff = values[i]-values[i-1];
      gain = (diff>0)? diff : 0;
      loss = (diff<0)? -diff : 0;
      if(i===1){
        // seed with first
        out.push(null);
        var avgGain = gain, avgLoss = loss;
      } else {
        avgGain = (avgGain*(period-1)+gain)/period;
        avgLoss = (avgLoss*(period-1)+loss)/period;
        const rs = avgGain/(avgLoss||1e-9);
        out.push(100 - (100/(1+rs)));
      }
    }
    out.unshift(null); // adjust for length
    return out;
  }

  return { SMA, EMA, RSI };
})();
