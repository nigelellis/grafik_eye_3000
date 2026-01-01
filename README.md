# grafik_eye_3000
Home Assistant Custom Component for Lutron Grafik Eye 3000

This component communicates with Grafik Eye units through a GRX-CI-NWK-E Control Interface. 

## Configuration
To use this component, you will need to add some code to your configuration.yaml.  The following is an example:

```yaml
grafik_eye:
  host: [ip address of interface] 
  port: 23
  user_name: [user name]
  switches:
    - name: "Hall All On"
      unit: "2"
      scene: "1"
    - name: "Hallway"
      unit: "2"
      scene: "2"
    - name: "Upstairs"
      unit: "2"
      scene: "3"
```

This can get tedious if you have many units and many scenes. 

## Events
This integration will also fire a custome event `grafik_eye_button_press` when scene buttons are pressed on the GrafikEye units.

When a button is pressed, an event is fired with this data:
```yaml
{
    'unit': '2',                      # Unit number as string
    'scene': 5,                       # Scene number as integer
    'name': 'Hallway',                # Switch name from config (if configured)
    'device_id': 'grafik_eye_unit_2'  # Device identifier for filtering
}
```

Example automation:
```yaml
  automation:
    - alias: "Hallway Button Pressed"
      trigger:
        - platform: event
          event_type: grafik_eye_button_press
          event_data:
            name: "Hallway"
      action:
        - service: light.turn_on
          target:
            entity_id: light.other_room
```
