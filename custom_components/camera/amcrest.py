"""
This version of the amcrest camera component contains enhancements for 
PTZ control, playing audio files, and rebooting the camera via services.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/camera.amcrest/
"""

import logging

import voluptuous as vol
import homeassistant.helpers.config_validation as cv
import requests
# import aiohttp
from homeassistant.components.amcrest import (
    DATA_AMCREST, STREAM_SOURCE_LIST, TIMEOUT)
# from homeassistant.const import (
# ATTR_ENTITY_ID, ATTR_PRESET)
from homeassistant.components.camera import Camera
from homeassistant.components.ffmpeg import DATA_FFMPEG

from homeassistant.const import CONF_NAME
from homeassistant.helpers.aiohttp_client import (
    async_get_clientsession, async_aiohttp_proxy_web,
    async_aiohttp_proxy_stream)
from requests.auth import HTTPDigestAuth
VERSION = '0.1.0'
DEPENDENCIES = ['amcrest', 'ffmpeg']
DOMAIN = 'amcrest'
_LOGGER = logging.getLogger(__name__)

ATTR_PRESET = "preset";
ATTR_ENTITY_ID = "entity_id";
ATTR_FILE = "file";

SERVICE_PTZ = "go_to_preset";
SERVICE_PTZ_SCHEMA = vol.Schema({
    ATTR_ENTITY_ID:  cv.entity_id,
    ATTR_PRESET:  vol.All(vol.Coerce(int), vol.Range(min=0))
});

SERVICE_DO = "do";
SERVICE_DO_SCHEMA = vol.Schema({
    ATTR_ENTITY_ID:  cv.entity_id,
    ATTR_FILE:  cv.string
});
SERVICE_PLAY_WAV = "play_wav";
SERVICE_PLAY_WAV_SCHEMA = vol.Schema({
    ATTR_ENTITY_ID:  cv.entity_id,
    ATTR_FILE:  cv.string
});

ATTR_START = "point_a";
ATTR_END = "point_b";

SERVICE_MOVE_DIRECTLY = "move_directly";
SERVICE_MOVE_DIRECTLY_SCHEMA = vol.Schema({
    ATTR_ENTITY_ID:  cv.entity_id,
    ATTR_START:  cv.string,
    ATTR_END:  cv.string
});

SERVICE_REBOOT = "reboot";
SERVICE_REBOOT_SCHEMA = vol.Schema({
    ATTR_ENTITY_ID:  cv.entity_id
});

