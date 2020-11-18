#!/usr/bin/python3

##FORTSÄTT PÅ RAD 635, ReadMV()

# import spidev
import time
import sys
import os
from datetime import datetime
import shutil
import urllib.request

import RPi.GPIO as GPIO


# https://github.com/Tuckie/max31855
class MAX31855(object):
    # Python driver for [MAX38155 Cold-Junction Compensated Thermocouple-to-Digital Converter](http://www.maximintegrated.com/datasheet/index.mvp/id/7273)
    # Requires:
    # - The [GPIO Library](https://code.google.com/p/raspberry-gpio-python/) (Already on most Raspberry Pi OS builds)
    # - A [Raspberry Pi](http://www.raspberrypi.org/)

    def __init__(self, cs_pin, clock_pin, data_pin, units="c", board=GPIO.BCM):
        # Initialize Soft (Bitbang) SPI bus
        # Parameters:
        # - cs_pin:    Chip Select (CS) / Slave Select (SS) pin (Any GPIO)
        # - clock_pin: Clock (SCLK / SCK) pin (Any GPIO)
        # - data_pin:  Data input (SO / MOSI) pin (Any GPIO)
        # - units:     (optional) unit of measurement to return. ("c" (default) | "k" | "f")
        # - board:     (optional) pin numbering method as per RPi.GPIO library (GPIO.BCM (default) | GPIO.BOARD)

        self.cs_pin = cs_pin
        self.clock_pin = clock_pin
        self.data_pin = data_pin
        self.units = units
        self.data = None
        self.board = board

        # Initialize needed GPIO
        GPIO.setmode(self.board)
        GPIO.setup(self.cs_pin, GPIO.OUT)
        GPIO.setup(self.clock_pin, GPIO.OUT)
        GPIO.setup(self.data_pin, GPIO.IN)

        # Pull chip select high to make chip inactive
        GPIO.output(self.cs_pin, GPIO.HIGH)

    def get(self):
        # Reads SPI bus and returns current value of thermocouple.
        self.read()
        self.checkErrors()
        return getattr(self, "to_" + self.units)(self.data_to_tc_temperature())

    def get_rj(self):
        # Reads SPI bus and returns current value of reference junction.
        self.read()
        return getattr(self, "to_" + self.units)(self.data_to_rj_temperature())

    def read(self):
        # Reads 32 bits of the SPI bus & stores as an integer in self.data.
        bytesin = 0
        # Select the chip
        GPIO.output(self.cs_pin, GPIO.LOW)
        # Read in 32 bits
        for i in range(32):
            GPIO.output(self.clock_pin, GPIO.LOW)
            bytesin = bytesin << 1
            if GPIO.input(self.data_pin):
                bytesin = bytesin | 1
            GPIO.output(self.clock_pin, GPIO.HIGH)
        # Unselect the chip
        GPIO.output(self.cs_pin, GPIO.HIGH)
        # Save data
        self.data = bytesin

    def checkErrors(self, data_32=None):
        # Checks error bits to see if there are any SCV, SCG, or OC faults
        if data_32 is None:
            data_32 = self.data
        anyErrors = (data_32 & 0x10000) != 0  # Fault bit, D16
        noConnection = (data_32 & 1) != 0  # OC bit, D0
        shortToGround = (data_32 & 2) != 0  # SCG bit, D1
        shortToVCC = (data_32 & 4) != 0  # SCV bit, D2
        if anyErrors:
            if noConnection:
                raise MAX31855Error("No Connection")
            elif shortToGround:
                raise MAX31855Error("Thermocouple short to ground")
            elif shortToVCC:
                raise MAX31855Error("Thermocouple short to VCC")
            else:
                # Perhaps another SPI device is trying to send data?
                # Did you remember to initialize all other SPI devices?
                raise MAX31855Error("Unknown Error")

    def data_to_tc_temperature(self, data_32=None):
        # Takes an integer and returns a thermocouple temperature in celsius.
        if data_32 is None:
            data_32 = self.data
        tc_data = ((data_32 >> 18) & 0x3FFF)
        return self.convert_tc_data(tc_data)

    def data_to_rj_temperature(self, data_32=None):
        # Takes an integer and returns a reference junction temperature in celsius.
        if data_32 is None:
            data_32 = self.data
        rj_data = ((data_32 >> 4) & 0xFFF)
        return self.convert_rj_data(rj_data)

    def convert_tc_data(self, tc_data):
        # Convert thermocouple data to a useful number (celsius).
        if tc_data & 0x2000:
            # two's compliment
            without_resolution = ~tc_data & 0x1FFF
            without_resolution += 1
            without_resolution *= -1
        else:
            without_resolution = tc_data & 0x1FFF
        return without_resolution * 0.25

    def convert_rj_data(self, rj_data):
        # Convert reference junction data to a useful number (celsius).
        if rj_data & 0x800:
            without_resolution = ~rj_data & 0x7FF
            without_resolution += 1
            without_resolution *= -1
        else:
            without_resolution = rj_data & 0x7FF
        return without_resolution * 0.0625

    def to_c(self, celsius):
        # Celsius passthrough for generic to_* method.
        return celsius

    def to_k(self, celsius):
        # Convert celsius to kelvin.
        return celsius + 273.15

    def to_f(self, celsius):
        # Convert celsius to fahrenheit.
        return celsius * 9.0 / 5.0 + 32

    def cleanup(self):
        # Selective GPIO cleanup
        GPIO.setup(self.cs_pin, GPIO.IN)
        GPIO.setup(self.clock_pin, GPIO.IN)


