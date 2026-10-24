"""Deterministic software counterpart of firmware/controller.h (no hardware I/O)."""
from collections import deque
from dataclasses import dataclass, asdict
import math
import random

RULES = [[[22,18,14],[32,26,22],[40,36,30]],
         [[8,4,0],[12,8,4],[22,14,8]], [[0,0,0],[0,0,0],[0,0,0]]]
VERSION = "smartagri-lab-1.0"
SAMPLE_SECONDS = 5
WINDOW_SECONDS = 60
# Matches Wokwi's acceleration, NOT physical watering duration.
SECONDS_PER_COMMAND_MINUTE = 1


def clamp(x, low=0, high=1):
    return max(low, min(high, x))


def memberships(m, t, h):
    def left(x,a,b): return clamp((b-x)/(b-a))
    def right(x,a,b): return clamp((x-a)/(b-a))
    def triangle(x,a,b,c): return min(right(x,a,b),left(x,b,c))
    return [[left(m,20,50),triangle(m,20,50,80),right(m,50,80)],
            [left(t,15,27),triangle(t,15,27,39),right(t,27,39)],
            [left(h,30,60),triangle(h,30,60,90),right(h,60,90)]]


def valid(m,t,h):
    return all(isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v)
               and lo <= v <= hi for v,lo,hi in [(m,0,100),(t,0,50),(h,0,100)])


def evaluate(m,t,h, baseline=False):
    if not valid(m,t,h):
        return {"valid":False,"minutes":0,"weight":0,"rules":[],"memberships":[]}
    if baseline:
        return {"valid":True,"minutes":10.0 if m<30 else 0.0,"weight":1,"rules":[],"memberships":[]}
    mm,tt,hh = memberships(m,t,h)
    active=[]
    for i in range(3):
        for j in range(3):
            for k in range(3):
                w=min(mm[i],tt[j],hh[k])
                if w>0:
                    active.append({"m":i,"t":j,"h":k,"weight":w,"minutes":RULES[i][j][k]})
    weight=sum(r["weight"] for r in active)
    return {"valid":weight>0,"minutes":sum(r["weight"]*r["minutes"] for r in active)/weight if weight else 0,
            "weight":weight,"rules":active,"memberships":[mm,tt,hh]}


PRESETS = [
    {"id":"normal","name":"Everyday conditions","description":"50% moisture, 27 °C, 60% RH. Inspect the 8-minute fuzzy command and timed indicator.","moisture":50,"temperature":27,"humidity":60},
    {"id":"dry_hot","name":"Hot & dry","description":"Dry soil surrogate and hot air activate the longest fuzzy dose.","moisture":10,"temperature":45,"humidity":20},
    {"id":"wet","name":"Already wet","description":"85% moisture should produce no dose in either controller.","moisture":85,"temperature":27,"humidity":60},
    {"id":"boundary","name":"At the boundary","description":"Exactly 30%: low-moisture alert is inclusive; the baseline pump threshold is strict.","moisture":30,"temperature":27,"humidity":60},
    {"id":"wet_stop","name":"Sudden wet reading","description":"A step to 90% at 15 s stops watering at that sample, before the filter settles.","moisture":10,"temperature":45,"humidity":20},
    {"id":"sensor_fault","name":"Sensor fault & recovery","description":"Injected failure at 12–27 s stops the output immediately. Readings resume on a sampling tick.","moisture":10,"temperature":45,"humidity":20},
    {"id":"network_loss","name":"Connection lost","description":"Transport disabled at 10–40 s. Local control continues; only the latest offline snapshot is retained.","moisture":10,"temperature":45,"humidity":20},
    {"id":"noisy","name":"Noisy sensor","description":"Seeded moisture noise with a five-reading moving average. Compare raw and filtered inputs.","moisture":30,"temperature":27,"humidity":60},
    {"id":"drying","name":"Gradual drying","description":"A prescribed moisture ramp from 65% to 10%. It does not respond to the pump.","moisture":65,"temperature":32,"humidity":45},
]


@dataclass
class Config:
    preset: str = "normal"
    moisture: float = 50
    temperature: float = 27
    humidity: float = 60
    duration: int = 120
    seed: int = 7
    noise: float = 0

    @classmethod
    def parse(cls, value):
        if not isinstance(value,dict) or set(value)-set(cls.__dataclass_fields__):
            raise ValueError("Unknown simulation setting.")
        c=cls(**value)
        if c.preset not in {p["id"] for p in PRESETS}|{"custom"}:
            raise ValueError("Choose a known scenario.")
        if not valid(c.moisture,c.temperature,c.humidity):
            raise ValueError("Inputs must be finite: moisture 0–100%, air temperature 0–50 °C, humidity 0–100%.")
        if type(c.duration) is not int or not 30<=c.duration<=600:
            raise ValueError("Duration must be a whole number from 30 to 600 seconds.")
        if type(c.seed) is not int or not 0<=c.seed<=999999:
            raise ValueError("Seed must be a whole number from 0 to 999999.")
        if isinstance(c.noise,bool) or not isinstance(c.noise,(int,float)) or not math.isfinite(c.noise) or not 0<=c.noise<=20:
            raise ValueError("Noise must be 0–20 percentage points.")
        return c


