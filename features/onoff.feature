Feature: testing on and off for heating system

    Scenario: do nothing, all rooms radiators are within offset
        Given i have a jsonobject from the controller
        """
        {"kamer": [{"airco": [],"devices": [{"custom": null,"ip": "192.168.0.135","last_change": null,"lowbattery": false,"mac": null,"name": "airco","open_close": null,"priority": 2,"protocol": "class:daikin_control_object"},{"custom": null,"ip": null,"last_change": null,"lowbattery": false,"mac": "00:1A:22:16:8B:E9","name": "radiator","open_close": null,"priority": 2,"protocol": "class:daikin_control_object"},{"custom": null,"ip": null,"last_change": null,"lowbattery": false,"mac": "00:1A:22:16:D3:B5@192.168.0.126","name": "radiator","open_close": null,"priority": 2,"protocol": "class:daikin_control_object"}],"exclude": false,"handmatig": false,"huidig": 18.8,"ingesteld": 19,"insync": true,"laatste_tijd": "06:30","lowbattery": false,"naam": "Woonkamer","offset": null,"radiator": [],"smartheat": false,"tid": 6,"volgend_temp": 15,"volgend_tijd": "21:30"},{"airco": [],"devices": [{"custom": null,"ip": "192.168.0.140","last_change": null,"lowbattery": false,"mac": null,"name": "airco","open_close": null,"priority": 2,"protocol": "class:daikin_control_object"},{"custom": null,"ip": null,"last_change": null,"lowbattery": false,"mac": "11:1A:33:18:8B:C9","name": "radiator","open_close": null,"priority": 2,"protocol": "class:daikin_control_object"},{"custom": null,"ip": null,"last_change": null,"lowbattery": false,"mac": "00:1A:22:16:D3:B5@192.168.0.129","name": "radiator","open_close": null,"priority": 2,"protocol": "class:daikin_control_object"}],"exclude": false,"handmatig": false,"huidig": 21.5,"ingesteld": 21,"insync": true,"laatste_tijd": "06:30","lowbattery": false,"naam": "Werkkamer","offset": null,"radiator": [],"smartheat": false,"tid": 9,"volgend_temp": 15,"volgend_tijd": "21:30"}],"otemp": [{"otemp": 9}],"tijd": [{"tijd": "Fri, 24 Feb 2023 16:47:22 GMT"}]}
        """
        When the room measured temperature is below the requested temperature within offset
        Then i expect my heating system to stay off

    Scenario: start heating outside offset
        Given i have a jsonobject from the controller
        """
        {"kamer": [{"airco": [],"devices": [{"custom": null,"ip": "192.168.0.135","last_change": null,"lowbattery": false,"mac": null,"name": "airco","open_close": null,"priority": 2,"protocol": "class:daikin_control_object"}],"exclude": false,"handmatig": false,"huidig": 18,"ingesteld": 19,"insync": true,"laatste_tijd": "06:30","lowbattery": false,"naam": "Woonkamer","offset": null,"radiator": [],"smartheat": false,"tid": 6,"volgend_temp": 15,"volgend_tijd": "21:30"},{"devices": [{"custom": null,"ip": "192.168.0.135","last_change": null,"lowbattery": false,"mac": null,"name": "airco","open_close": null,"priority": 2,"protocol": "class:daikin_control_object"}],"exclude": false,"handmatig": false,"huidig": 20.9,"ingesteld": 21,"insync": true,"laatste_tijd": "06:30","lowbattery": false,"naam": "Werkkamer","offset": null,"radiator": [],"smartheat": false,"tid": 9,"volgend_temp": 15,"volgend_tijd": "21:30"}],"otemp": [{"otemp": 9}],"tijd": [{"tijd": "Fri, 24 Feb 2023 16:47:22 GMT"}]}
        """
        When the room measured temperature is below the requested temperature outside offset
        Then i expect my heating system to turn on
    
    Scenario: force a command to heads every 5 minutes/times
        Given i have a jsonobject from the controller
        """
        {"kamer": [{"airco": [],"devices": [{"custom": null,"ip": null,"last_change": null,"lowbattery": false,"mac": "00:00:00:00:00","name": "radiator","open_close": null,"priority": 2,"protocol": "class:daikin_control_object"}],"exclude": false,"handmatig": false,"huidig": 18,"ingesteld": 19,"insync": true,"laatste_tijd": "06:30","lowbattery": false,"naam": "Woonkamer","offset": null,"radiator": [],"smartheat": false,"tid": 6,"volgend_temp": 15,"volgend_tijd": "21:30"},{"devices": [{"custom": null,"ip": "192.168.0.135","last_change": null,"lowbattery": false,"mac": null,"name": "airco","open_close": null,"priority": 2,"protocol": "class:daikin_control_object"}],"exclude": false,"handmatig": false,"huidig": 20.9,"ingesteld": 21,"insync": true,"laatste_tijd": "06:30","lowbattery": false,"naam": "Werkkamer","offset": null,"radiator": [],"smartheat": false,"tid": 9,"volgend_temp": 15,"volgend_tijd": "21:30"}],"otemp": [{"otemp": 9}],"tijd": [{"tijd": "Fri, 24 Feb 2023 16:47:22 GMT"}]}
        """
        When the room measured temperature is below the requested temperature outside offset
        And the situation stays unchanged next time
        Then i expect no signal to be send to my heads
        But only when it is the 5th time

    Scenario: force a command if in error
        Given i have a jsonobject from the controller
        """
        {"kamer": [{"airco": [],"devices": [{"custom": null,"ip": "192.168.0.135","last_change": null,"lowbattery": false,"mac": null,"name": "airco","open_close": null,"priority": 2,"protocol": "class:daikin_control_object"}],"exclude": false,"handmatig": false,"huidig": 18,"ingesteld": 19,"insync": true,"laatste_tijd": "06:30","lowbattery": false,"naam": "Woonkamer","offset": null,"radiator": [],"smartheat": false,"tid": 6,"volgend_temp": 15,"volgend_tijd": "21:30"},{"devices": [{"custom": null,"ip": "192.168.0.135","last_change": null,"lowbattery": false,"mac": null,"name": "airco","open_close": null,"priority": 2,"protocol": "class:daikin_control_object"}],"exclude": false,"handmatig": false,"huidig": 20.9,"ingesteld": 21,"insync": true,"laatste_tijd": "06:30","lowbattery": false,"naam": "Werkkamer","offset": null,"radiator": [],"smartheat": false,"tid": 9,"volgend_temp": 15,"volgend_tijd": "21:30"}],"otemp": [{"otemp": 9}],"tijd": [{"tijd": "Fri, 24 Feb 2023 16:47:22 GMT"}]}
        """
        When the room measured temperature is below the requested temperature outside offset
        And the situation stays unchanged next time
        And the head is in error
        Then i expect a signal to be send to my errorhead

    Scenario: start heating outside offset, but within heating offset (0.7)
        Given i have a jsonobject from the controller
        """
        {"kamer": [{"airco": [],"devices": [{"custom": null,"ip": null,"last_change": null,"lowbattery": false,"mac": "00:1A:22:16:8B:E9","name": "radiator","open_close": null,"priority": 1,"protocol": "class:daikin_control_object"}],"exclude": false,"handmatig": false,"huidig": 18.5,"ingesteld": 19,"insync": true,"laatste_tijd": "06:30","lowbattery": false,"naam": "Woonkamer","offset": null,"radiator": [],"smartheat": false,"tid": 6,"volgend_temp": 15,"volgend_tijd": "21:30"},{"devices": [{"custom": null,"ip": "192.168.0.135","last_change": null,"lowbattery": false,"mac": "19:16:00:15","name": "radiator","open_close": null,"priority": 2,"protocol": "class:daikin_control_object"}],"exclude": false,"handmatig": false,"huidig": 18.5,"ingesteld": 19,"insync": true,"laatste_tijd": "06:30","lowbattery": false,"naam": "Werkkamer","offset": null,"radiator": [],"smartheat": false,"tid": 9,"volgend_temp": 15,"volgend_tijd": "21:30"}],"otemp": [{"otemp": 9}],"tijd": [{"tijd": "Fri, 24 Feb 2023 16:47:22 GMT"}]}
        """
        When the room measured temperature is below the requested temperature outside offset
        But within heating offset of CV
        Then i expect my cv system to stay off
        And the radiator heads opened

    Scenario: heating outside offset more than 1 hour
        Given i have a jsonobject from the controller
        """
        {"kamer": [{"airco": [{"ip": "192.168.0.135","last_change": null,"open_close": 0}],"devices": [{"custom": null,"ip": "192.168.0.135","last_change": null,"lowbattery": false,"mac": null,"name": "airco","open_close": null,"priority": 1,"protocol": "class:daikin_control_object"},{"custom": null,"ip": null,"last_change": null,"lowbattery": false,"mac": "00:1A:22:16:8B:E9","name": "radiator","open_close": null,"priority": 2,"protocol": "class:eq3_control_object"}],"exclude": false,"handmatig": false,"huidig": 18,"ingesteld": 19,"insync": true,"laatste_tijd": "06:30","lowbattery": false,"naam": "Woonkamer","offset": null,"radiator": [{"lowbattery": false,"mac": "00:1A:22:16:D3:B5@192.168.0.126","open_close": 1}],"smartheat": false,"tid": 6,"volgend_temp": 15,"volgend_tijd": "21:30"}],"otemp": [{"otemp": 10}],"tijd": [{"tijd": "Fri, 24 Feb 2023 16:47:22 GMT"}]}
        """
        When the room measured temperature is below the requested temperature outside offset
        And the first priority has been heating for more than 1 hour
        Then i expect my heating system to also turn on

    Scenario: outside temp < -5, although airco prio 1 start heating CV
        Given i have a jsonobject from the controller
        """
        {"kamer": [{"airco": [{"ip": "192.168.0.135","last_change": null,"open_close": 0}],"devices": [{"custom": null,"ip": "192.168.0.135","last_change": null,"lowbattery": false,"mac": null,"name": "airco","open_close": null,"priority": 1,"protocol": "class:daikin_control_object"},{"custom": null,"ip": null,"last_change": null,"lowbattery": false,"mac": "00:1A:22:16:8B:E9","name": "radiator","open_close": null,"priority": 2,"protocol": "class:eq3_control_object"}],"exclude": false,"handmatig": false,"huidig": 18.0,"ingesteld": 19,"insync": true,"laatste_tijd": "06:30","lowbattery": false,"naam": "Woonkamer","offset": null,"radiator": [{"lowbattery": false,"mac": "00:1A:22:16:D3:B5@192.168.0.126","open_close": 1}],"smartheat": false,"tid": 6,"volgend_temp": 15,"volgend_tijd": "21:30"}],"otemp": [{"otemp": -10}],"tijd": [{"tijd": "Fri, 24 Feb 2023 16:47:22 GMT"}]}
        """
        When the room measured temperature is below the requested temperature within offset
        And the outside temp is below -5
        Then i expect my airco to stay off
        And my heating system to start
    
    Scenario: outside temp < -5, although airco prio 1 but only device
        Given i have a jsonobject from the controller
        """
        {"kamer": [{"airco": [],"devices": [{"custom": null,"ip": "192.168.0.135","last_change": null,"lowbattery": false,"mac": null,"name": "airco","open_close": null,"priority": 1,"protocol": "class:daikin_control_object"}],"exclude": false,"handmatig": false,"huidig": 18.0,"ingesteld": 19,"insync": true,"laatste_tijd": "06:30","lowbattery": false,"naam": "Woonkamer","offset": null,"radiator": [],"smartheat": false,"tid": 6,"volgend_temp": 15,"volgend_tijd": "21:30"}],"otemp": [{"otemp": -10}],"tijd": [{"tijd": "Fri, 24 Feb 2023 16:47:22 GMT"}]}
        """
        When the room measured temperature is below the requested temperature within offset
        And the outside temp is below -5
        And the airco is the only device
        Then i expect my airco to turn on

    Scenario: New devices found
        Given i have a set of devices in a json eq3_control_object
        """
        {"kamer": [{"airco": [],"devices": [{"custom": null,"ip": "192.168.0.135","last_change": null,"lowbattery": false,"mac": null,"name": "airco","open_close": null,"priority": 1,"protocol": "class:daikin_control_object"},{"custom": null,"ip": null,"last_change": null,"lowbattery": false,"mac": "00:1A:22:16:8B:E9","name": "radiator","open_close": null,"priority": 2,"protocol": "class:eq3_control_object"}],"exclude": false,"handmatig": false,"huidig": 18.8,"ingesteld": 19,"insync": true,"laatste_tijd": "06:30","lowbattery": false,"naam": "Woonkamer","offset": null,"radiator": [],"smartheat": false,"tid": 6,"volgend_temp": 15,"volgend_tijd": "21:30"}],"otemp": [{"otemp": -10}],"tijd": [{"tijd": "Fri, 24 Feb 2023 16:47:22 GMT"}]}
        """
        When i get a new device because ip changed or command changed
        """
        {"kamer": [{"airco": [],"devices": [{"custom": null,"ip": "192.168.0.137","last_change": null,"lowbattery": false,"mac": null,"name": "airco","open_close": null,"priority": 1,"protocol": "class:daikin_control_object"},{"custom": "just testing","ip": null,"last_change": null,"lowbattery": false,"mac": null,"name": "custom","open_close": null,"priority": 2,"protocol": "class:eq3_control_object"}],"exclude": false,"handmatig": false,"huidig": 18.8,"ingesteld": 19,"insync": true,"laatste_tijd": "06:30","lowbattery": false,"naam": "Woonkamer","offset": null,"radiator": [],"smartheat": false,"tid": 6,"volgend_temp": 15,"volgend_tijd": "21:30"}],"otemp": [{"otemp": -10}],"tijd": [{"tijd": "Fri, 24 Feb 2023 16:47:22 GMT"}]}
        """
        Then i expect my new device to be added 
        and the redundant one to be deleted

    Scenario: Multiple priority one devices
        Given i have a set of devices in a json eq3_control_object
        """
        {"kamer": [{"airco": [],"devices": [{"custom": null,"ip": null,"last_change": null,"lowbattery": false,"mac": "10:1A:99:16:8B:A9","name": "radiator","open_close": null,"priority": 1,"protocol": "class:eq3_control_object"},{"custom": null,"ip": null,"last_change": null,"lowbattery": false,"mac": "00:1A:22:16:8B:E9","name": "radiator","open_close": null,"priority": 1,"protocol": "class:eq3_control_object"}],"exclude": false,"handmatig": false,"huidig": 10,"ingesteld": 20,"insync": true,"laatste_tijd": "06:30","lowbattery": false,"naam": "Woonkamer","offset": null,"radiator": [],"smartheat": false,"tid": 6,"volgend_temp": 15,"volgend_tijd": "21:30"}],"otemp": [{"otemp": 10}],"tijd": [{"tijd": "Fri, 24 Feb 2023 16:47:22 GMT"}]}
        """
        When the system is heating up my room
        and they have the same priority within one room
        Then i expect all devices to be opened

    Scenario: Close CV before reaching target temp (use hot water)
        Given i have a set of devices in a json eq3_control_object
        """
        {"kamer": [{"airco": [],"devices": [{"custom": null,"ip": null,"last_change": null,"lowbattery": false,"mac": "10:1A:99:16:8B:A9","name": "radiator","open_close": null,"priority": 1,"protocol": "class:eq3_control_object"},{"custom": "http://start","ip": null,"last_change": null,"lowbattery": false,"mac": null,"name": "custom","open_close": null,"priority": 1,"protocol": "class:eq3_control_object"}],"exclude": false,"handmatig": false,"huidig": 10,"ingesteld": 20,"insync": true,"laatste_tijd": "06:30","lowbattery": false,"naam": "Woonkamer","offset": null,"radiator": [],"smartheat": false,"tid": 6,"volgend_temp": 15,"volgend_tijd": "21:30"}],"otemp": [{"otemp": 10}],"tijd": [{"tijd": "Fri, 24 Feb 2023 16:47:22 GMT"}]}
        """
        When the system is heating up my room 
        and the target temp is nearly reached
        """
        {"kamer": [{"airco": [],"devices": [{"custom": null,"ip": null,"last_change": null,"lowbattery": false,"mac": "10:1A:99:16:8B:A9","name": "radiator","open_close": null,"priority": 1,"protocol": "class:eq3_control_object"},{"custom": "http://start","ip": null,"last_change": null,"lowbattery": false,"mac": null,"name": "custom","open_close": null,"priority": 1,"protocol": "class:eq3_control_object"}],"exclude": false,"handmatig": false,"huidig": 19.8,"ingesteld": 20,"insync": true,"laatste_tijd": "06:30","lowbattery": false,"naam": "Woonkamer","offset": null,"radiator": [],"smartheat": false,"tid": 6,"volgend_temp": 15,"volgend_tijd": "21:30"}],"otemp": [{"otemp": 10}],"tijd": [{"tijd": "Fri, 24 Feb 2023 16:47:22 GMT"}]}
        """
        Then i expect the device to stay open
        And my CV to stop 
        But my airco or custom device on

    Scenario: Testing unreachable target radiator head
        Given i have a jsonobject from the controller
        """
        {"kamer": [{"airco": [],"devices": [{"custom": null,"ip": "192.168.0.135","last_change": null,"lowbattery": false,"mac": null,"name": "airco","open_close": null,"priority": 1,"protocol": "class:daikin_control_object"},{"custom": null,"ip": null,"last_change": null,"lowbattery": false,"mac": "00:1A:22:16:8B:E9","name": "radiator","open_close": null,"priority": 2,"protocol": "class:eq3_control_object"}],"exclude": false,"handmatig": false,"huidig": 18,"ingesteld": 19,"insync": true,"laatste_tijd": "06:30","lowbattery": false,"naam": "Woonkamer","offset": null,"radiator": [],"smartheat": false,"tid": 6,"volgend_temp": 15,"volgend_tijd": "21:30"}],"otemp": [{"otemp": 10}],"tijd": [{"tijd": "Fri, 24 Feb 2023 16:47:22 GMT"}]}
        """
        When the heating system can not reach the radiator head for more than 15min (serious radiator problem)
        Then i expect my CV to not turn on preventing overheat
        But not when it is an airco or custom device
    
    Scenario: Testing thermostat is out of sync
        Given i have a jsonobject from the controller
        """
        {"kamer": [{"airco": [],"devices": [{"custom": "http:looser","ip": "192.168.0.135","last_change": null,"lowbattery": false,"mac": null,"name": "custom","open_close": null,"priority": 1,"protocol": "class:daikin_control_object"},{"custom": null,"ip": null,"last_change": null,"lowbattery": false,"mac": "00:1A:22:16:8B:E9","name": "radiator","open_close": null,"priority": 2,"protocol": "class:eq3_control_object"}],"exclude": false,"handmatig": false,"huidig": 18,"ingesteld": 19,"insync": false,"laatste_tijd": "06:30","lowbattery": false,"naam": "Woonkamer","offset": null,"radiator": [{"lowbattery": false,"mac": "00:1A:22:16:D3:B5@192.168.0.126","open_close": 1}],"smartheat": false,"tid": 6,"volgend_temp": 15,"volgend_tijd": "21:30"}],"otemp": [{"otemp": 10}],"tijd": [{"tijd": "Fri, 24 Feb 2023 16:47:22 GMT"}]}
        """
        When the thermostat is out of sync
        Then i expect this device to be closed by default

    Scenario: manual temperature override on
        Given i have a jsonobject from the controller
        """
        {"kamer": [{"airco": [],"devices": [{"custom": null,"ip": "192.168.0.135","last_change": null,"lowbattery": false,"mac": null,"name": "airco","open_close": null,"priority": 1,"protocol": "class:daikin_control_object"},{"custom": null,"ip": null,"last_change": null,"lowbattery": false,"mac": "00:1A:22:16:8B:E9","name": "radiator","open_close": null,"priority": 2,"protocol": "class:eq3_control_object"}],"exclude": false,"handmatig": true,"huidig": 18,"ingesteld": 19,"insync": true,"laatste_tijd": "06:30","lowbattery": false,"naam": "Woonkamer","offset": null,"radiator": [],"smartheat": false,"tid": 6,"volgend_temp": 15,"volgend_tijd": "21:30"}],"otemp": [{"otemp": 10}],"tijd": [{"tijd": "Fri, 24 Feb 2023 16:47:22 GMT"}]}
        """
        When i have set the temperature manually via the console
        And the room measured temperature is below the requested temperature outside offset
        Then i expect my heating system to turn on

    Scenario: manual temperature override off
        Given i have a jsonobject from the controller
        """
        {"kamer": [{"airco": [],"devices": [{"custom": null,"ip": "192.168.0.135","last_change": null,"lowbattery": false,"mac": null,"name": "airco","open_close": null,"priority": 1,"protocol": "class:daikin_control_object"},{"custom": null,"ip": null,"last_change": null,"lowbattery": false,"mac": "00:1A:22:16:8B:E9","name": "radiator","open_close": null,"priority": 2,"protocol": "class:eq3_control_object"}],"exclude": false,"handmatig": true,"huidig": 18.7,"ingesteld": 19,"insync": true,"laatste_tijd": "06:30","lowbattery": false,"naam": "Woonkamer","offset": null,"radiator": [],"smartheat": false,"tid": 6,"volgend_temp": 15,"volgend_tijd": "21:30"}],"otemp": [{"otemp": 10}],"tijd": [{"tijd": "Fri, 24 Feb 2023 16:47:22 GMT"}]}
        """
        When i have set the temperature manually via the console
        And the room measured temperature is below the requested temperature within offset
        Then i expect my heating system to stay off

    Scenario: vacation mode
        Given i have a jsonobject from the controller
        """
        {"kamer": [{"airco": [],"devices": [{"custom": null,"ip": "192.168.0.135","last_change": null,"lowbattery": false,"mac": null,"name": "airco","open_close": null,"priority": 1,"protocol": "class:daikin_control_object"},{"custom": null,"ip": null,"last_change": null,"lowbattery": false,"mac": "00:1A:22:16:8B:E9","name": "radiator","open_close": null,"priority": 2,"protocol": "class:eq3_control_object"}],"exclude": true,"handmatig": false,"huidig": 18.7,"ingesteld": 19,"insync": true,"laatste_tijd": "06:30","lowbattery": false,"naam": "Woonkamer","offset": null,"radiator": [],"smartheat": false,"tid": 6,"volgend_temp": 15,"volgend_tijd": "21:30"}],"otemp": [{"otemp": 10}],"tijd": [{"tijd": "Fri, 24 Feb 2023 16:47:22 GMT"}]}
        """
        When i have put the room on vacation mode
        Then i expect this device to be excluded from any steering

    Scenario: Airco multiple rooms highest temp
        Given i have a jsonobject from the controller
        """
        {"kamer": [{"airco": [],"devices": [{"custom": null,"ip": "192.168.0.135","last_change": null,"lowbattery": false,"mac": null,"name": "airco","open_close": null,"priority": 1,"protocol": "class:daikin_control_object"},{"custom": null,"ip": null,"last_change": null,"lowbattery": false,"mac": "11:1A:22:16:8B:E9","name": "radiator","open_close": null,"priority": 2,"protocol": "class:eq3_control_object"}],"exclude": false,"handmatig": false,"huidig": 18,"ingesteld": 19,"insync": true,"laatste_tijd": "06:30","lowbattery": false,"naam": "Woonkamer","offset": null,"radiator": [],"smartheat": false,"tid": 6,"volgend_temp": 15,"volgend_tijd": "21:30"},{"airco": [],"devices": [{"custom": null,"ip": "192.168.0.135","last_change": null,"lowbattery": false,"mac": null,"name": "airco","open_close": null,"priority": 1,"protocol": "class:daikin_control_object"},{"custom": null,"ip": null,"last_change": null,"lowbattery": false,"mac": "00:1A:22:16:8B:E9","name": "radiator","open_close": null,"priority": 2,"protocol": "class:eq3_control_object"}],"exclude": false,"handmatig": false,"huidig": 20.7,"ingesteld": 21,"insync": true,"laatste_tijd": "06:30","lowbattery": false,"naam": "Werkkamer","offset": null,"radiator": [],"smartheat": false,"tid": 9,"volgend_temp": 15,"volgend_tijd": "21:30"}],"otemp": [{"otemp": 10}],"tijd": [{"tijd": "Fri, 24 Feb 2023 16:47:22 GMT"}]}
        """
        When i have an airco heating more than one rooms
        And the room measured temperature is below the requested temperature outside offset
        Then i expect my airco to be on
        And set to the highest temp of a room