class MAX31855Error(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


# Not yet used - further development
def SendSerialOP():
    # Send serial controller output by GPIOpins and USB
    pass


class PWM:
    # Handles PWM outlet on GPIO pins defined (pin 17 in original version)
    # PWM preiod frequencu is 1s. 1% duty cycle -> 0.01s on time

    def __init__(self, pin):
        self.PWM_enabled = False
        self.GPIO_pin = pin
        # Initalize PWM
        GPIO.setup(self.GPIO_pin, GPIO.OUT)  # Set GPIO pin as output
        self.pwm = GPIO.PWM(self.GPIO_pin, 1)  # GPIO 17, 1 Hz period frequency (1% dc @ 1Hz -> 0,01s on time)
        self.pwm.start(0)  # Start with duty cycle 0 (dc:0-100%)

    def Update(self, mode, OP):
        # Generate GPIO output of suitable length for control
        # See https://sourceforge.net/p/raspberry-gpio-python/wiki/PWM/

        if mode == 'aut' or mode == 'man':
            self.PWM_enabled = True
            self.pwm.ChangeDutyCycle(OP)  # todo Fixa skalning av max Dutycykle vid 100% OP, se icke oo-versionen
        else:
            # For all undefined modes set pwm to 0 for safety reasons
            self.PWM_enabled = False
            self.pwm.ChangeDutyCycle(0)

    def Disable(self):
        self.PWM_enabled = False
        self.pwm.ChangeDutyCycle(0)

    def Enable(self, OP=0):
        self.PWM_enabled = True
        self.pwm.ChangeDutyCycle(OP)


class Settings:
    # Read control settings from file. If no File exist
    # initiate default values and save to file
    # mode [off, man, aut]
    # SP [degC]
    # OP [%]
    # P
    # I
    # D
    # interval, execution interval in ms

    def __init__(self, settingsfilename="/usr/share/nginx/www/data_to_cnt", mode="off", SP=0, OP=0, P=-0.1, I=1, D=0,
                 interval=1000):
        self.settingsfilename = settingsfilename
        self.mode = mode
        self.SP = SP
        self.OP = OP
        self.P = P
        self.I = I
        self.D = D
        self.interval = interval

    def Read(self):
        try:
            with open(self.settingsfilename, "r") as fh:
                settings = fh.readlines()

            settings = [row.strip('\n') for row in settings]
            # settings in followin order in file - mode, SP ,OP ,P ,I ,D
            self.mode = settings[0]
            self.SP = settings[1]
            self.OP = settings[2]
            self.P = settings[3]
            self.I = settings[4]
            self.D = settings[5]

        except:
            print("Settings read failure!",
                  'Error: {}. {}, line: {}'.format(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2].tb_lineno))
            raise

        fh.close()


