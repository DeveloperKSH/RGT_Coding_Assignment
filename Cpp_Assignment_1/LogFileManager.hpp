// LogFileManager.hpp
#pragma once
#include <string>
#include <vector>
#include <unordered_map>
#include <memory>
#include <mutex>
#include <fstream>
#include <chrono>
#include <iomanip>
#include <sstream>
#include <stdexcept>

// 스마트 포인터를 활용한 리소스 관리 클래스
class LogFileManager {
private:
  std::unordered_map<std::string, std::unique_ptr<std::ofstream>> files_;
  mutable std::mutex mtx_;

  // 타임스탬프 생성
  static std::string nowString() {
    using namespace std::chrono;

    // 현재 시간 확인 후 time_t로 변환
    std::time_t t = system_clock::to_time_t(system_clock::now());

    // time_t를 tm으로 변환 (반환값 확인)
    std::tm tm{};
    if (localtime_s(&tm, &t) != 0) {
      throw std::runtime_error("localtime_s failed");
    }

    // 로컬 시간 문자열 생성
    std::ostringstream oss;
    oss << std::put_time(&tm, "%Y-%m-%d %H:%M:%S");
    return oss.str();
  }

  // 이동 로직용 함수
  void moveFrom(LogFileManager&& other) {
    files_ = std::move(other.files_);
  }

public:
  LogFileManager() = default;

  // 복사 금지 (스트림 복사 불가, 소유권 충돌 방지)
  LogFileManager(const LogFileManager&) = delete;
  LogFileManager& operator=(const LogFileManager&) = delete;

  // 이동 허용 (소유권 이전)
  LogFileManager(LogFileManager&& other) noexcept { moveFrom(std::move(other)); }
  LogFileManager& operator=(LogFileManager&& other) noexcept {
    if (this != &other) {
      std::scoped_lock lk(mtx_, other.mtx_);
      files_.clear();
      moveFrom(std::move(other));
    }
    return *this;
  }

  // 기능 1. 파일 열기 (기존 파일이 없으면 생성, append 모드)
  void openLogFile(const std::string& filename) {
    std::lock_guard<std::mutex> lk(mtx_);
    if (files_.count(filename)) return;
    auto ofs = std::make_unique<std::ofstream>(filename, std::ios::app);
    if (!ofs->is_open()) {
      throw std::ios_base::failure("Failed to open log file: " + filename);
    }
    files_.emplace(filename, std::move(ofs));
  }

  // 기능 2. 로그 작성 (타임스탬프 + 로그)
  void writeLog(const std::string& filename, const std::string& message) {
    std::lock_guard<std::mutex> lk(mtx_);
    auto it = files_.find(filename);
    if (it == files_.end()) throw std::logic_error("File not opened: " + filename);

    (*it->second) << "[" << nowString() << "] " << message << "\n";
    if (!(*it->second)) {
      throw std::ios_base::failure("Failed to write to: " + filename);
    }
    it->second->flush();
  }

  // 기능 3. 전체 읽기 (새 ifstream으로 일시 오픈)
  std::vector<std::string> readLogs(const std::string& filename) {
    std::lock_guard<std::mutex> lk(mtx_);
    std::ifstream ifs(filename);
    if (!ifs.is_open()) throw std::ios_base::failure("Failed to read: " + filename);

    std::vector<std::string> lines;
    std::string line;
    while (std::getline(ifs, line)) lines.push_back(line);
    return lines;
  }

  // 기능 4. 파일 닫기
  void closeLogFile(const std::string& filename) {
    std::lock_guard<std::mutex> lk(mtx_);
    files_.erase(filename);
  }
};