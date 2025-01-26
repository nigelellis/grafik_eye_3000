# grafik_eye_3000
Home Assistant Custom Component for Lutron Grafik Eye 3000

This component communicates with Grafik Eye units through a GRX-CI-NWK-E Control Interface. To use this component, you will need to add some code to your configuration.yaml.  The following is an example:

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

Yes, this can get tedious if you have many units and many scenes.  There is probably a better way to do this, so I am open to suggestions.  I am a mere hobbyist coder, so please do not judge too harshly.
