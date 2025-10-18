# Final Makefile for the Unified Server

CXX = g++
CXXFLAGS = -std=c++17 -Wall -Wextra -pthread
TARGET = server
SRC = server.cpp

all: $(TARGET)

$(TARGET): $(SRC)
	$(CXX) $(CXXFLAGS) -o $(TARGET) $(SRC)

clean:
	rm -f $(TARGET)

.PHONY: all clean