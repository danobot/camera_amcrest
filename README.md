# Introduction
Custom camera component for Amcrest cameras.
This component is not compatible with the one in Home Assistant (I tried to merge but for some reason the services would not be available in HA.)

## Getting Started
Place this file in `custom_components/camera/amcrest.py`.


You can copy the following card to your Lovelace config which has buttons for different presets and the ability to reboot and play audio:

```

cards:
  - entity: camera.cam_front
    id: 462927f785804074bf3caf252955d200
    show_name: Front
    type: picture-entity
  - cards:
      - entity: camera.cam_front
        icon: 'mdi:camcorder-box'
        name: Park
        tap_action:
          action: call-service
          service: amcrest.go_to_preset
          service_data:
            entity_id: camera.cam_front
            preset: 1
        type: entity-button
      - entity: camera.cam_front
        icon: 'mdi:camcorder-box'
        name: Door
        tap_action:
          action: call-service
          service: amcrest.go_to_preset
          service_data:
            entity_id: camera.cam_front
            preset: 3
        type: entity-button
      - entity: camera.cam_front
        icon: 'mdi:camcorder-box'
        name: Inside
        tap_action:
          action: call-service
          service: amcrest.go_to_preset
          service_data:
            entity_id: camera.cam_front
            preset: 4
        type: entity-button
      - entity: camera.cam_front
        icon: 'mdi:camcorder-box'
        name: Driveway
        tap_action:
          action: call-service
          service: amcrest.go_to_preset
          service_data:
            entity_id: camera.cam_front
            preset: 2
        type: entity-button
      - entity: camera.cam_front
        icon: 'mdi:camcorder-box'
        name: Zoom
        tap_action:
          action: call-service
          service: amcrest.go_to_preset
          service_data:
            entity_id: camera.cam_front
            preset: 5
        type: entity-button
    id: 60e3891e5658419a9aa69ddb10ead8f7
    type: horizontal-stack
  - cards:
      - entity: camera.cam_front
        icon: 'mdi:speaker'
        name: Play Audio
        tap_action:
          action: call-service
          service: amcrest.play_wav
          service_data:
            entity_id: camera.cam_front
            file: /config/www/assets/doorbell.wav
        type: entity-button
      - entity: camera.cam_front
        name: Move Directly
        tap_action:
          action: call-service
          service: amcrest.move_directly
          service_data:
            entity_id: camera.cam_front
            point_a: '0,0'
            point_b: '2000,2000'
        type: entity-button
      - entity: camera.cam_front
        icon: 'mdi:refresh'
        name: Reboot Cam
        tap_action:
          action: call-service
          service: amcrest.reboot
          service_data:
            entity_id: camera.cam_front
        type: entity-button
    type: horizontal-stack
id: ec2942d2090a445c9cfe6a701446ca2c
type: vertical-stack


```