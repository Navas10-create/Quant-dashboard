// very lightweight drawing overlay system
const DrawingTools = (function(){
  let canvas, ctx, chartObj, series;
  const drawings = []; // in-memory; persist to backend/localStorage later
  let mode = null;
  let tempPoints = [];

  function screenToTimePrice(x,y){
    const coords = chartObj.priceScale('right').coordinateToLogical ? null : null;
    // lightweight-charts doesn't provide direct pixel->time/price, so we approximate using timeScale coordinate conversion:
    const time = chartObj.timeScale().coordinateToTime(x);
    const price = series.coordinateToPrice ? series.coordinateToPrice(y) : null;
    return { time: Math.round(time), price: price };
  }

  function redraw(){
    // clear overlay
    ctx.clearRect(0,0,canvas.width,canvas.height);
    ctx.save();
    ctx.scale(1,1);
    drawings.forEach(d=>{
      ctx.strokeStyle = d.color||'#ff0';
      ctx.lineWidth = d.width||2;
      if(d.type === 'trendline' && d.points.length>=2){
        const p1 = chartObj.timeScale().timeToCoordinate(d.points[0].time);
        const p2 = chartObj.timeScale().timeToCoordinate(d.points[1].time);
        const priceToY = (p)=> series.priceToCoordinate ? series.priceToCoordinate(p) : null;
        const y1 = priceToY(d.points[0].price);
        const y2 = priceToY(d.points[1].price);
        if(p1 && p2 && y1 && y2){
          ctx.beginPath();
          ctx.moveTo(p1, y1);
          ctx.lineTo(p2, y2);
          ctx.stroke();
        }
      }
      // more shapes...
    });
    ctx.restore();
  }

  function mouseDown(e){
    if(!mode) return;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const tp = chartObj.timeScale().coordinateToTime(x);
    // approximate price via price scale conversion
    const price = series.priceScale().coordinateToPrice ? series.priceScale().coordinateToPrice(y) : null;
    tempPoints.push({time: Math.round(tp), price});
    if(mode==='trendline' && tempPoints.length===2){
      drawings.push({type:'trendline', points: [tempPoints[0], tempPoints[1]], color:'#00ff00'});
      tempPoints = [];
      mode = null;
      redraw();
    }
  }

  function init(cvs, cctx, ch){
    canvas = cvs;
    ctx = cctx;
    chartObj = ch;
    // locate series used for coordinate conversions
    // assume first series is candle series
    series = chartObj._internal__series && chartObj._internal__series[0] ? chartObj._internal__series[0] : null;
    // attach interactive events
    canvas.addEventListener('mousedown', mouseDown);
    window.addEventListener('resize', redraw);
  }

  function startTool(t, ch, s){
    mode = t;
    chartObj = ch;
    series = s;
    tempPoints = [];
  }

  return { init, startTool, redrawAll: redraw, redraw };
})();
