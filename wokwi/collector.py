"""MQTT -> validated JSONL/CSV. No weather requests or ML inside callbacks."""
import argparse, csv, json, math, os, time, uuid
from datetime import datetime, timezone
from pathlib import Path

FIELDS=['received_utc','received_unix_s','schema','device_id','seq','uptime_ms','controller','input_source','sensor_ok','temperature_c','humidity_pct','moisture_pct','raw_temperature_c','raw_humidity_pct','raw_moisture_pct','irrigation_minutes','pump_on','status','low_moisture_alert','mqtt_connected','inference_us','sample_work_us','ms_per_irrigation_minute']
def validate(d):
    if not isinstance(d,dict) or d.get('schema')!=1: raise ValueError('unsupported schema')
    required=FIELDS[2:]
    if any(k not in d for k in required):raise ValueError('missing field')
    if not isinstance(d['device_id'],str) or not d['device_id']:raise ValueError('invalid device id')
    if d['controller'] not in ['fuzzy','baseline']:raise ValueError('invalid controller')
    if d['input_source'] not in ['serial_override','simulated_sensors']:raise ValueError('invalid source')
    for k in ['seq','uptime_ms','inference_us','sample_work_us','ms_per_irrigation_minute']:
        if type(d[k]) is not int or d[k]<0:raise ValueError('invalid '+k)
    for k in ['sensor_ok','pump_on','low_moisture_alert','mqtt_connected']:
        if type(d[k]) is not bool:raise ValueError('invalid '+k)
    for k,hi in [('temperature_c',50),('humidity_pct',100),('moisture_pct',100),('raw_temperature_c',50),('raw_humidity_pct',100),('raw_moisture_pct',100)]:
        v=d[k]
        if d['sensor_ok']:
            if type(v) not in (int,float) or not math.isfinite(v) or not 0<=v<=hi:raise ValueError('invalid '+k)
        elif v is not None:raise ValueError('fault readings must be null')
    v=d['irrigation_minutes']
    if type(v) not in (int,float) or not math.isfinite(v) or not 0<=v<=40:raise ValueError('invalid command')
    if not d['sensor_ok'] and (d['pump_on'] or v!=0):raise ValueError('unsafe fault output')
    return d

def save(d,folder):
    validate(d);folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    row={**d,'received_utc':datetime.now(timezone.utc).isoformat(),'received_unix_s':time.time()}
    with (folder/'telemetry.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(row,allow_nan=False)+'\n')
    csvpath=folder/'telemetry.csv';exists=csvpath.exists()
    with csvpath.open('a',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=FIELDS,extrasaction='ignore')
        if not exists:w.writeheader()
        w.writerow(row)
    tmp=folder/'latest.tmp';tmp.write_text(json.dumps(row,allow_nan=False),encoding='utf-8');os.replace(tmp,folder/'latest.json')
    return row

def main():
    p=argparse.ArgumentParser();p.add_argument('--broker',default='broker.hivemq.com');p.add_argument('--port',type=int,default=1883)
    p.add_argument('--topic',default='smartagri/23bct0157/demo-v1/data');p.add_argument('--out',default='runs/demo')
    p.add_argument('--serial-file',help='Import a saved Wokwi Serial Monitor text file instead of MQTT')
    args=p.parse_args()
    if args.serial_file:
        count=0
        for line in Path(args.serial_file).read_text(encoding='utf-8-sig').splitlines():
            if not line.lstrip().startswith('{'):continue
            try:save(json.loads(line),args.out);count+=1
            except (ValueError,TypeError) as e:print('REJECTED:',e)
        print('Imported',count,'rows. Import timestamps are NOT original reception timestamps.');return
    import paho.mqtt.client as mqtt
    def on_connect(client,userdata,flags,reason_code,properties):
        print('MQTT connection:',reason_code,flush=True)
        if reason_code==0:client.subscribe(args.topic,qos=0)
    def on_message(client,userdata,msg):
        try:
            if len(msg.payload)>4096:raise ValueError('oversized payload')
            d=save(json.loads(msg.payload.decode('utf-8')),args.out)
            print(d['received_utc'],d['seq'],d['status'],'LED',d['pump_on'],flush=True)
        except (ValueError,TypeError,UnicodeError) as e:print('REJECTED:',e,flush=True)
    c=mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,client_id='agri-log-'+uuid.uuid4().hex[:12])
    c.on_connect=on_connect;c.on_message=on_message;c.reconnect_delay_set(1,30)
    c.connect_async(args.broker,args.port,60)
    print('Listening:',args.broker,args.port,args.topic,'->',args.out,flush=True)
    try:c.loop_forever(retry_first_connection=True)
    except KeyboardInterrupt:c.disconnect()
if __name__=='__main__':main()
