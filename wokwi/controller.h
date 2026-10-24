#pragma once
#include <math.h>
#include <stdint.h>

// Pure C++ controller shared by ESP32 firmware and the desktop tests.
// This new specification is NOT the undocumented legacy controller in the paper.
namespace agri {
inline float clamp(float x,float lo,float hi){return x<lo?lo:(x>hi?hi:x);}
inline float left(float x,float a,float b){return clamp((b-x)/(b-a),0,1);}
inline float right(float x,float a,float b){return clamp((x-a)/(b-a),0,1);}
inline float triangle(float x,float a,float b,float c){return fminf(right(x,a,b),left(x,b,c));}
inline bool valid(float m,float t,float h){
  return isfinite(m)&&isfinite(t)&&isfinite(h)&&m>=0&&m<=100&&t>=0&&t<=50&&h>=0&&h<=100;
}
struct Result { bool valid; float minutes; float weight; bool lowMoisture; };
// Indices: moisture Dry/Normal/Wet; temperature Cold/Warm/Hot;
// humidity Low/Medium/High. All 27 zero-order Sugeno consequents, in minutes.
static const float RULES[3][3][3]={
  {{22,18,14},{32,26,22},{40,36,30}},
  {{8,4,0},{12,8,4},{22,14,8}},
  {{0,0,0},{0,0,0},{0,0,0}}
};
inline Result evaluate(float m,float t,float h,bool baseline=false){
  if(!valid(m,t,h))return {false,0,0,false};
  if(baseline)return {true,m<30?10.0f:0.0f,1,m<=30};
  float mm[3]={left(m,20,50),triangle(m,20,50,80),right(m,50,80)};
  float tt[3]={left(t,15,27),triangle(t,15,27,39),right(t,27,39)};
  float hh[3]={left(h,30,60),triangle(h,30,60,90),right(h,60,90)};
  float sum=0,weight=0;
  for(int i=0;i<3;i++)for(int j=0;j<3;j++)for(int k=0;k<3;k++){
    float w=fminf(mm[i],fminf(tt[j],hh[k]));
    sum+=w*RULES[i][j][k];weight+=w;
  }
  if(weight<=0)return {false,0,0,false};
  return {true,clamp(sum/weight,0,40),weight,m<=30};
}
struct Average {
  float values[5]={0,0,0,0,0}; int count=0,index=0;
  void reset(){count=0;index=0;}
  float add(float x){values[index]=x;index=(index+1)%5;if(count<5)count++;
    float total=0;for(int i=0;i<count;i++)total+=values[i];return total/count;}
};
// Wrap-safe timer for doses much shorter than the 32-bit millis wrap interval.
struct Pump {
  bool on=false;uint32_t started=0,duration=0;
  void stop(){on=false;}
  void start(uint32_t now,float minutes,uint32_t msPerMinute){
    duration=(uint32_t)(clamp(minutes,0,40)*msPerMinute+0.5f);
    started=now;on=duration>0;
  }
  void tick(uint32_t now){if(on&&(uint32_t)(now-started)>=duration)stop();}
};
}