class Node:
    """One-second clock, with five-second sensor sampling and independent dose timer."""
    def __init__(self, baseline=False):
        self.baseline=baseline
        self.filters=[deque(maxlen=5) for _ in range(3)]
        self.filtered=None
        self.decision=evaluate(None,None,None)
        self.pump_until=0
        self.sensor_ok=False
        self.was_fault=False
        self.pending=True
        self.last_window=0
        self.events=[]
        self.on_seconds=0
        self.doses=0

    def event(self,t,kind,message):
        self.events.append({"time":t,"kind":kind,"message":message})

    def tick(self,t,raw,fault):
        was_on=self.pump_until>t-1 if t else False
        if fault:
            if not self.was_fault:
                self.event(t,"fault","Sensor fault injected; output stopped and filters reset.")
            self.sensor_ok=False
            self.filtered=None
            self.decision=evaluate(None,None,None)
            self.pump_until=0
            self.pending=False
            for f in self.filters:f.clear()
        elif self.was_fault:
            # Equivalent to FAULT OFF → scheduleTest in sketch.ino.
            self.pending=True
            self.event(t,"recovery","Fault cleared; waiting for the next scheduled sensor sample.")
        self.was_fault=fault
        if t-self.last_window>=WINDOW_SECONDS:
            self.pending=True
            self.last_window=t
        if t%SAMPLE_SECONDS==0 and not fault:
            if not valid(*raw):
                self.sensor_ok=False;self.pump_until=0
                self.decision=evaluate(None,None,None)
                self.filtered=None
                self.pending=False
                for f in self.filters:f.clear()
            else:
                for f,v in zip(self.filters,raw):f.append(v)
                self.filtered=[sum(f)/len(f) for f in self.filters]
                self.decision=evaluate(*self.filtered,self.baseline)
                self.sensor_ok=self.decision["valid"]
                if raw[0]>=80 or self.decision["minutes"]<=0:
                    if self.pump_until>t:
                        self.event(t,"stop","Wet reading or zero command stopped the current dose.")
                    self.pump_until=0
                if self.pending:
                    if raw[0]<80:
                        self.pump_until=t+self.decision["minutes"]*SECONDS_PER_COMMAND_MINUTE
                        if self.pump_until>t:
                            self.doses+=1
                            self.event(t,"dose",f"Dose started: {self.decision['minutes']:.2f} command min.")
                    self.pending=False
                    self.last_window=t
        on=self.sensor_ok and self.pump_until>t
        if was_on and not on and not fault and not any(e["time"]==t and e["kind"]=="stop" for e in self.events):
            self.event(t,"timer","Dose timer completed.")
        if on:self.on_seconds+=1
        return {"pump_on":on,"remaining_seconds":max(0,self.pump_until-t) if on else 0,
                "sensor_ok":self.sensor_ok,"filtered":self.filtered,
                "command_minutes":self.decision["minutes"],"rules":self.decision["rules"],
                "memberships":self.decision["memberships"]}


def run(config):
    if not isinstance(config,Config):config=Config.parse(config)
    rng=random.Random(config.seed)
    fuzzy,baseline=Node(),Node(True)
    frames=[];last_received=None;pending=None;delivered=0;overwritten=0;sequence=0
    sampled=[config.moisture,config.temperature,config.humidity]
    for t in range(config.duration+1):
        fault=config.preset=="sensor_fault" and 12<=t<27
        online=not(config.preset=="network_loss" and 10<=t<40)
        if t%SAMPLE_SECONDS==0:
            m=config.moisture
            if config.preset=="drying":m=65-55*t/config.duration
            if config.preset=="wet_stop" and t>=15:m=90
            amplitude=config.noise or (10 if config.preset=="noisy" else 0)
            sampled=[clamp(m+rng.uniform(-amplitude,amplitude),0,100),config.temperature,config.humidity]
        f=fuzzy.tick(t,sampled,fault);b=baseline.tick(t,sampled,fault)
        # Latest-snapshot transport surrogate; no real MQTT, retries or latency claims.
        publish=t%SAMPLE_SECONDS==0 or (frames and (f["pump_on"]!=frames[-1]["fuzzy"]["pump_on"] or f["sensor_ok"]!=frames[-1]["fuzzy"]["sensor_ok"]))
        if publish:
            sequence+=1
            if pending is not None:overwritten+=1
            pending={"seq":sequence,"sample_time":t,"moisture":f["filtered"][0] if f["filtered"] else None,
                     "temperature":f["filtered"][1] if f["filtered"] else None,"humidity":f["filtered"][2] if f["filtered"] else None,
                     "pump_on":f["pump_on"],"sensor_ok":f["sensor_ok"],"command_minutes":f["command_minutes"]}
        if online and pending is not None:
            last_received={**pending,"received_time":t};pending=None;delivered+=1
        frames.append({"time":t,"raw":sampled[:] if not fault else [None,None,None],"network_online":online,
                       "fuzzy":f,"baseline":b,"collector":last_received.copy() if last_received else None,
                       "delivered":delivered,"overwritten":overwritten,
                       "low_moisture_alert":not fault and sampled[0]<=30})
    # Exclude final endpoint: a duration of N seconds covers intervals [0,N).
    summary={"fuzzy_on_seconds":sum(r["fuzzy"]["pump_on"] for r in frames[:-1]),
             "baseline_on_seconds":sum(r["baseline"]["pump_on"] for r in frames[:-1]),
             "fuzzy_doses":sum(e["kind"]=="dose" and e["time"]<config.duration for e in fuzzy.events),
             "baseline_doses":sum(e["kind"]=="dose" and e["time"]<config.duration for e in baseline.events),
             "delivered":delivered,"overwritten":overwritten}
    return {"version":VERSION,"config":asdict(config),"frames":frames,"summary":summary,
            "events":{"fuzzy":fuzzy.events,"baseline":baseline.events},
            "assumptions":{"source":"synthetic prescribed sensor traces; Python controller",
                           "sample_seconds":5,"dose_window_seconds":60,"seconds_per_command_minute":1,
                           "filter":"up to five valid samples; cleared on fault",
                           "transport":"in-process latest-snapshot surrogate; not an MQTT benchmark",
                           "plant":"no water balance, soil physics, rain or yield model",
                           "timing":"discrete 1-second software clock; not ESP32 latency"}}


