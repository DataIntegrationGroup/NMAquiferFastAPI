function initMap(center, zoom, dataurl){
    console.log('asdfasdfa', center, dataurl)
    const map = new mapboxgl.Map({
        container: 'map', // container ID
        // Choose from Mapbox's core styles, or make your own style with Mapbox Studio
        style: 'mapbox://styles/mapbox/satellite-streets-v12', // style URL
        center: center, // starting position [lng, lat]
    zoom: zoom, // starting zoom
});

    const layerList = document.getElementById('menu');
    const inputs = layerList.getElementsByTagName('input');

    for (const input of inputs) {
        input.onclick = (layer) => {
            const layerId = layer.target.id;
            if (layerId != 'show_macrostrat'){
                map.setStyle('mapbox://styles/mapbox/' + layerId)
            }else{
                if ($('#show_macrostrat').is(':checked')){
                    map.setLayoutProperty('macrostrat', 'visibility', 'visible');

                }else{
                    map.setLayoutProperty('macrostrat', 'visibility', 'none');
                }
            }
        };
    }

    const popup = new mapboxgl.Popup({
        closeButton: false,
        closeOnClick: false
    });

    var geocoder = new MapboxGeocoder({ accessToken: mapboxgl.accessToken ,
        flyTo: {zoom: 10,
        },

        mapboxgl: mapboxgl
    });

    document.getElementById('geocoder-container').appendChild(geocoder.onAdd(map));

    map.on('mouseenter', 'wells', (e) => {
        map.getCanvas().style.cursor = 'pointer';

        // Copy coordinates array.
        const coordinates = e.features[0].geometry.coordinates.slice();

        // Ensure that if the map is zoomed out such that multiple
        // copies of the feature are visible, the popup appears
        // over the copy being pointed to.
        while (Math.abs(e.lngLat.lng - coordinates[0]) > 180) {
            coordinates[0] += e.lngLat.lng > coordinates[0] ? 360 : -360;
        }
        const description = e.features[0].properties.name
        let wd = JSON.parse(e.features[0].properties.well_depth).value
        if (wd == null){
            wd = 'Not known'
        }

        const txt = '<b>'+description+'</b><br>Well Depth (ft): '+wd

        popup.setLngLat(coordinates).setHTML(txt).addTo(map);

    });

    map.on('mouseleave', 'wells', () => {
        map.getCanvas().style.cursor = '';
        popup.remove();
    });
    map.on('click', 'wells', (e) => {
        const pointid = e.features[0].properties.name
        window.open('/locations/view/' + pointid, '_blank')
    });
    map.on('style.load',  (s) => {
        console.log('style loaded', s)
        console.log($('#show_macrostrat'))
        if ($('#show_macrostrat').is(':checked')){
            map.addSource('macrostrat', {type: 'raster',
                tiles: ["https://tiles.macrostrat.org/carto/{z}/{x}/{y}.png"]})

            map.addLayer({
                id: 'macrostrat',
                type: 'raster',
                source: 'macrostrat',
                minzoom: 0,
                maxzoom: 22,
                paint: {
                    'raster-opacity': 0.5,
                }
            })
        }

        map.addSource('wells', {type: 'geojson',
            data: dataurl });

        map.addLayer({
            id: 'wells',
            type: 'circle',
            source: 'wells',
            paint: {
                'circle-radius': 4,
                'circle-color': '#224bb4',
                'circle-stroke-color': 'rgba(0,0,0,1)',
                'circle-stroke-width': 1,
            }
        });
    });
}

