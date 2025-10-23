#include "LogFileManager.hpp"
#include <iostream>

int main() {
  LogFileManager manager;

  manager.openLogFile("error.log");
  manager.openLogFile("debug.log");
  manager.openLogFile("info.log");

  manager.writeLog("error.log", "Database connection failed");
  manager.writeLog("debug.log", "User login attempt");
  manager.writeLog("info.log",  "Server started successfully");

  std::vector<std::string> errorLogs = manager.readLogs("error.log");
  if (!errorLogs.empty()) {
    std::cout << "errorLogs[0] = \"" << errorLogs.front() << "\"\n";
  }

  manager.closeLogFile("error.log");
  manager.closeLogFile("debug.log");
  manager.closeLogFile("info.log");
  return 0;
}