async def async_setup_platform(hass, config, async_add_entities,
                               discovery_info=None):
    """Set up an Amcrest IP Camera."""
    if discovery_info is None:
        return

    device_name = discovery_info[CONF_NAME]
    amcrest = hass.data[DATA_AMCREST][device_name]

    async_add_entities([AmcrestCam(hass, amcrest)], True)
    
    def handle_go_to_preset(call):
        """Move camera to given preset"""
        preset = call.data.get(ATTR_PRESET, "1")
        _LOGGER.info("Moved {} to preset {}".format(call.data[ATTR_ENTITY_ID], preset));
        this_camera = get_camera(call);

        # _LOGGER.info(dir(this_camera.device)); 
        result = this_camera.go_to_preset(action='start', channel=0, preset_point_number=preset);
        _LOGGER.info(result);
        return result == 'OK';
    hass.services.async_register(DOMAIN, SERVICE_PTZ, handle_go_to_preset, schema=SERVICE_PTZ_SCHEMA)

    # def handle_do(call):
    #     _LOGGER.info("Doing {}".format(call.data[ATTR_ENTITY_ID]));
    #     this_camera = get_camera(call);
    #     this_camera.play_wav(path_file=file);

    #     return True
    def handle_move_directly(call):
        _LOGGER.info("Move directly {}".format(call.data[ATTR_ENTITY_ID]));
        this_camera = get_camera(call);

        start = call.data.get(ATTR_START).split(',');
        end = call.data.get(ATTR_END).split(',');
        if val_coord(start) and val_coord(end):
            _LOGGER.info("Coordinates are valid");
        else:
            _LOGGER.info("Coordinates are NOT valid");
        _LOGGER.info(dir(this_camera)); 
        _LOGGER.info(this_camera.ptz_status(channel=0)); 
        result = this_camera.move_directly(channel=1, startpoint_x=int(start[0]), startpoint_y=int(start[1]), endpoint_x=int(end[0]), endpoint_y=int(end[1]));
        _LOGGER.info(result);

        return result == 'OK';
    hass.services.async_register(DOMAIN, SERVICE_MOVE_DIRECTLY, handle_move_directly, schema=SERVICE_MOVE_DIRECTLY_SCHEMA)

    def val_coord(c):
        """Validates a coordinate for move_directly service"""
        return int(c[0]) >= 0 and int(c[0]) < 8192 and int(c[1]) >= 0 and int(c[1]) < 8192

    def handle_reboot(call):
        """Reboots the camera"""
        this_camera = get_camera(call);
        _LOGGER.info("Rebooting camera {}".format(call.data[ATTR_ENTITY_ID]));
        result = this_camera.shutdown();
        _LOGGER.info(result);
        return result == 'OK';
    hass.services.async_register(DOMAIN, SERVICE_REBOOT, handle_reboot, schema=SERVICE_REBOOT_SCHEMA);
        
    def handle_play_wav(call):
        """Play audio file on camera"""

        this_camera = get_camera(call);
        file=call.data.get(ATTR_FILE);
        _LOGGER.info("Playing {} on {}".format(file,call.data[ATTR_ENTITY_ID]));
        # this_camera.play_wav(httptype='singlepart', path_file=file);
        result = this_camera.audio_send_stream(httptype='singlepart', channel=1, path_file=file, encode='MPEG2');
        _LOGGER.info(dir(result));
        return result == 'OK';
    hass.services.async_register(DOMAIN, SERVICE_PLAY_WAV, handle_play_wav, schema=SERVICE_PLAY_WAV_SCHEMA)


    def get_camera(call):
        entity_id = call.data.get(ATTR_ENTITY_ID);
        if not entity_id:
            _LOGGER.error("No entity ID supplied");
        en = str(entity_id).split('.')[1];
        if en in hass.data[DATA_AMCREST]:
            return hass.data[DATA_AMCREST][en].device;
        else:
            return None;
            _LOGGER.info("Entity id does not exist:  {}".format(entity_id));

    return True


class AmcrestCam(Camera):
    """An implementation of an Amcrest IP camera."""

    def __init__(self, hass, amcrest):
        """Initialize an Amcrest camera."""
        _LOGGER.info("Now using custom Amcrest component");
        super(AmcrestCam, self).__init__()
        self._name = amcrest.name
        self._camera = amcrest.device
        self._base_url = self._camera.get_base_url()
        self._ffmpeg = hass.data[DATA_FFMPEG]
        self._ffmpeg_arguments = amcrest.ffmpeg_arguments
        self._stream_source = amcrest.stream_source
        self._resolution = amcrest.resolution
        self._token = self._auth = amcrest.authentication

    def camera_image(self):
        """Return a still image response from the camera."""
        # Send the request to snap a picture and return raw jpg data
        response = self._camera.snapshot(channel=self._resolution)
        return response.data

    async def handle_async_mjpeg_stream(self, request):
        """Return an MJPEG stream."""
        # The snapshot implementation is handled by the parent class
        if self._stream_source == STREAM_SOURCE_LIST['snapshot']:
            await super().handle_async_mjpeg_stream(request)
            return

        if self._stream_source == STREAM_SOURCE_LIST['mjpeg']:
            # stream an MJPEG image stream directly from the camera
            websession = async_get_clientsession(self.hass)
            streaming_url = self._camera.mjpeg_url(typeno=self._resolution)
            stream_coro = websession.get(
                streaming_url, auth=self._token, timeout=TIMEOUT)

            await async_aiohttp_proxy_web(self.hass, request, stream_coro)

        else:
            # streaming via fmpeg
            from haffmpeg import CameraMjpeg

            streaming_url = self._camera.rtsp_url(typeno=self._resolution)
            stream = CameraMjpeg(self._ffmpeg.binary, loop=self.hass.loop)
            await stream.open_camera(
                streaming_url, extra_cmd=self._ffmpeg_arguments)

            await async_aiohttp_proxy_stream(
                self.hass, request, stream,
                'multipart/x-mixed-replace;boundary=ffserver')
            await stream.close()

    @property
    def name(self):
        """Return the name of this camera."""
        return self._name