import {
  LitElement,
  html,
  css,
} from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js';

class GoogleMapsComponent extends LitElement {
  static properties = {
    api_key: {type: String},
    clickEvent: {type: String},
    marker: {type: Object},
    box: {type: Object},
    map_id: {type: String},
    show_layer: {type: Boolean},
    layer_opacity: {type: Number},
  };

  static styles = css`
    #map {
      height: 100%;
      width: 100%;
    }
  `;

  constructor() {
    super();
    this.api_key = '';
    this.clickEvent = '';
    this.marker = null;
    this.box = null;
    this.map_id = '';
    this.show_layer = true;
    this.layer_opacity = 1.0;
    this._map = null;
    this._marker = null;
    this._box = null;
    this._overlay = null;
  }

  updated(changedProperties) {
    if (changedProperties.has('marker')) {
      this._updateMarker();
    }
    if (changedProperties.has('box')) {
      this._updateBox();
    }
    if (
      changedProperties.has('show_layer') ||
      changedProperties.has('layer_opacity')
    ) {
      this._updateOverlay();
    }
  }

  firstUpdated() {
    this._loadGoogleMapsAPI();
  }

  _loadGoogleMapsAPI() {
    if (window.google && window.google.maps) {
      this._initializeMap(window.google.maps);
      return;
    }

    const script = document.createElement('script');
    script.src = `https://maps.googleapis.com/maps/api/js?key=${this.api_key}&callback=initMap&loading=async`;
    script.defer = true;
    script.async = true;
    window.initMap = () => {
      this._initializeMap(window.google.maps);
    };
    document.head.appendChild(script);
  }

  _initializeMap(googleMaps) {
    if (this._map) return;
    const mapDiv = this.shadowRoot.querySelector('#map');
    if (!mapDiv) return;

    this._map = new googleMaps.Map(mapDiv, {
      center: {lat: 37.422697, lng: -122.084113},
      zoom: 14,
      streetViewControl: false,
      mapTypeControl: true,
      fullscreenControl: false,
      mapTypeId: google.maps.MapTypeId.HYBRID,
      clickableIcons: false,
      cameraControl: false,
      zoomControl: true,
      zoomControlOptions: {
          position: googleMaps.ControlPosition.LEFT_TOP,
      },
      tilt: 0,
      rotateControl: false
    });

    this._map.addListener('click', (event) => {
      if (this.clickEvent) {
        this.dispatchEvent(
          new MesopEvent(this.clickEvent, {
            lat: event.latLng.lat(),
            lng: event.latLng.lng(),
          }),
        );
      }
    });
    this._updateOverlay();
  }

  _updateMarker() {
    if (!this._map || !this.marker) return;
    if (this._marker) {
      this._marker.setMap(null);
    }
    this._marker = new google.maps.Marker({
      position: this.marker,
      map: this._map,
    });
  }

  _updateBox() {
    if (!this._map || !this.box) return;
    if (this._box) {
      this._box.setMap(null);
    }
    this._box = new google.maps.Rectangle({
      strokeColor: '#FF0000',
      strokeOpacity: 0.8,
      strokeWeight: 2,
      fillColor: '#FF0000',
      fillOpacity: 0.35,
      map: this._map,
      bounds: this.box,
    });
  }

  _updateOverlay() {
    if (!this._map) return;

    if (this.show_layer && this.map_id) {
      if (!this._overlay) {
        this._overlay = new google.maps.ImageMapType({
          getTileUrl: (coord, zoom) => {
            return `https://earthengine.googleapis.com/v1/${this.map_id}/tiles/${zoom}/${coord.x}/${coord.y}`;
          },
          tileSize: new google.maps.Size(256, 256),
        });
        this._map.overlayMapTypes.insertAt(0, this._overlay);
      }
      this._overlay.setOpacity(this.layer_opacity);
    } else {
      if (this._overlay) {
        this._map.overlayMapTypes.removeAt(0);
        this._overlay = null;
      }
    }
  }

  render() {
    return html`<div id="map"></div>`;
  }
}

customElements.define('google-maps-component', GoogleMapsComponent);

window.downloadImage = (base64Image) => {
  const link = document.createElement('a');
  link.href = base64Image;
  link.download = 'colorized_image.png';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};
