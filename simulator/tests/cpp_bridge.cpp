#include "../firmware/controller.h"
#include <iostream>
#include <iomanip>
int main() {
    float m,t,h;
    std::cout << std::setprecision(10);
    while (std::cin >> m >> t >> h) {
        auto f=agri::evaluate(m,t,h), b=agri::evaluate(m,t,h,true);
        std::cout << f.minutes << " " << b.minutes << "\n";
    }
}