class Sequence:
    # Read recepy for SP change from file if it exists
    # recalculate SP according to recepy
    #
    #	Usable recepy commands:
    #
    #	# ramp-to-in XXX, YYY [XXX degC, YYY min]
    #	# ramp-to-at XXX, YYY [XXX degC, YYY degC/min]
    #	# hold-for XXX [XXX min]
    #	# wait-to-reach XXX [XXX degC]
    #	# new-sp XXX [XXX degC]
    #	# next-step # [# step number]
    #	# temp-diff-to-external xxx yyy zzz [xxx diff in degC, yyy min temp degC, zzz max temp degC]
    #
    #	Läs in sekvensen varje exekvering
    #	Läs in eventuellt nytt steg varje exekvering
    #	Håll reda på tid i varje steg och aktivt steg hela tiden
    #	Kontrollera om stegvillkor är uppfyllt, eller om nytt steg är angivet fråb HMI
    #		(kolla om HMI-steg är ändrat från föregående ekekvering och är skiljt från aktivt steg)
    #	Sätt ev nytt steg
    #	beräkna ev ny SP beroende på aktivt steg steg
    #
    #		seq_step = 0   in minutes
    #		seq_timer = 0.0

    def __init__(self, sequencefilename="/usr/share/nginx/www/sequence", interval=1000):
        self.sequencefilename = sequencefilename
        self.seq_timer = 0
        self.seq_step_input = 0
        self.seq_step = 0
        self.SP = 0
        self.OP = 0
        self.sequencelines = ["0", "1 ramp-to-in 10 5", "2 next-step 1", "end"]  # Just some defaults
        self.interval = interval

    def Read(self):
        try:
            with open(self.sequencefilename, "r") as fh:
                sequence = fh.readlines()

        except Exception as e:
            # Here I think I should check if the file doesn't exist and in that case write some content to it.
            print("Sequence read failure! ",
                  'Error: {}. {}, line: {}'.format(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2].tb_lineno))
            raise

        fh.close()

        self.sequencelines = [row.strip('\n') for row in sequence]

    def Execute(self, SP, MV):
        # First read the sequence input file, as it may have changed
        self.Read()

        # Determine if a new manual command has been given
        if self.sequencelines[0] != self.seq_step_input:
            print("New manuals sequence step input")
            self.seq_step_input = self.sequencelines[0]
            self.seq_step = self.seq_step_input
            self.seq_timer = 0.0

        # OK, now we should know what step to use.
        # If we are in step 0 (=sequence inactive) or beyond the last sequence step,
        # we shoud do absolutely nothing, so we start with that
        print("seq_step:", self.seq_step)
        if (int(self.seq_step) == 0) or (int(self.seq_step) > len(self.sequencelines) - 1):
            print("Sequence inactive.")
            self.seq_step = 0
            self.seq_timer = 0.0
            return self.SP

        # Now break up the sequence command line to command and input values and do the work
        sequence_command = self.sequencelines[int(self.seq_step)].split(' ')
        print("sequence_command", sequence_command)
        # If the row doesn't contain anysequence command, set it to "" anyway, so we dont get an error later
        if len(sequence_command) < 2:
            sequence_command = ["-", ""]

        if sequence_command[1] == 'ramp-to-in':
            print("ramp-to-in")
            # Calculate new setpoint
            # SPnew = SP + interval*(SPtarget-SP)/(ramptime-seq_timer)
            try:
                self.SP = self.SP + self.interval / 1000 / 60 * (float(sequence_command[2]) - SP) / (
                            float(sequence_command[3]) - self.seq_timer)
            except ZeroDivisionError:
                self.SP = float(sequence_command[2])

            if self.seq_timer >= float(sequence_command[3]):
                # We have reached our time limit so go on with the next step!
                print("Reset seq_timer")
                self.seq_timer = 0.0
                self.seq_step = int(self.seq_step) + 1

            self.seq_timer = self.seq_timer + self.interval / 1000 / 60
            return SP

        elif sequence_command[1] == 'ramp-to-at':
            print("ramp-to-at")
            # Calculate new setpoint
            SP_old = self.SP
            SP_target = float(sequence_command[2])
            rate = float(sequence_command[3])
            step_finished = False

            if self.SP <= SP_target:
                self.SP = self.SP + self.interval / 1000 / 60 * rate
                if self.SP >= SP_target:
                    self.SP = SP_target
                    step_finished = True

            else:
                self.SP = self.SP - self.interval / 1000 / 60 * rate
                if self.SP <= SP_target:
                    self.SP = SP_target
                    step_finished = True

            if step_finished:
                # We have reached our time limit so go on with the next step!
                print("Reset seq_timer")
                self.seq_timer = 0.0
                self.seq_step = int(self.seq_step) + 1

            self.seq_timer = self.seq_timer + self.interval / 1000 / 60

            return self.SP

        elif sequence_command[1] == 'hold-for':
            print("hold-for")
            if self.seq_timer >= float(sequence_command[2]):
                # We have reached our time limit so go on with the next step!
                print("Reset seq_timer")
                self.seq_timer = 0.0
                self.seq_step = int(self.seq_step) + 1

            self.seq_timer = self.seq_timer + self.interval / 1000 / 60

            return self.SP

        elif sequence_command[1] == 'wait-to-reach':
            print("wait-to-reach, skipping NOT IMPLEMENTED YET")
            # NOT FINISHED. This step just continues to next for now
            self.seq_step = int(self.seq_step) + 1
            return self.SP

        elif sequence_command[1] == 'new-SP':
            print("new-SP")
            self.SP = float(sequence_command[2])
            self.seq_timer = 0.0
            self.seq_step = int(self.seq_step) + 1

            return self.SP

        elif sequence_command[1] == 'next-step':
            print("next-step")
            self.seq_step = int(sequence_command[2])

            return self.SP

        elif sequence_command[1] == 'temp-diff-to-external':
            print("temp-diff-to-external skipping NOT IMPLEMENTED YET")
            self.seq_step = int(self.seq_step) + 1
            return self.SP

        elif sequence_command[1] == '':
            print("Sequence ended")
            seq_step = 0
            return self.SP

        else:
            # No known command found, increment the step counter and try next!
            self.seq_step = int(self.seq_step) + 1
            return self.SP

    def WriteStatus(self):
        # Write sequence status to file so it can be shown in HMI
        try:
            with open("sequence_status", "w") as filehandle:
                filehandle.write(seq_step + "\n" + seq_timer + "\n")

        except:
            print("Write sequence_status failure!")
            raise

        if filehandle.closed != 0:
            filehandle.close()


