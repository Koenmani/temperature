from behave import *
import json
import sys
import os
cwd = os.getcwd()
cwd = cwd.split('temperature')[0] + 'temperature\\'
sys.path.append(cwd+'onoffscripts\\')
import verwarmonoff
import time
from datetime import datetime
from datetime import timedelta
from datetime import date
from dateutil import tz

@given(u'i have a jsonobject from the controller')
def step_impl(context):
    context.r = json.loads(context.text)
    verwarmonoff.device_list = {}
    verwarmonoff.clean_device_list(context.r, True)

@given(u'i have a set of devices in a json eq3_control_object')
def step_impl(context):
    context.r = json.loads(context.text)
    verwarmonoff.device_list = {}
    verwarmonoff.clean_device_list(context.r, True)

@when(u'the room measured temperature is below the requested temperature within offset')
def step_impl(context):
    verwarmonoff.device_open = []
    verwarmonoff.device_close = []
    verwarmonoff.exclude = []
    verwarmonoff.outofsync = []
    verwarmonoff.tempdiff = 0
    verwarmonoff.process_rooms(context.r, True)


@then(u'i expect my heating system to stay off')
def step_impl(context):
    verwarmonoff.device_on_off(True)
    if verwarmonoff.device_list[list(verwarmonoff.device_list.keys())[0]].status == 'off':
        assert True
    else:
        assert False

@then(u'i expect my cv system to stay off')
def step_impl(context):
    verwarmonoff.device_on_off(True)
    verwarmonoff.boiler_on_off(True)
    if verwarmonoff.verwarming == False:
        assert True
    else:
        assert False
        

@when(u'the room measured temperature is below the requested temperature outside offset')
def step_impl(context):
    verwarmonoff.device_open = []
    verwarmonoff.device_close = []
    verwarmonoff.exclude = []
    verwarmonoff.outofsync = []
    verwarmonoff.tempdiff = 0
    verwarmonoff.process_rooms(context.r, True)
    verwarmonoff.device_on_off(True)

@then(u'i expect my heating system to turn on')
def step_impl(context):
    verwarmonoff.device_on_off(True)
    if verwarmonoff.device_list[list(verwarmonoff.device_list.keys())[0]].status == 'on':
        assert True
    else:
        assert False

@then(u'i expect my heating system to also turn on')
def step_impl(context):
    verwarmonoff.device_on_off(True)
    if verwarmonoff.device_list[list(verwarmonoff.device_list.keys())[0]].status == 'on' and verwarmonoff.device_list[list(verwarmonoff.device_list.keys())[1]].status == 'on':
        assert True
    else:
        assert False

@when(u'the first priority has been heating for more than 1 hour')
def step_impl(context):
    verwarmonoff.device_open = []
    verwarmonoff.device_close = []
    verwarmonoff.exclude = []
    verwarmonoff.outofsync = []
    verwarmonoff.tempdiff = 0
    nu = datetime.now()
    nu = nu.replace(tzinfo=tz.gettz('UTC'))
    nu = nu.astimezone(tz.gettz('Europe/Amsterdam'))
    nu = nu - timedelta(minutes=61)
    verwarmonoff.device_list[list(verwarmonoff.device_list.keys())[0]].last_change = nu
    verwarmonoff.device_list[list(verwarmonoff.device_list.keys())[0]].status = 'on'
    verwarmonoff.process_rooms(context.r, True)


@when(u'the outside temp is below -5')
def step_impl(context):
    verwarmonoff.device_open = []
    verwarmonoff.device_close = []
    verwarmonoff.exclude = []
    verwarmonoff.outofsync = []
    verwarmonoff.tempdiff = 0
    verwarmonoff.outside_temp = -10
    verwarmonoff.process_rooms(context.r, True)

