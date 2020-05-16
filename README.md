This project is an improved version of the Enphase Envoy sensor currently in the Home Assistant core.
See: https://github.com/home-assistant/core/tree/dev/homeassistant/components/enphase_envoy 

It uses local and new implementation of the Envoy Reader that is compatible with the R4.10 firmware.
This implementation was inspired by:
https://github.com/jesserizzo/envoy_reader


The data collection in the version is improved because it now used the DataUpdateCoordinator pattern so all data is collected at once and not for each sensor.


###### References

* https://thecomputerperson.wordpress.com/2016/08/03/enphase-envoy-s-data-scraping/
* https://www.datafix.com.au/BASHing/2019-09-06.html
* https://enphase.com/sites/default/files/Envoy-API-Technical-Brief.pdf