def ReadMV(thermocouple):
    # Read MW from sensor (or other input)
    temp = thermocouple.get()
    return temp


def Read_ext_temp(ext_temp_in_use):
    ext_temp = 0
    if ext_temp_in_use == 1:
        try:
            # Read external temperature from sensor (or other input)
            f = urllib.request.urlopen("http://192.168.1.10/temperature/temperature_out")
            raw_text = f.read().decode('utf-8')
            text = raw_text.strip('b')
            ext_temp = float(text)

        except:
            # Don't halt if reading from the net doesn't work. Just give a sensible return temp
            ext_temp = -1

    return ext_temp


class PIDControl:

    def __init__(self, mode="off", SP=0, MV=0, OP=0, P=-0.1, I=1, D=0, interval=1000, e_last=0, e_int=0):
        self.mode = mode
        self.SP = SP
        self.MV = MV
        self.OP = OP
        self.P = P
        self.I = I
        self.D = D
        self.interval = interval
        self.e_last = e_last
        self.e_int = e_int

    def Update(self, mode="off", SP=0, MV=0, OP=0, P=-0.1, I=1, D=0, interval=1000, e_last=0, e_int=0):
        self.mode = mode
        self.SP = SP
        self.MV = MV
        self.OP = OP
        self.P = P
        self.I = I
        self.D = D
        self.interval = interval
        self.e_last = e_last
        self.e_int = e_int

    def Execute(self):
        # Calculate new OP based on SP, MV and error terms

        # OP = P(err + err_int+err*interval/I + D/interval*(err-err_last)

        if self.mode == 'aut':
            err = self.MV - self.SP

            # If the controller gives below 0 OP ot above 100 OP we have
            # to stop wind-up! Wind-up goes up or down dep. on 'sign' of P
            try:
                if self.OP >= 100:
                    if self.P > 0:
                        self.e_int = min(self.e_int, self.e_int + (self.interval / 1000.0) / self.I * err)
                    else:
                        self.e_int = max(self.e_int, self.e_int + (self.interval / 1000.0) / self.I * err)
                elif self.OP <= 0:
                    if self.P > 0:
                        self.e_int = max(self.e_int, self.e_int + (self.interval / 1000.0) / self.I * err)
                    else:
                        self.e_int = min(self.e_int, self.e_int + (self.interval / 1000.0) / self.I * err)
                else:
                    self.e_int = self.e_int + (self.interval / 1000.0) / self.I * err

            except ZeroDivisionError:
                # This occurs if I=0 above
                self.e_int = 0

            self.OP = self.P * (err + self.e_int + self.D / (self.interval / 1000.0) * (err - self.e_last))

            # Limit output to between 0 and 100
            if self.OP > 100:
                self.OP = 100
            if self.OP < 0:
                self.OP = 0
        elif self.mode == 'man':
            # In manual mode just keep current OP and set errors to 0 to have bumpless switches
            self.OP = self.OP
            err = 0.0
            self.e_int = 0.0
        else:
            # If we are not in a defined mode we should be off!
            # Set OP and errors to 0 to have bumpless switches to other modes
            self.OP = 0.0
            err = 0.0
            self.e_int = 0.0

        return self.OP


