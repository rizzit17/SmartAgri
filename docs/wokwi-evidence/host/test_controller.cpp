#include "controller.h"
#include <assert.h>
#include <stdio.h>
#include <limits>
int main(){
  int points=0;
  // An exhaustive integer grid checks domain coverage and bounded output.
  for(int m=0;m<=100;m++)for(int t=0;t<=50;t++)for(int h=0;h<=100;h++){
    auto r=agri::evaluate(m,t,h);assert(r.valid&&r.weight>0&&r.minutes>=0&&r.minutes<=40);points++;
  }
  assert(fabs(agri::evaluate(50,27,60).minutes-8)<0.001);
  assert(agri::evaluate(85,27,60).minutes==0);
  assert(agri::evaluate(10,45,20).minutes==40);
  assert(fabs(agri::evaluate(30,27,60).minutes-20)<0.001);
  assert(agri::evaluate(30,27,60).lowMoisture);
  assert(!agri::evaluate(31,27,60).lowMoisture);
  assert(fabs(agri::evaluate(31,27,60).minutes-19.4)<0.001);
  assert(agri::evaluate(29,27,60,true).minutes==10);
  assert(agri::evaluate(30,27,60,true).minutes==0);
  assert(!agri::evaluate(-1,27,60).valid);
  assert(!agri::evaluate(20,51,60).valid);
  assert(!agri::evaluate(20,std::numeric_limits<float>::quiet_NaN(),60).valid);
  // Membership peaks: test every rule consequent independently.
  float ms[]={10,50,90},ts[]={10,27,45},hs[]={20,60,95};
  for(int i=0;i<3;i++)for(int j=0;j<3;j++)for(int k=0;k<3;k++)
    assert(fabs(agri::evaluate(ms[i],ts[j],hs[k]).minutes-agri::RULES[i][j][k])<0.001);
  agri::Average a;for(int i=0;i<5;i++)a.add(100);
  for(int i=0;i<5;i++)assert(fabs(a.add(0)-(80-20*i))<0.001);
  a.reset();assert(a.add(30)==30);
  agri::Pump p;p.start(100,8,1000);p.tick(8099);assert(p.on);p.tick(8100);assert(!p.on);
  p.start(0xfffffff0U,1,1000);p.tick(0x000003d7U);assert(p.on);p.tick(0x000003d8U);assert(!p.on);
  p.start(0,40,1000);p.stop();assert(!p.on);p.start(0,0,1000);assert(!p.on);
  printf("PASS: %d domain points; 27 consequents; boundaries, invalid inputs, filter, timer, millis wrap\n",points);
}