@when(u'the situation stays unchanged next time')
def step_impl(context):
    verwarmonoff.device_open = []
    verwarmonoff.device_close = []
    verwarmonoff.exclude = []
    verwarmonoff.outofsync = []
    verwarmonoff.tempdiff = 0
    verwarmonoff.process_rooms(context.r, True)
    verwarmonoff.device_on_off(True)

@then(u'i expect my airco to stay off')
def step_impl(context):
    if verwarmonoff.device_list[list(verwarmonoff.device_list.keys())[0]].power == False:
        assert True
    else:
        assert False


@then(u'my heating system to start')
def step_impl(context):
    verwarmonoff.device_on_off(True)
    verwarmonoff.boiler_on_off(True)
    if verwarmonoff.verwarming == True:
        assert True
    else:
        assert False

@when(u'i get a new device because ip changed or command changed') #new ip 192.168.0.137
def step_impl(context):
    context.r = json.loads(context.text)
    verwarmonoff.clean_device_list(context.r, True)


@then(u'i expect my new device to be added')
def step_impl(context):
    for device in verwarmonoff.device_list:
        try:
            if device.host:
                if device.host == '192.168.0.137':
                    return True
        except:
            pass
    return False


@then(u'the redundant one to be deleted')
def step_impl(context):
    for device in verwarmonoff.device_list:
        try:
            if device.host:
                if device.host == '192.168.0.135':
                    return False
        except:
            pass
    return True

@then(u'i expect no signal to be send to my heads')
def step_impl(context):
    verwarmonoff.device_on_off(True)
    if verwarmonoff.device_list[list(verwarmonoff.device_list.keys())[0]].force_command > 1:
        assert True
    else:
        assert False

@then(u'only when it is the 5th time')
def step_impl(context):
    verwarmonoff.device_on_off(True)
    verwarmonoff.device_on_off(True)
    verwarmonoff.device_on_off(True)
    verwarmonoff.device_on_off(True)
    if verwarmonoff.device_list[list(verwarmonoff.device_list.keys())[0]].force_command == 0:
        assert True
    else:
        assert False


@when(u'the head is in error')
def step_impl(context):
    verwarmonoff.device_list[list(verwarmonoff.device_list.keys())[0]].status = 'error'


@then(u'i expect a signal to be send to my errorhead')
def step_impl(context):
    verwarmonoff.device_on_off(True)
    if verwarmonoff.device_list[list(verwarmonoff.device_list.keys())[0]].force_command == 0:
        assert True
    else:
        assert False


@when(u'within heating offset of CV')
def step_impl(context):
    pass #already defined in the json object as 0.5 difference in temp


@then(u'the radiator heads opened')
def step_impl(context):
    if len(verwarmonoff.device_open) >= 2:
        assert True
    else:
        assert False


@when(u'the airco is the only device')
def step_impl(context):
    pass #already defined in the json object


@then(u'i expect my airco to turn on')
def step_impl(context):
    verwarmonoff.device_on_off(True)
    if verwarmonoff.device_list[list(verwarmonoff.device_list.keys())[0]].power == True:
        assert True
    else:
        assert False


@when(u'the system is heating up my room')
def step_impl(context):
    verwarmonoff.device_open = []
    verwarmonoff.device_close = []
    verwarmonoff.exclude = []
    verwarmonoff.outofsync = []
    verwarmonoff.tempdiff = 0
    verwarmonoff.process_rooms(context.r, True)
    verwarmonoff.device_on_off(True)
    verwarmonoff.boiler_on_off(True)
    if verwarmonoff.verwarming == True:
        assert True
    else:
        assert False


@when(u'the target temp is nearly reached')
def step_impl(context):
    context.r = json.loads(context.text)
    verwarmonoff.clean_device_list(context.r, True)
    verwarmonoff.device_open = []
    verwarmonoff.device_close = []
    verwarmonoff.exclude = []
    verwarmonoff.outofsync = []
    verwarmonoff.tempdiff = 0
    verwarmonoff.process_rooms(context.r, True)
    verwarmonoff.device_on_off(True)
    verwarmonoff.boiler_on_off(True)

