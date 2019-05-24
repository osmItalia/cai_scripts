function slugify(instr){
    return instr.toLowerCase().replace(/ /g,'-').replace(/'/g,'-').replace(/\//g,'-').replace(/é/g,'e').replace(/ü/g,'u');
}

function randomIntFromInterval(min,max) // min and max included
{
    return Math.floor(Math.random()*(max-min+1)+min);
}

var cai_scale = {'T': '', 'E': [10, 10], 'EE': [5, 5], 'EEA': [2, 2], 'EAI': [2, 2]}
var styleCache = {};
function routeStyleFunction(feature, resolution) {
	var type = feature.get('cai_scale');
	if (!styleCache[type]) {
		if (type == 'T'){
        styleCache[type] = [new ol.style.Style({
		     stroke: new ol.style.Stroke({
	          color: '#f00',
	          width: 1
	        }),
	        text: new ol.style.Text({
	          font: '12px Calibri,sans-serif',
	          fill: new ol.style.Fill({
	            color: '#000'
	          }),
	          stroke: new ol.style.Stroke({
	            color: '#fff',
	            width: 3
	          })
	        })
	     })]
	   } else {
	     styleCache[type] = [new ol.style.Style({
		     stroke: new ol.style.Stroke({
	          color: '#f00',
	          width: 1,
	          lineDash: cai_scale[type]
	        }),
	        text: new ol.style.Text({
	          font: '12px Calibri,sans-serif',
	          fill: new ol.style.Fill({
	            color: '#000'
	          }),
	          stroke: new ol.style.Stroke({
	            color: '#fff',
	            width: 3
	          })
	        })
	     })]
	   }
   }
   //TODO set label from ref
   /*
   if (resolution < 10) {
   	 var ref = feature.get('ref');
   	 label = new ol.style.Style({
   	 	  geometry: function(feature) {
			    var geometry = feature.getGeometry();
			    var outGeoms = [];
			    if (geometry.getType() == 'MultiLineString') {
			      var lines = geometry.getLineStrings();
			      for (var i = 0, ii = lines.length; i < ii; ++i) {
			        var line = lines[i];
			        if (line.getLength() > 1000){
			           	outGeoms.push(line)
			        }
			      }
			      console.log(outGeoms);
			    return new ol.geom.MultiLineString(outGeoms);
			    }
			  },
   	 	  text: new ol.style.Text({
   	 	  	 text: ref,
	          font: '12px Calibri,sans-serif',
	          fill: new ol.style.Fill({
	            color: '#000'
	          }),
	          stroke: new ol.style.Stroke({
	            color: '#fff',
	            width: 3
	          }),
	          placement: 'LINE',
	          offsetX: randomIntFromInterval(20, 40),
	          offsetY: randomIntFromInterval(20, 40)
	        })
	     })
	     styleCache[type].push(label);
   }
   */
	return styleCache[type];
}

function highlightStyleFunction(feature, resolution) {
	var type = feature.get('cai_scale');
	if (!styleCache[type]) {
		if (type == 'T'){
        styleCache[type] = [new ol.style.Style({
		     stroke: new ol.style.Stroke({
	          color: '#000',
	          width: 1
	        }),
	        text: new ol.style.Text({
	          font: '12px Calibri,sans-serif',
	          fill: new ol.style.Fill({
	            color: '#000'
	          }),
	          stroke: new ol.style.Stroke({
	            color: '#fff',
	            width: 3
	          })
	        })
	     })]
	   } else {
	     styleCache[type] = [new ol.style.Style({
		     stroke: new ol.style.Stroke({
	          color: '#000',
	          width: 1,
	          lineDash: cai_scale[type]
	        }),
	        text: new ol.style.Text({
	          font: '12px Calibri,sans-serif',
	          fill: new ol.style.Fill({
	            color: '#000'
	          }),
	          stroke: new ol.style.Stroke({
	            color: '#fff',
	            width: 3
	          })
	        })
	     })]
	   }
   }
   //TODO set label from ref
   /*
   if (resolution < 10) {
   	 var ref = feature.get('ref');
   	 label = new ol.style.Style({
   	 	  geometry: function(feature) {
			    var geometry = feature.getGeometry();
			    var outGeoms = [];
			    if (geometry.getType() == 'MultiLineString') {
			      var lines = geometry.getLineStrings();
			      for (var i = 0, ii = lines.length; i < ii; ++i) {
			        var line = lines[i];
			        if (line.getLength() > 1000){
			           	outGeoms.push(line)
			        }
			      }
			      console.log(outGeoms);
			    return new ol.geom.MultiLineString(outGeoms);
			    }
			  },
   	 	  text: new ol.style.Text({
   	 	  	 text: ref,
	          font: '12px Calibri,sans-serif',
	          fill: new ol.style.Fill({
	            color: '#000'
	          }),
	          stroke: new ol.style.Stroke({
	            color: '#fff',
	            width: 3
	          }),
	          placement: 'LINE',
	          offsetX: randomIntFromInterval(20, 40),
	          offsetY: randomIntFromInterval(20, 40)
	        })
	     })
	     styleCache[type].push(label);
   }
   */
	return styleCache[type];
}

var osm = new ol.layer.Tile({
	source: new ol.source.OSM()
});
var map, features, table;

function home_map(){
    var md = new MobileDetect(window.navigator.userAgent);

    var regionStyle = new ol.style.Style({
        stroke: new ol.style.Stroke({
          color: '#f00',
          width: 1
        }),
        fill: new ol.style.Fill({
          color: 'rgba(255,0,0,0.1)'
        }),
        text: new ol.style.Text({
          font: '12px Calibri,sans-serif',
          fill: new ol.style.Fill({
            color: '#000'
          }),
          stroke: new ol.style.Stroke({
            color: '#fff',
            width: 3
          })
        })
    });


    var italy_source = new ol.source.Vector({
	     url: '/static/data/italy.geojson',
	     format: new ol.format.GeoJSON()
	 })
	 var italy = new ol.layer.Vector({
        source: italy_source,
        style: function(feature) {
          regionStyle.getText().setText(feature.get('Name'));
          return regionStyle;
        }
	 })
    map = new ol.Map({
        layers: [osm, italy],
        target: 'map',
        view: new ol.View({
            center: ol.proj.transform([12.4853384, 41.8948020],'EPSG:4326','EPSG:3857'),
            zoom: 6
        })
    });
    if (md.mobile() != null){
   	map.setZoom(5);
    }
    

    // display popup on click
    map.on('click', function(evt) {
        var feature = map.forEachFeatureAtPixel(evt.pixel,
            function(feature) {
		          return feature;
	         });
	         region = slugify(feature.get('Name'))
	         window.open('/regione/' + region, '_self')
	 })
}

function home_table(){
	$.ajax({
        type: "GET",
        url: "/static/data/cai_osm.csv",
        dataType: "text",
        success: function(data) {
        	 var allTextLines = data.split(/\r\n|\n/);
        	 var line = allTextLines[0].split('|');
        	 var atext = '<tr><td><a href="/sezioneroute/' + line[0] + '">' + line[1] + '</a></td>';
        	 for (var i=1; i<allTextLines.length; i++) {
        	 	line = allTextLines[i].split('|');
        	 	if (line.length == 1){
        	 	   continue;
        	 	}
        	 	if (i == allTextLines.length - 1){
					atext = atext + '<td><a href="/sezioneroute/' + line[0] + '">' + line[1] + '</a></td></tr>';
        	 	} else if ( (i % 4) == 0 ) {
        	 	   atext = atext + '</tr><tr><td><a href="/sezioneroute/' + line[0] + '">' + line[1] + '</a></td>';
        	 	} else {
        	 	   atext = atext + '<td><a href="/sezioneroute/' + line[0] + '">' + line[1] + '</a></td>';
        	 	}
        	 }
        	 $( "#osmtable" ).append(atext);
         } 
     });
}

function region_map(region) {
	 
	 var routes_source = new ol.source.Vector({
	     url: '/static/regions/'+region+'.geojson',
	     format: new ol.format.GeoJSON()
	 })
	 var routes = new ol.layer.Vector({
        source: routes_source,
        style: routeStyleFunction
	 })

    map = new ol.Map({
        layers: [osm, routes],
        target: 'map',
        view: new ol.View({
            center: ol.proj.transform([12.4853384, 41.8948020],'EPSG:4326','EPSG:3857'),
            zoom: 6
        })
    });
    routes_source.once('change',function(e){
	     if(routes_source.getState() === 'ready') {
	         var extent = routes_source.getExtent();
	         map.getView().fit(extent, map.getSize());
	         features = routes_source.getFeatures();
	     }
	 });
	 map.on('click', function(evt) {
        var feature = map.forEachFeatureAtPixel(evt.pixel,
            function(feature) {
            	 if (feature) {
		              return feature;
		          } else {
		          	  return null;
		          } 
	         }
	     );
	     if (feature){
	         table.columns(0).search(feature.get('id')).draw();
	     }
	 })
}

function find_route(value){
	var found;
	for (var i = 0, ii = features.length; i < ii; i++) {
	  if (features[i].get('id') == value) {
	    found = features[i];
	    return found;
	  }
	}
}

function region_table(region){
	 $.fn.dataTable.ext.errMode = 'none';
	 table = $('#osmtable').DataTable({
        "ajax": {
        	    url: '/static/regions/'+region+'.json',
        	    dataSrc: ''
        }, 
        "columns": [
            { data: "id" },
            { data: "name" },
            { data: "ref" },
            { data: "cai_scale" },
            { data: "from" },
            { data: "to" },
            { data: "distance" },
            { data: "symbol:it" },
            { data: "id" },
        ],
        "columnDefs": [{
            "targets": -1,
            "data": "id",
            "render": function(data, type, full, meta) {
			      out = '<a href="https://www.openstreetmap.org/relation/'+data+'" target="_blank">OpenStreetMap</a><br>';
			      out = out + '<a href="https://www.openstreetmap.org/edit?relation='+data+'" target="_blank">OpenStreetMap Edit</a><br>';
			      out = out + '<a href="http://ra.osmsurround.org/analyzeRelation?relationId='+data+'" target="_blank">analyzeRelation</a><br>';
			      out = out + '<a href="http://hiking.waymarkedtrails.org/#route?id='+data+'" target="_blank">Hiking waymarkedtrails</a><br>';
			      out = out + '<a href="https://hiking.waymarkedtrails.org/api/details/relation/'+data+'/gpx" target="_blank">GPX</a>';
			      return out;
			   } 
        }]
    });
    table.on('click', 'td', function () {
		  var data = table.cell( this ).data();
		  route = find_route(data);
		  if (route != undefined){
		      var ext = route.getGeometry().getExtent(); 
		      map.getView().fit(ext, map.getSize());
		  }
    })
}

function sezione_map(region) {
	 var routes_source = new ol.source.Vector({
	     url: '/sezionegeojson/'+region,
	     format: new ol.format.GeoJSON()
	 })
	 var routes = new ol.layer.Vector({
        source: routes_source,
        style: routeStyleFunction
	 })

    map = new ol.Map({
        layers: [osm, routes],
        target: 'map',
        view: new ol.View({
            center: ol.proj.transform([12.4853384, 41.8948020],'EPSG:4326','EPSG:3857'),
            zoom: 6
        })
    });
    routes_source.once('change',function(e){
    	  if(routes_source.getState() === 'loading') {
    	  	   //$(".se-pre-con").fadeIn("fast");
    	  	   console.log('loading');
    	  }
	     if(routes_source.getState() === 'ready') {
	     	   //$(".se-pre-con").fadeOut("slow");
	         var extent = routes_source.getExtent();
	         map.getView().fit(extent, map.getSize());
	         features = routes_source.getFeatures();
	         console.log('loaded')
	     }
	 });
	 map.on('click', function(evt) {
        var feature = map.forEachFeatureAtPixel(evt.pixel,
            function(feature) {
		          return feature;
	         }
	     );
	     feature.setStyle(highlightStyleFunction);
	     table.columns(0).search(feature.get('id')).draw();
	 })
}

function sezione_table(region){
	 $.fn.dataTable.ext.errMode = 'none';
	 table = $('#osmtable').DataTable({
        "ajax": {
        	    url: '/sezionejson/'+region,
        	    dataSrc: ''
        }, 
        "columns": [
            { data: "id" },
            { data: "name" },
            { data: "ref" },
            { data: "cai_scale" },
            { data: "from" },
            { data: "to" },
            { data: "distance" },
            { data: "symbol:it" },
            { data: "id" },
        ],
        "columnDefs": [{
            "targets": -1,
            "data": "id",
            "render": function(data, type, full, meta) {
			      out = '<a href="https://www.openstreetmap.org/relation/'+data+'" target="_blank">OpenStreetMap</a><br>';
			      out = out + '<a href="https://www.openstreetmap.org/edit?relation='+data+'" target="_blank">OpenStreetMap Edit</a><br>';
			      out = out + '<a href="http://ra.osmsurround.org/analyzeRelation?relationId='+data+'" target="_blank">analyzeRelation</a><br>';
			      out = out + '<a href="http://hiking.waymarkedtrails.org/#route?id='+data+'" target="_blank">Hiking waymarkedtrails</a><br>';
			      out = out + '<a href="https://hiking.waymarkedtrails.org/api/details/relation/'+data+'/gpx" target="_blank">GPX</a>';
			      return out;
			   } 
        }]
    });
    table.on('click', 'td', function () {
		  var data = table.cell( this ).data();
		  route = find_route(data);
		  if (route != undefined){
		      var ext = route.getGeometry().getExtent(); 
		      map.getView().fit(ext, map.getSize());
		  }
    })
}

function clearFilter(){
    table.search( '' ).columns().search( '' ).draw();
}