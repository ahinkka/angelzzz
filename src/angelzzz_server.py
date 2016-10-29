import argparse
from bedditbt import BedditStreamer 
import time
import traceback
import os.path
import os
import sys
import bluetooth
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from Database import AngelzzzDB, Base
from timeout import timeout, TimeoutError

DB_PATH = "sqlite:////home/pi/angelzzz.sql"

PATH = os.path.dirname(os.path.realpath(__file__))


def avg(l):
    return sum(l) / float(len(l))

def init_db(engine):
    Base.metadata.create_all(engine)

def insert_to_db(engine, time, beddit, channel1, channel2):
    Session = sessionmaker()
    Session.configure(bind=engine)
    session = Session()
    entry = AngelzzzDB(time=time, beddit=beddit, channel1=channel1, channel2=channel2)
    session.add(entry)
    session.commit()
    return
    
def run_server_forever():
    a = None
    engine = create_engine(DB_PATH)
    init_db(engine)
    
    connected = False
    while True:
        try:
            if not connected:
                with timeout(10):
                    print("Connecting")
                    connected = True
                    a = BedditStreamer()
                    print("Connected")
            with timeout(10):
                channel1, channel2 = a.get_reading()
            data = [ time.time(),avg(channel1), avg(channel2)]
            insert_to_db(engine, time.time(), "beddit",avg(channel1), avg(channel2))
            # print(data)
        except (bluetooth.BluetoothError, TimeoutError) as e:
            print("got: " + str(e))
            if e.message.find("Bad file descriptor") > 0 or e.message.find("16") > 0:
                #print("restart bluetooth power")
                os.system(os.path.join(PATH, "restart_bluetooth_power"))
                print("sleeing 2")
                time.sleep(2)
                os.system(os.path.join(PATH, "reset_device.sh"))
            connected = False
            time.sleep(1)
        except KeyboardInterrupt:
            print("User sent termination call")
            try:
                a.conn.stop_streaming()
                a.conn.disconnect()
                sys.exit()
            except Exception:
                print(traceback.format_exc())
                sys.exit()
        except Exception:
            time.sleep(1)
            print("except " + str(time.time()))
            print(traceback.format_exc())
        #except bluetooth.ProtocolError as e:
        #    print("restarting")
        #    time.sleep(1)
        #    os.execl(sys.executable,sys.executable,__file__,"restart")
    
if __name__ == "__main__":
    
    run_server_forever()

    