def preset_config(name):
    p=next(p for p in PRESETS if p["id"]==name)
    return Config.parse({k:p[k] for k in ("moisture","temperature","humidity")} | {"preset":name})


def run_suite():
    tests=[]
    def check(name,expected,actual,passed):
        tests.append({"name":name,"expected":expected,"actual":actual,"passed":bool(passed)})
    for m,t,h,want in [(50,27,60,8),(10,45,20,40),(85,27,60,0),(30,27,60,20),(31,27,60,19.4)]:
        result=evaluate(m,t,h)["minutes"]
        check(f"Fuzzy {m}/{t}/{h}",want,result,abs(want-result)<1e-8)
    for m,want in [(29,10),(30,0),(31,0)]:
        result=evaluate(m,27,60,True)["minutes"]
        check(f"Baseline moisture {m}%",want,result,result==want)
    peaks=all(abs(evaluate(m,t,h)["minutes"]-RULES[i][j][k])<1e-8
              for i,m in enumerate([10,50,90]) for j,t in enumerate([10,27,45]) for k,h in enumerate([20,60,95]))
    check("All 27 rule peaks","27 exact consequents",peaks,peaks)
    invalid=all(not evaluate(*v)["valid"] and evaluate(*v)["minutes"]==0 for v in [(-1,27,60),(101,27,60),(20,51,60),(20,27,None),(20,float('nan'),60)])
    check("Invalid input fail-safe","rejected with zero command",invalid,invalid)
    runs={p["id"]:run(preset_config(p["id"])) for p in PRESETS}
    f=runs["normal"]["frames"]
    check("Dose timer","ON at 7 s, OFF at 8 s",[f[7]["fuzzy"]["pump_on"],f[8]["fuzzy"]["pump_on"]],f[7]["fuzzy"]["pump_on"] and not f[8]["fuzzy"]["pump_on"])
    f=runs["wet_stop"]["frames"]
    check("Immediate raw-wet stop","OFF at 15 s while average <80%",f[15]["fuzzy"]["filtered"][0],not f[15]["fuzzy"]["pump_on"] and f[15]["fuzzy"]["filtered"][0]<80)
    f=runs["sensor_fault"]["frames"]
    check("Fault and recovery","OFF 12–26 s; fresh filter at 30 s",[f[12]["fuzzy"]["sensor_ok"],f[30]["fuzzy"]["filtered"]],all(not r["fuzzy"]["pump_on"] for r in f[12:27]) and f[30]["fuzzy"]["filtered"]==[10,45,20])
    f=runs["network_loss"]["frames"]
    check("Offline local control","ON locally at 20 s; collector holds old sample",f[20]["collector"]["sample_time"],f[20]["fuzzy"]["pump_on"] and f[20]["collector"]["sample_time"]<10)
    check("Reconnect latest snapshot","sample 40 s delivered at 40 s",f[40]["collector"]["sample_time"],f[40]["collector"]["sample_time"]==40)
    node=Node()
    for t in range(0,25,5):node.tick(t,[100,27,60],False)
    observed=[node.tick(t,[0,27,60],False)["filtered"][0] for t in range(25,50,5)]
    check("Five-sample step response",[80,60,40,20,0],observed,observed==[80,60,40,20,0])
    a=run(preset_config("noisy"));b=run(preset_config("noisy"))
    check("Seed repeatability","identical numerical frames",a["frames"]==b["frames"],a["frames"]==b["frames"])
    return {"version":VERSION,"tests":tests,"passed":sum(t["passed"] for t in tests),"total":len(tests),
            "scenarios":[{"id":key,"config":r["config"],**r["summary"]} for key,r in runs.items()],
            "scope":"Software regression tests on synthetic traces; no water-saving or field-performance inference."}