class Output:

    def __init__(self, SP=0, MV=0, OP=0, no_data_points=1, mirrorfilename="/var/tmp/temperatures",
                 outputfilename="/var/tmp/temperatures_workfile"):
        self.SP = SP
        self.MV = MV
        self.OP = OP
        self.no_data_points = no_data_points
        self.mirrorfilename = mirrorfilename
        self.outputfilename = outputfilename

    def LoadData(self, SP=0, MV=0, OP=0, no_data_points=1):
        self.SP = SP
        self.MV = MV
        self.OP = OP
        self.no_data_points = no_data_points

    def WriteOutput(self):
        # Write output to file for GUI presentation in web browser
        no_of_records = self.no_data_points

        try:
            filehandle = open(self.outputfilename, "a+")
            i = datetime.now()
            datestring = i.strftime('%Y-%m-%d %H:%M:%S')
            flen = 0
            filehandle.seek(0, 0)
            content = filehandle.readlines()
            flen = len(content)
            if flen == 0:
                # The file didnt exist yet, so
                filehandle.write("time,sp,mv,op\n")
            filehandle.close()
            print("flen: " + str(flen) + " (" + str(no_of_records) + ")")

            if flen > no_of_records - 1:
                # Delete oldest value(s) to trim length to no_of_records-1 to make room
                i = 0
                filehandle = open(self.outputfilename, "w")
                # First write the header for d3js script in web page!
                filehandle.write("time,sp,mv,op\n")
                # Then populate the file with the data lines that should be kept
                for line in content:
                    if i > flen - (no_of_records - 1):
                        filehandle.write(content[i])

                    i += 1

            filehandle.close()

            with open(self.outputfilename, "a") as filehandle:
                filehandle.write(datestring + "," + str(round(self.SP, 2)) + "," + str(round(self.MV, 2)) + "," + str(
                    round(self.OP, 2)) + "\n");

        except:
            print("Write output failure!")
            raise

        if filehandle.closed != 0:
            filehandle.close()

        # Copy the working file to the mirror file so it can be used externally!
        shutil.copy2(self.outputfilename, self.mirrorfilename)


