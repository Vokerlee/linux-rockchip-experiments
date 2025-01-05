CC = g++
FLAGS = -O2 -Wall -Wextra -Werror -static \
	-ffunction-sections -fdata-sections -Wl,--gc-sections

BUILD_DIR = build
SRC_DIR = src
SRC_FILES = $(wildcard $(SRC_DIR)/*.cpp)
OUT_FILE = $(BUILD_DIR)/pmu_collector

all:
	mkdir -p $(BUILD_DIR)
	$(CC) $(FLAGS) $(SRC_FILES) -o $(OUT_FILE)

clean:
	$(RM) -r $(BUILD_DIR)