@then(u'i expect the device to stay open')
def step_impl(context):
    if verwarmonoff.device_list[list(verwarmonoff.device_list.keys())[0]].status == 'on' and verwarmonoff.device_list[list(verwarmonoff.device_list.keys())[1]].status == 'on':
        assert True
    else:
        assert False


@then(u'my CV to stop')
def step_impl(context):
    if verwarmonoff.verwarming == True:
        assert False
    else:
        assert True


@then(u'not when it is an airco or custom device')
def step_impl(context):
    if verwarmonoff.device_list[list(verwarmonoff.device_list.keys())[0]].status == 'on' and verwarmonoff.device_list[list(verwarmonoff.device_list.keys())[1]].status == 'off':
        assert True
    else:
        assert False

@then(u'my airco or custom device on')
def step_impl(context):
    if verwarmonoff.device_list[list(verwarmonoff.device_list.keys())[1]].status == 'on':
        assert True
    else:
        assert False

@when(u'the heating system can not reach the radiator head for more than 15min (serious radiator problem)')
def step_impl(context):
    verwarmonoff.device_open = []
    verwarmonoff.device_close = []
    verwarmonoff.exclude = []
    verwarmonoff.outofsync = []
    verwarmonoff.tempdiff = 0
    verwarmonoff.process_rooms(context.r, True)
    verwarmonoff.device_on_off(True)
    verwarmonoff.serious_radiator_problem = True
    verwarmonoff.boiler_on_off(True)


@then(u'i expect my CV to not turn on preventing overheat')
def step_impl(context):
    if verwarmonoff.verwarming == False:
        assert True
    else:
        assert False


@when(u'the thermostat is out of sync')
def step_impl(context):
    verwarmonoff.device_open = []
    verwarmonoff.device_close = []
    verwarmonoff.exclude = []
    verwarmonoff.outofsync = []
    verwarmonoff.tempdiff = 0
    verwarmonoff.process_rooms(context.r, True)
    verwarmonoff.device_on_off(True)
    #verwarmonoff.boiler_on_off(True)


@then(u'i expect this device to be closed by default')
def step_impl(context):
    if verwarmonoff.device_list[list(verwarmonoff.device_list.keys())[0]].status == 'off':
        assert True
    else:
        assert False


@when(u'i have set the temperature manually via the console')
def step_impl(context):
    pass #already in the json


@when(u'i have put the room on vacation mode')
def step_impl(context):
    verwarmonoff.device_open = []
    verwarmonoff.device_close = []
    verwarmonoff.exclude = []
    verwarmonoff.outofsync = []
    verwarmonoff.tempdiff = 0
    verwarmonoff.process_rooms(context.r, True)
    verwarmonoff.device_on_off(True)

@when(u'i have an airco heating more than one rooms')
def step_impl(context):
    pass #already in the json


@then(u'i expect my airco to be on')
def step_impl(context):
    if verwarmonoff.device_list[list(verwarmonoff.device_list.keys())[0]].status == 'on':
        assert True
    else:
        assert False


@then(u'set to the highest temp of a room')
def step_impl(context):
    if verwarmonoff.device_list[list(verwarmonoff.device_list.keys())[0]].ingesteld >= 21:
        assert True
    else:
        assert False

@then(u'i expect this device to be excluded from any steering')
def step_impl(context):
    if verwarmonoff.device_list[list(verwarmonoff.device_list.keys())[0]].status == 'exclude':
        assert True
    else:
        assert False

@when(u'they have the same priority within one room')
def step_impl(context):
    pass #already in the json


@then(u'i expect all devices to be opened')
def step_impl(context):
    if verwarmonoff.device_list[list(verwarmonoff.device_list.keys())[0]].status == 'on' and verwarmonoff.device_list[list(verwarmonoff.device_list.keys())[1]].status == 'on':
        assert True
    else:
        assert False