if __name__ == "__main__":

    # Initialize thermocouple
    cs_pin = 2
    clock_pin = 3
    data_pin = 4
    units = "c"
    thermocouple = MAX31855(cs_pin, clock_pin, data_pin, units)

    # Initialize sequence step and timer
    seq_step_input = 0
    seq_step = 0
    seq_timer = 0.0

    # Initialize controller settings
    SP = thermocouple.get()
    settings = Settings("off", SP)
    # #Initialize Sp to current MV and Op to 0, before reading settings - be safe
    # mode = 'off'
    # SP = ReadMV(thermocouple)
    # OP = 0.0
    # P = -0.1
    # I = 1
    # D = 0.0
    # settings=[mode,SP,OP,P,I,D]

    # Initialize error to 0 at start
    error_last = 0.0
    error_int = 0.0

    # Initialize external temperature to 0 at start
    # This code is eperimental
    ext_temp = 0

    # Initalize PWM
    GPIO.setup(17, GPIO.OUT)  # Set GPIO pin as output
    pwm = GPIO.PWM(17, 1)  # GPIO 17, 1 Hz period frequency (1% dc @ 1Hz -> 0,01s on time)
    pwm.start(0)  # Start with duty cycle 0 (dc:0-100%)

    # Initialize execution timer before reading from settings
    # Finns nu i settings!
    interval = 1000  # ms

    # Init number of datapoints to write to file before reading from settings
    no_of_datapoints = 7 * 24 * 3600 / (interval / 1000.0)  # Start storing 1 week...

    last_timestamp = time.time()
    # Eternal loop
    while 1:
        try:
            if time.time() > last_timestamp + interval / 1000.0:
                last_timestamp = time.time()

                settings_old = settings
                settings = ReadSettings()
                mode = settings[0]

                if settings != settings_old:
                    SP = float(settings[1])
                    if mode == 'man':
                        OP = float(settings[2])  # %
                    P = float(settings[3])
                    I = float(settings[4])  # s
                    D = float(settings[5])  # s
                    interval = float(settings[6])  # ms
                    log_time = float(settings[7])  # minutes

                # Experimental ext_temp (set arg to 1 to use external temp)
                ext_temp = Read_ext_temp(0)
                MV = ReadMV(thermocouple)
                SP = ExecuteSequence(SP, MV)
                # This is ugly, but is easiest to do here,
                # If we are in manual mode HMI output scaling works better if SP=MV
                if mode == 'man' or mode == 'off':
                    SP = MV
                pid = PID_Control(mode, SP, MV, OP, P, I, D, error_last, error_int, interval)
                OP = pid[0]
                error_last = pid[1]
                error_int = pid[2]
                print(mode)
                print(pid)

                no_of_datapoints = 60 * log_time / (interval / 1000.0)
                WriteOutput(SP, MV, OP, no_of_datapoints)
                PWM(pwm, mode, OP)

                print("MV: " + str(MV) + "  SP:", str(SP), "\n")

        except (KeyboardInterrupt, SystemExit):
            print("Exit due to user pressing Ctrl+C")
            # raise
            break

        except (TypeError, ValueError):
            print('Execution error! ',
                  'Error: {}. {}, line: {}'.format(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2].tb_lineno))
            # Here I  roll back the settings to what was before the new ones were read!
            settings = settings_old
            raise

        except Exception:
            print('Something really shitty just happend. CRAP! ',
                  'Error: {}. {}, line: {}'.format(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2].tb_lineno))
            # 2017-05-10_thermocouple.cleanup()
            pwm.stop()
            # 2017-05-10_GPIO.cleanup()
            raise

    # Exit code
    thermocouple.cleanup()
    pwm.stop()
    GPIO.cleanup()
    print("Going to rest.")
