#include "CircularBuffer.hpp"
#include <iostream>
#include <iomanip>    
#include <algorithm>  
#include <numeric>    

int main() {
    std::cout << std::fixed << std::setprecision(1);

    CircularBuffer<double> tempBuffer(5);
    tempBuffer.push_back(23.5);
    tempBuffer.push_back(24.1);
    tempBuffer.push_back(23.8);
    tempBuffer.push_back(25.2);
    tempBuffer.push_back(24.7);
    tempBuffer.push_back(26.1); // 초과 시 가장 오래된 값 덮어쓰기

    // STL 사용
    double maxTemp = *std::max_element(tempBuffer.begin(), tempBuffer.end());
    double avgTemp = std::accumulate(tempBuffer.begin(), tempBuffer.end(), 0.0) / tempBuffer.size();

    std::cout << "버퍼 내용 (인덱스 순서): [" << tempBuffer.dump_index() << "]\n";

    std::cout << "begin()부터 순회 시: ";
    bool first = true;
    for (auto v : tempBuffer) {
        if (!first) std::cout << ", ";
        std::cout << v;
        first = false;
    }
    std::cout << " (가장 오래된 것부터)\n\n";

    std::cout << "tempBuffer.size() = "     << tempBuffer.size()     << "\n";
    std::cout << "tempBuffer.capacity() = " << tempBuffer.capacity() << "\n";
    std::cout << "tempBuffer.empty() = "    << std::boolalpha << tempBuffer.empty() << "\n";
    std::cout << "maxTemp = " << maxTemp << "\n";
    std::cout << "avgTemp = " << std::setprecision(2) << avgTemp << "\n";
    std::cout << std::setprecision(1);
    std::cout << "tempBuffer.front() = " << tempBuffer.front() << "  // 가장 오래된 데이터\n";
    std::cout << "tempBuffer.back()  = " << tempBuffer.back()  << "  // 가장 최근 데이터\n";

    return 0;
}
